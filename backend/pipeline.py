"""End-to-end RAG orchestration — the heart of ResolvAI.

Flow (preserving the paper's pillars, re-domained to placement/interview prep):
  1. Normalise + PII-mask the incoming query.
  2. Rewrite follow-ups into a standalone query using conversation history (RQ3).
  3. Classify intent with fine-tuned DistilBERT; route/escalate/smalltalk accordingly.
  4. Hybrid retrieval (dense + sparse, RRF) filtered by the intent's document category (RQ2).
  5. Confidence gate — abstain & escalate to a human below threshold (RQ1).
  6. Grounded generation with inline citations (open LLM via Ollama).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

from . import config
from .generation import llm, prompt
from .ingest.clean import normalize_query
from .ingest.pii import mask_pii
from .nlp import intent as intent_mod
from .nlp import rewrite as rewrite_mod
from .retrieval import confidence, hybrid

ESCALATION_MSG = (
    "I'm connecting you to a placement officer who can help with this. "
    "Your conversation has been shared with them for context."
)
ABSTAIN_MSG = (
    "I don't have that in my knowledge base yet, so I don't want to guess. "
    "I'm escalating this to a placement officer."
)
GREETING_MSG = (
    "Hi! I'm ResolvAI, your placement prep assistant. Ask me about company PYQs, aptitude, "
    "coding rounds, HR interviews, eligibility, the placement process, and more."
)
OUT_OF_SCOPE_MSG = (
    "I can only help with placement and interview preparation. "
    "Try asking about company PYQs, aptitude, coding rounds, or the placement process."
)


@dataclass
class ChatResult:
    answer: str
    intent: str
    confidence: float
    escalated: bool
    citations: list[dict] = field(default_factory=list)
    rewritten_query: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def answer(query: str, history: list[dict] | None = None) -> ChatResult:
    # 1. preprocess + mask PII (never index/log raw student PII)
    clean = mask_pii(normalize_query(query), mask_names=config.MASK_NAMES)

    # 2. A request to reach a human is always self-contained, so classify the *original*
    # message first and escalate on it directly. Rewriting runs next and folds conversation
    # history into the query — which on a sensitive message destroys it ("I want to talk to
    # a placement officer" became "campus placement requirements cgpa minimum" mid-chat),
    # silently denying the handoff. Safety must not depend on the rewriter.
    direct = intent_mod.predict(clean)
    if direct.escalate:
        return ChatResult(ESCALATION_MSG, direct.intent, direct.confidence, True,
                          rewritten_query=clean)

    # 3. conversational query rewriting, then intent classification + routing
    standalone = rewrite_mod.rewrite(clean, history)
    intent = intent_mod.predict(standalone)

    if intent.escalate:
        return ChatResult(ESCALATION_MSG, intent.intent, intent.confidence, True,
                          rewritten_query=standalone)
    # A greeting always short-circuits. An out-of-scope verdict only does so when the
    # classifier is confident — otherwise fall through to retrieval, because the knowledge
    # base is the better judge of whether a question is covered than a 19-class model
    # trained on a few hundred utterances.
    if intent.smalltalk and (
        intent.intent != "out_of_scope" or intent.confidence >= config.OUT_OF_SCOPE_MIN_CONF
    ):
        msg = GREETING_MSG if intent.intent == "greeting" else OUT_OF_SCOPE_MSG
        return ChatResult(msg, intent.intent, intent.confidence, False,
                          rewritten_query=standalone)

    # 4. hybrid retrieval, routed to the intent's document category
    hits = hybrid.search(standalone, category=intent.category)
    conf = confidence.score(hits)

    # Treat the predicted category as a *preference*, not a hard constraint. The intent
    # corpus is small, so routing is unreliable: a mis-routed query gets filtered into the
    # wrong category, and if that category happens to return a weak-but-above-threshold
    # chunk the system would answer "I don't have that" from it while the real answer sits
    # unsearched in another category. Comparing against unfiltered retrieval and keeping
    # the stronger result makes a routing mistake cost precision, not the answer.
    if intent.category:
        alt_hits = hybrid.search(standalone, category=None)
        alt_conf = confidence.score(alt_hits)
        if alt_conf > conf:
            hits, conf = alt_hits, alt_conf

    # 5. confidence-aware abstention / escalation
    if confidence.should_abstain(conf):
        return ChatResult(ABSTAIN_MSG, intent.intent, conf, True,
                          rewritten_query=standalone)

    # 6. grounded generation with citations
    context, citations = prompt.build_context(hits)
    text = llm.generate(
        prompt.build_prompt(standalone, context),
        system=prompt.GROUNDED_SYSTEM,
    )
    return ChatResult(text, intent.intent, conf, False, citations, standalone)
