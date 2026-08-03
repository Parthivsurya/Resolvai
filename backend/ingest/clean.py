"""Text preprocessing and normalisation.

Mirrors the cleaning challenges from the case study: strip URLs / HTML / boilerplate,
normalise casing and elongated words ("pleaseee" -> "please"), collapse whitespace — while
**preserving** company names, product codes, and order/roll IDs (we never lowercase blindly
or strip alphanumeric tokens).
"""
from __future__ import annotations

import re

_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_HTML_RE = re.compile(r"<[^>]+>")
_MULTISPACE_RE = re.compile(r"[ \t]+")
_MULTINEWLINE_RE = re.compile(r"\n{3,}")
# 3+ repeated letters -> 2 (soooo -> soo). Keeps codes like "A100" untouched (digits ignored).
_ELONGATED_RE = re.compile(r"([A-Za-z])\1{2,}")


def normalize(text: str) -> str:
    """Clean a raw document or query while preserving meaningful tokens."""
    text = _URL_RE.sub(" ", text)
    text = _HTML_RE.sub(" ", text)
    text = _ELONGATED_RE.sub(r"\1\1", text)
    text = _MULTISPACE_RE.sub(" ", text)
    text = _MULTINEWLINE_RE.sub("\n\n", text)
    return text.strip()


def normalize_query(text: str) -> str:
    """Lighter normalisation for a user query (single-line collapse)."""
    text = normalize(text)
    return re.sub(r"\s+", " ", text).strip()
