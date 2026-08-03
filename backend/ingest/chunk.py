"""Structure-aware chunking.

Splits documents into retrieval units. We first split on Markdown headings / blank lines so
a chunk stays within a logical section, then pack paragraphs up to ``CHUNK_SIZE`` characters
with ``CHUNK_OVERLAP`` carry-over. Chunk size and overlap are config variables (RQ4) so they
can be swept experimentally rather than fixed arbitrarily.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .. import config
from .loaders import RawDoc

_SECTION_RE = re.compile(r"\n(?=#{1,6}\s)")  # split before Markdown headings
_H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
_HEADING_RE = re.compile(r"^#{1,6}\s.*$", re.MULTILINE)
_MIN_CONTENT_CHARS = 40  # drop near-empty chunks (bare titles/dividers)


def _doc_title(text: str) -> str | None:
    m = _H1_RE.search(text)
    return m.group(1).strip() if m else None


def _content_len(text: str) -> int:
    """Length of a chunk ignoring heading lines — used to drop bare-title chunks."""
    return len(_HEADING_RE.sub("", text).strip())


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    source: str
    category: str
    text: str
    company: str | None = None


def _split_sections(text: str) -> list[str]:
    parts = _SECTION_RE.split(text)
    return [p.strip() for p in parts if p.strip()]


def _pack_paragraphs(section: str, size: int, overlap: int) -> list[str]:
    """Greedily pack paragraphs into ~``size``-char windows with ``overlap`` carry-over."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", section) if p.strip()]
    chunks: list[str] = []
    buf = ""
    for para in paras:
        if buf and len(buf) + len(para) + 2 > size:
            chunks.append(buf.strip())
            tail = buf[-overlap:] if overlap else ""
            buf = f"{tail}\n{para}"
        else:
            buf = f"{buf}\n\n{para}" if buf else para
    if buf.strip():
        chunks.append(buf.strip())
    return chunks


def chunk_document(doc: RawDoc) -> list[Chunk]:
    """Split a document into retrieval units. Each chunk is prefixed with the document's H1
    title (contextual chunking) so section chunks carry the parent context — e.g. the query
    "TCS coding questions" matches the coding section even though it doesn't repeat "TCS"."""
    title = _doc_title(doc.text)
    chunks: list[Chunk] = []
    idx = 0
    for section in _split_sections(doc.text):
        pieces = _pack_paragraphs(section, config.CHUNK_SIZE, config.CHUNK_OVERLAP) \
            if len(section) > config.CHUNK_SIZE else [section]
        for piece in pieces:
            if _content_len(piece) < _MIN_CONTENT_CHARS:
                continue  # skip bare-title / divider chunks that add noise to retrieval
            # prepend the doc title as a breadcrumb, unless this piece already is the H1 block
            text = piece if piece.lstrip().startswith("# ") else f"{title}\n{piece}" if title else piece
            chunks.append(
                Chunk(
                    chunk_id=f"{doc.doc_id}::{idx}",
                    doc_id=doc.doc_id,
                    source=doc.source,
                    category=doc.category,
                    text=text,
                    company=doc.company,
                )
            )
            idx += 1
    return chunks
