"""Conversational query rewriting (RQ3).

Follow-up questions like "what about Infosys?" or "and the coding round?" are meaningless to
a retriever on their own. Using the recent conversation history, the local LLM rewrites them
into a self-contained, standalone query before retrieval. When there is no history (or the
LLM is unreachable) we return the original query unchanged.
"""
from __future__ import annotations

from .. import config
from ..generation import llm

_REWRITE_SYSTEM = (
    "You rewrite a user's latest message into a single standalone search query for a campus "
    "placement / interview-preparation knowledge base. Resolve pronouns and references using "
    "the conversation history (e.g. company names, round names). Output ONLY the rewritten "
    "query on one line, with no preamble, quotes, or explanation."
)


def rewrite(query: str, history: list[dict] | None = None) -> str:
    """history: list of {"role": "user"|"bot", "text": str}, oldest first."""
    if not history:
        return query

    convo = "\n".join(
        f"{'User' if turn['role'] == 'user' else 'Assistant'}: {turn['text']}"
        for turn in history[-6:]
    )
    prompt = (
        f"Conversation so far:\n{convo}\n\n"
        f"Latest user message: {query}\n\n"
        f"Standalone search query:"
    )
    try:
        rewritten = llm.generate(prompt, system=_REWRITE_SYSTEM, temperature=0.0).strip()
    except Exception:
        return query

    # take the first non-empty line, guard against an empty/echoed answer
    rewritten = next((ln.strip() for ln in rewritten.splitlines() if ln.strip()), "")
    return rewritten or query
