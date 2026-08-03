"""Hybrid retrieval — Reciprocal Rank Fusion (RRF) of dense + sparse results (RQ2).

RRF fuses two ranked lists without needing their scores to be on the same scale: each chunk
gets ``sum(1 / (RRF_K + rank))`` across the lists it appears in. We keep the max raw dense
similarity around as an interpretable signal for the confidence gate.
"""
from __future__ import annotations

from .. import config
from . import dense, sparse


def _rrf(ranked_lists: list[list[dict]], k: int) -> dict[str, dict]:
    fused: dict[str, dict] = {}
    for results in ranked_lists:
        for rank, item in enumerate(results):
            cid = item["chunk_id"]
            entry = fused.setdefault(
                cid, {**item, "rrf": 0.0, "dense_score": 0.0, "sparse_score": 0.0}
            )
            entry["rrf"] += 1.0 / (k + rank + 1)
    return fused


def search(query: str, top_k: int | None = None, category: str | None = None) -> list[dict]:
    """Return fused, ranked chunks. Each has ``rrf`` (fusion score), ``dense_score``, and
    ``sparse_score`` for downstream confidence scoring and debugging."""
    top_k = top_k or config.TOP_K_FINAL

    dense_hits = dense.search(query, category=category)
    sparse_hits = sparse.search(query, category=category)

    fused = _rrf([dense_hits, sparse_hits], config.RRF_K)
    for hit in dense_hits:
        fused[hit["chunk_id"]]["dense_score"] = hit["score"]
    for hit in sparse_hits:
        fused[hit["chunk_id"]]["sparse_score"] = hit["score"]

    ranked = sorted(fused.values(), key=lambda x: x["rrf"], reverse=True)
    return ranked[:top_k]
