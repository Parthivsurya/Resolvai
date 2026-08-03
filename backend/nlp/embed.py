"""Sentence-embedding wrapper around sentence-transformers.

A single lazily-loaded model instance is shared across indexing and querying so both sides
use identical vectors. ``bge`` models recommend prefixing queries with an instruction, which
we apply in :func:`encode_query`.
"""
from __future__ import annotations

from functools import lru_cache

from .. import config

# bge models benefit from this retrieval instruction on the *query* side only.
_BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(config.EMBED_MODEL)


def _is_bge() -> bool:
    return "bge" in config.EMBED_MODEL.lower()


def encode_documents(texts: list[str]) -> list[list[float]]:
    vecs = _model().encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return [v.tolist() for v in vecs]


def encode_query(text: str) -> list[float]:
    if _is_bge():
        text = _BGE_QUERY_PREFIX + text
    vec = _model().encode([text], normalize_embeddings=True, show_progress_bar=False)[0]
    return vec.tolist()
