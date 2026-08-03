"""Sparse keyword retrieval via a pickled BM25 index.

BM25 catches exact tokens that dense embeddings miss — company names, product/error codes,
acronyms (TCS, NQT, DSA). The index and chunk metadata are loaded once and cached.
"""
from __future__ import annotations

import pickle
import re
from functools import lru_cache

from .. import config

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


@lru_cache(maxsize=1)
def _load():
    with config.BM25_PATH.open("rb") as fh:
        payload = pickle.load(fh)
    return payload["bm25"], payload["chunks"]


def search(query: str, top_k: int | None = None, category: str | None = None) -> list[dict]:
    """Return the top BM25 matches. Scores are min-max normalised to [0, 1] across the
    returned candidates so they can be fused with dense scores by rank."""
    top_k = top_k or config.TOP_K_SPARSE
    bm25, chunks = _load()
    scores = bm25.get_scores(_tokenize(query))

    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    if category:
        ranked = [i for i in ranked if chunks[i]["category"] == category]
    ranked = ranked[:top_k]

    if not ranked:
        return []
    hi = scores[ranked[0]] or 1.0
    lo = scores[ranked[-1]]
    span = (hi - lo) or 1.0

    out: list[dict] = []
    for i in ranked:
        c = chunks[i]
        out.append(
            {
                "chunk_id": c["chunk_id"],
                "text": c["text"],
                "source": c["source"],
                "category": c["category"],
                "doc_id": c["doc_id"],
                "score": (scores[i] - lo) / span,
            }
        )
    return out
