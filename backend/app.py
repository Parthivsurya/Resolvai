"""FastAPI app exposing the ResolvAI placement RAG backend.

Endpoints
  GET  /health          liveness probe
  POST /chat            answer a student query (multi-turn via session_id)
  POST /ingest          rebuild the knowledge-base indexes from data/raw

CORS is open to the Vite dev server so the existing React UI can call /chat later.

Run:  ``uvicorn backend.app:app --reload``
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import pipeline
from .ingest import build_index

app = FastAPI(title="ResolvAI — Placement & Interview-Prep RAG")

app.add_middleware(
    CORSMiddleware,
    # allow any localhost / 127.0.0.1 port so the Vite dev server works whether it's
    # opened via localhost or 127.0.0.1 (browsers treat them as different origins).
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory conversation store (session_id -> list of turns). Fine for a demo / single node;
# swap for Redis if you need persistence across restarts or multiple workers.
_SESSIONS: dict[str, list[dict]] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    intent: str
    confidence: float
    escalated: bool
    citations: list[dict] = []
    rewritten_query: str | None = None
    session_id: str | None = None


@app.get("/")
def root() -> dict:
    return {
        "service": "ResolvAI — Placement & Interview-Prep RAG",
        "docs": "/docs",
        "endpoints": ["GET /health", "POST /chat", "POST /ingest"],
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    history = _SESSIONS.get(req.session_id, []) if req.session_id else []
    result = pipeline.answer(req.message, history=history)

    if req.session_id is not None:
        history = history + [
            {"role": "user", "text": req.message},
            {"role": "bot", "text": result.answer},
        ]
        _SESSIONS[req.session_id] = history[-12:]  # keep the last few turns

    return ChatResponse(session_id=req.session_id, **result.to_dict())


@app.post("/ingest")
def ingest() -> dict:
    """Rebuild Chroma + BM25 from whatever is currently in data/raw."""
    n = build_index.build()
    # drop cached retriever handles so the next query sees the fresh index
    from .retrieval import dense, sparse

    dense._collection.cache_clear()
    sparse._load.cache_clear()
    return {"status": "ok", "chunks_indexed": n}
