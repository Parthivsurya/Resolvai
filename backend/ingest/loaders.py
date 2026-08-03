"""Document loaders for the knowledge base.

Reads raw files from ``data/raw`` and yields ``RawDoc`` records. The document *category*
(pyq, hr, process, ...) is inferred from the sub-directory a file lives in, e.g.
``data/raw/pyq/tcs.md`` -> category ``pyq``. Files placed directly under ``raw/`` get the
category ``misc``.

Supported formats: .md / .txt (plain text), .pdf (via pypdf), .csv (each row -> one doc).
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from .. import config


@dataclass
class RawDoc:
    """A single loaded document before cleaning/chunking."""
    doc_id: str          # stable id, e.g. "pyq/tcs_nqt_pyq.md"
    source: str          # original filename shown in citations
    category: str        # one of config.DOC_CATEGORIES (or "misc")
    text: str
    metadata: dict = field(default_factory=dict)


def _category_for(path: Path) -> str:
    """Infer the KB category from the file's parent directory name."""
    rel = path.relative_to(config.RAW_DIR)
    if len(rel.parts) >= 2:
        cat = rel.parts[0]
        if cat in config.DOC_CATEGORIES:
            return cat
    return "misc"


def _load_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages = [(page.extract_text() or "") for page in reader.pages]
    return "\n\n".join(pages)


def _load_csv(path: Path, category: str) -> Iterator[RawDoc]:
    """Each CSV row becomes a document. A 'text'/'answer'/'content' column is used as the
    body; a 'question'/'title' column (if present) is prepended for context."""
    rel = str(path.relative_to(config.RAW_DIR))
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        body_keys = ("text", "answer", "content", "response", "solution")
        head_keys = ("question", "title", "query")
        for i, row in enumerate(reader):
            body = next((row[k] for k in body_keys if row.get(k)), None)
            if not body:
                # fall back to concatenating all cells
                body = " ".join(str(v) for v in row.values() if v)
            head = next((row[k] for k in head_keys if row.get(k)), "")
            text = f"{head}\n{body}".strip() if head else body
            yield RawDoc(
                doc_id=f"{rel}#{i}",
                source=path.name,
                category=category,
                text=text,
                metadata={k: v for k, v in row.items()},
            )


def load_raw_docs() -> Iterator[RawDoc]:
    """Yield every document found under ``data/raw`` (recursively)."""
    for path in sorted(config.RAW_DIR.rglob("*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        category = _category_for(path)
        suffix = path.suffix.lower()
        rel = str(path.relative_to(config.RAW_DIR))
        if suffix in (".md", ".txt"):
            yield RawDoc(rel, path.name, category, path.read_text(encoding="utf-8"))
        elif suffix == ".pdf":
            yield RawDoc(rel, path.name, category, _load_pdf(path))
        elif suffix == ".csv":
            yield from _load_csv(path, category)
        # silently skip unsupported extensions
