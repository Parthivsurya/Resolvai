# ResolvAI — Placement & Interview-Prep RAG Backend

A Retrieval-Augmented Generation chatbot that answers student questions about **campus
placements and interview preparation** — company PYQs, aptitude, coding/technical/HR rounds,
eligibility, the placement process, and interview experiences — grounded in a document
knowledge base, with **source citations** and **confidence-aware escalation** (it says "I
don't know" and hands off to a human instead of hallucinating).

Built entirely on **open-source, local** components (no paid API), preserving the NLP pillars
from the case study: fine-tuned **DistilBERT** intent classification, **hybrid** dense+sparse
retrieval, conversational **query rewriting**, and **RAGAS** evaluation.

## Architecture

```
query
  ├─ normalize + PII mask        ingest/clean.py, ingest/pii.py
  ├─ conversational rewrite       nlp/rewrite.py        (Ollama, uses history)  [RQ3]
  ├─ intent classification        nlp/intent.py         (fine-tuned DistilBERT)
  │     ├─ sensitive → human handoff
  │     └─ route to doc category
  ├─ hybrid retrieval             retrieval/hybrid.py   (Chroma + BM25, RRF)    [RQ2]
  ├─ confidence gate              retrieval/confidence.py (abstain/escalate)    [RQ1]
  └─ grounded generation          generation/           (Ollama + citations)
```

## Tech stack

| Concern | Choice |
|---|---|
| API | FastAPI + Uvicorn |
| Embeddings | sentence-transformers (`BAAI/bge-small-en-v1.5`) |
| Vector store | ChromaDB (persistent) |
| Sparse retrieval | BM25 (`rank_bm25`) |
| Intent classifier | fine-tuned DistilBERT (HuggingFace) |
| Local LLM | Ollama (`llama3:latest` by default) |
| PII masking | spaCy NER + regex |
| Evaluation | RAGAS + scikit-learn |

## Setup

> **Run every command below from the repository root** (`.../Resolvai`), not from inside
> `backend/`. `backend` is a Python package, so `python3 -m backend.…` and
> `uvicorn backend.app:app` only resolve when the repo root is the working directory.

```bash
cd /path/to/Resolvai                          # repo root — stay here for all commands
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
python3 -m spacy download en_core_web_sm      # optional; regex masking works without it

# Ollama (already installed). Ensure the model is available:
ollama pull llama3                            # or set RESOLVAI_OLLAMA_MODEL to another local model
```

## Usage

```bash
# (from the repo root)
# 1. Add knowledge to backend/data/raw/<category>/  (categories: pyq, aptitude, coding, hr,
#    process, company_profile, experience). Sample docs are already included.

# 2. Build the indexes (Chroma + BM25)
python3 -m backend.ingest.build_index

# 3. Train the intent classifier
python3 -m backend.nlp.intent

# 4. Run the API
uvicorn backend.app:app --reload
```

Query it:

```bash
curl -s localhost:8000/chat -H 'content-type: application/json' \
  -d '{"message":"What TCS PYQ coding questions are asked?","session_id":"s1"}'
```

Response shape:

```json
{
  "answer": "TCS NQT commonly asks ... [1][2]",
  "intent": "company_pyq",
  "confidence": 0.71,
  "escalated": false,
  "citations": [{"n": 1, "source": "tcs_nqt_pyq.md", "category": "pyq", "score": 0.68}],
  "rewritten_query": "TCS NQT previous year coding questions",
  "session_id": "s1"
}
```

## Evaluation

```bash
python3 -m backend.eval.intent_eval               # accuracy / macro-F1 per intent
pip install langchain-ollama
python3 -m backend.eval.ragas_eval                # groundedness on data/eval/qa.csv
```

## Configuration

All knobs live in `backend/config.py` (also overridable via env vars): embedding/LLM model
names, chunk size/overlap (`RQ4`), retrieval `top_k`, RRF constant, and the
`CONFIDENCE_THRESHOLD` for abstention.

## Adding your own data

Drop PDFs / CSVs / Markdown into `backend/data/raw/<category>/` and re-run
`python3 -m backend.ingest.build_index` (or `POST /ingest`). CSV rows are treated as one
document each (a `question`/`title` column is prepended to a `text`/`answer`/`content`
column). To grow the intent classifier, add rows to `data/intents/intents.csv` and retrain.
```
