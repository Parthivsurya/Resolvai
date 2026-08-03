"""Confidence-aware abstention (RQ1).

Turns retrieval quality into a single confidence score and an abstain/escalate decision, so
the LLM never gets to answer from weak or empty context. We combine the best dense semantic
similarity with a small bonus when both retrievers agree on the top chunk (dense + sparse
overlap is a strong signal of a genuine match).
"""
from __future__ import annotations

from .. import config


def score(hits: list[dict]) -> float:
    """Compute a retrieval-confidence score in [0, 1] from fused hits."""
    if not hits:
        return 0.0
    top = hits[0]
    dense_top = max((h.get("dense_score", 0.0) for h in hits), default=0.0)
    # agreement bonus: the top fused chunk was found by *both* retrievers
    agreement = 0.1 if (top.get("dense_score", 0.0) > 0 and top.get("sparse_score", 0.0) > 0) else 0.0
    return max(0.0, min(1.0, dense_top + agreement))


def should_abstain(confidence: float) -> bool:
    """True when confidence is below the configured threshold — abstain and escalate."""
    return confidence < config.CONFIDENCE_THRESHOLD
