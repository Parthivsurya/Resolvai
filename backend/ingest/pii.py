"""PII detection and masking.

Student queries and interview-experience docs can contain names, emails, phone numbers,
and roll numbers. We mask them with placeholder tokens *before* indexing or logging, using
regex for structured PII and spaCy NER for person names. spaCy is loaded lazily so the rest
of the pipeline works even if the model isn't installed yet.
"""
from __future__ import annotations

import re

_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE_RE = re.compile(r"\b(?:\+?\d{1,3}[-\s]?)?\d{10}\b")
# College roll numbers like CB.SC.U4CSE24535 or 21CSE1234
_ROLL_RE = re.compile(r"\b[A-Z]{2,}\.?[A-Z0-9.]*\d{3,}[A-Z0-9]*\b")

_nlp = None
_SPACY_FAILED = False


def _get_nlp():
    global _nlp, _SPACY_FAILED
    if _nlp is None and not _SPACY_FAILED:
        try:
            import spacy

            _nlp = spacy.load("en_core_web_sm", disable=["parser", "lemmatizer"])
        except Exception:
            # model not installed — degrade gracefully to regex-only masking
            _SPACY_FAILED = True
    return _nlp


def mask_pii(text: str, mask_names: bool = True) -> str:
    """Return ``text`` with emails, phones, roll numbers, and (optionally) person names
    replaced by placeholder tokens."""
    text = _EMAIL_RE.sub("[EMAIL]", text)
    text = _PHONE_RE.sub("[PHONE]", text)
    text = _ROLL_RE.sub("[ID]", text)

    if mask_names:
        nlp = _get_nlp()
        if nlp is not None:
            doc = nlp(text)
            # replace from the end so character offsets stay valid
            for ent in sorted(doc.ents, key=lambda e: e.start_char, reverse=True):
                if ent.label_ == "PERSON":
                    text = text[: ent.start_char] + "[NAME]" + text[ent.end_char :]
    return text
