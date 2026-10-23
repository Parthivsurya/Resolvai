# ResolvAI — Grounded Placement & Interview-Prep Assistant

A Retrieval-Augmented Generation (RAG) chatbot that answers campus-placement and
interview-preparation questions **only** from a curated knowledge base, **cites the source
document** for every claim, and **abstains and escalates to a placement officer** instead of
guessing when the knowledge base does not contain the answer.

Built entirely from open-source components running locally — no paid API, no student data
leaving the machine.

> *Answers that know, not guess.*

NLP case study (23CSE471), Group 14 — Amrita School of Computing, Amrita Vishwa Vidyapeetham,
Coimbatore. Guide: Dr. T. Senthil Kumar.

| | |
|---|---|
| Parthivsurya K B | CB.SC.U4CSE24535 — system architecture & NLP pipeline |
| Awaaz Muhammed | CB.SC.U4CSE24562 — data pipeline & knowledge base |
| Rajendra G | CB.SC.U4CSE24511 — intent modelling, evaluation & interface |

## Pipeline

```
query
  ├─ normalize + PII mask     ingest/clean.py, ingest/pii.py
  ├─ conversational rewrite   nlp/rewrite.py           (uses history)   [RQ3]
  ├─ intent classification    nlp/intent.py            (DistilBERT, 19 classes)
  │     ├─ sensitive  → human handoff
  │     ├─ smalltalk  → canned reply, no retrieval
  │     └─ factual    → prefer the intent's document category
  ├─ hybrid retrieval         retrieval/hybrid.py      (Chroma + BM25, RRF)  [RQ2]
  ├─ confidence gate          retrieval/confidence.py  (abstain / escalate)  [RQ1]
  └─ grounded generation      generation/              (local LLM + citations)
```

Orchestrated end to end by [`backend/pipeline.py`](backend/pipeline.py).

## Repository layout

| Path | Contents |
|---|---|
| `backend/` | FastAPI RAG backend — see [`backend/README.md`](backend/README.md) for setup and usage |
| `backend/data/raw/` | The knowledge base. Folder path encodes `<category>/<company>` |
| `src/` | React + Vite chat interface (citation and confidence display) |
| `dataset/` | Exportable dataset release (knowledge base + intent/eval CSVs) |
| `scripts/` | Dataset export and evaluation entry points |

## Quick start

Run everything from this directory (`backend` is a Python package, so `python -m backend.…`
only resolves from the repository root).

```bash
source backend/.venv/bin/activate

ollama list                             # Ollama must be running; needs llama3
python -m backend.ingest.build_index    # build Chroma + BM25 over data/raw
uvicorn backend.app:app --reload        # API on :8000  (Swagger UI at /docs)

npm install && npm run dev              # UI on :5173, in a second terminal
```

```bash
curl -s localhost:8000/chat -H 'content-type: application/json' \
  -d '{"message":"What DSA questions does Amazon ask?","session_id":"s1"}'
```

See [`backend/README.md`](backend/README.md) for the full architecture, configuration knobs,
evaluation harnesses, and how to add your own placement material.
