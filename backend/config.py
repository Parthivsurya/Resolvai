"""Central configuration for the ResolvAI placement/interview-prep RAG backend.

Everything tunable (model names, paths, retrieval params, thresholds) lives here so the
rest of the codebase never hard-codes a magic value. Values can be overridden via env vars.
"""
from __future__ import annotations

import os
from pathlib import Path

# --------------------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent
DATA_DIR = BACKEND_DIR / "data"
RAW_DIR = DATA_DIR / "raw"                 # user drops PYQ / placement PDFs, CSVs, MDs here
PROCESSED_DIR = DATA_DIR / "processed"     # cleaned + chunked artifacts (jsonl)
CHROMA_DIR = DATA_DIR / "chroma"           # persisted vector store
INTENTS_DIR = DATA_DIR / "intents"         # labeled intent training data (csv)
MODELS_DIR = BACKEND_DIR / "models"        # fine-tuned intent classifier checkpoint
BM25_PATH = PROCESSED_DIR / "bm25.pkl"     # pickled BM25 index + chunk metadata

for _d in (RAW_DIR, PROCESSED_DIR, CHROMA_DIR, INTENTS_DIR, MODELS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------------------
# Models
# --------------------------------------------------------------------------------------
# Sentence embedding model used for both indexing and query encoding.
EMBED_MODEL = os.getenv("RESOLVAI_EMBED_MODEL", "BAAI/bge-small-en-v1.5")

# Local LLM served by Ollama (generation + conversational query rewriting).
# Defaults to llama3 (8B). The 3B llama3.2 is faster but hedges — it contradicts itself and
# over-triggers the "not in my knowledge base" refusal even when the context holds the
# answer. deepseek-r1 also works but emits <think> reasoning traces.
OLLAMA_MODEL = os.getenv("RESOLVAI_OLLAMA_MODEL", "llama3:latest")
OLLAMA_HOST = os.getenv("RESOLVAI_OLLAMA_HOST", "http://localhost:11434")

# Base checkpoint fine-tuned into the intent classifier, and where the tuned model is saved.
INTENT_BASE_MODEL = os.getenv("RESOLVAI_INTENT_BASE", "distilbert-base-uncased")
INTENT_MODEL_DIR = MODELS_DIR / "intent-distilbert"

# --------------------------------------------------------------------------------------
# Chroma collection
# --------------------------------------------------------------------------------------
CHROMA_COLLECTION = "resolvai_placement"

# --------------------------------------------------------------------------------------
# PII masking
# --------------------------------------------------------------------------------------
# Structured PII (emails, phone numbers, roll numbers) is always masked via regex.
# spaCy NER *name* masking is off by default: on curated placement docs it produces bad
# false positives (e.g. tagging "C++"/"Java" as PERSON), corrupting the knowledge base.
# Enable it only for free-text with real personal names (e.g. raw interview experiences).
MASK_NAMES = os.getenv("RESOLVAI_MASK_NAMES", "0") == "1"

# --------------------------------------------------------------------------------------
# Chunking (RQ4 — treated as an experimental variable, not a fixed constant)
# --------------------------------------------------------------------------------------
CHUNK_SIZE = int(os.getenv("RESOLVAI_CHUNK_SIZE", "800"))       # target chars per chunk
CHUNK_OVERLAP = int(os.getenv("RESOLVAI_CHUNK_OVERLAP", "120"))  # char overlap between chunks

# --------------------------------------------------------------------------------------
# Retrieval (RQ2 — hybrid dense + sparse)
# --------------------------------------------------------------------------------------
TOP_K_DENSE = 12       # candidates pulled from Chroma
TOP_K_SPARSE = 12      # candidates pulled from BM25
TOP_K_FINAL = 8        # chunks handed to the LLM after fusion
RRF_K = 60             # Reciprocal Rank Fusion constant

# --------------------------------------------------------------------------------------
# Confidence-aware abstention (RQ1)
# --------------------------------------------------------------------------------------
# If the fused top-result confidence is below this, abstain and escalate to a human
# instead of letting the LLM guess.
CONFIDENCE_THRESHOLD = float(os.getenv("RESOLVAI_CONF_THRESHOLD", "0.35"))

# --------------------------------------------------------------------------------------
# Intents (placement / interview-prep domain) and their document-category routing.
# The classifier predicts one of INTENTS; DOC_CATEGORY maps it to the doc category used
# to filter retrieval. SENSITIVE_INTENTS force an immediate human handoff.
# --------------------------------------------------------------------------------------
INTENTS = [
    "company_pyq",
    "aptitude_prep",
    "coding_round",
    "technical_interview",
    "hr_interview",
    "group_discussion",
    "resume_help",
    "eligibility_criteria",
    "placement_process",
    "ctc_salary",
    "company_info",
    "off_campus",
    "internship",
    "interview_experience",
    "prep_roadmap",
    "cutoff",
    "greeting",
    "out_of_scope",
    "talk_to_placement_officer",
]

# Intent -> knowledge-base document category (used as a Chroma metadata filter).
DOC_CATEGORY = {
    "company_pyq": "pyq",
    "aptitude_prep": "aptitude",
    "coding_round": "coding",
    "technical_interview": "coding",
    "hr_interview": "hr",
    "group_discussion": "hr",
    "resume_help": "hr",
    "eligibility_criteria": "process",
    "placement_process": "process",
    "ctc_salary": "company_profile",
    "company_info": "company_profile",
    "off_campus": "process",
    "internship": "process",
    "interview_experience": "experience",
    "prep_roadmap": "process",
    "cutoff": "process",
    # intents below don't map to a KB category (handled specially in the pipeline)
    "greeting": None,
    "out_of_scope": None,
    "talk_to_placement_officer": None,
}

# Intents that skip retrieval entirely and hand off to a human.
# Below this DistilBERT softmax confidence, defer to the keyword heuristic. The seed
# intents.csv is tiny (~4 examples/intent), so the fine-tuned model is weak; this guard keeps
# routing sensible until the dataset is expanded.
INTENT_MIN_CONF = float(os.getenv("RESOLVAI_INTENT_MIN_CONF", "0.6"))

SENSITIVE_INTENTS = {"talk_to_placement_officer"}

# Intents handled conversationally without retrieval.
SMALLTALK_INTENTS = {"greeting"}

# Refusing a query outright as out-of-scope skips retrieval entirely, so a classifier slip
# silently denies a real question ("give me some pyq of amazon" was refused at 0.82). Only
# short-circuit when the classifier is *confident*; below this, fall through to retrieval and
# let the confidence gate decide, since the knowledge base is the better judge of coverage.
OUT_OF_SCOPE_MIN_CONF = float(os.getenv("RESOLVAI_OOS_MIN_CONF", "0.9"))

# All document categories used across the knowledge base.
DOC_CATEGORIES = ["pyq", "aptitude", "coding", "hr", "process", "company_profile", "experience"]
