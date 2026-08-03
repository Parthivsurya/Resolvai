"""Document loaders for the knowledge base.

Reads raw files from ``data/raw`` and yields ``RawDoc`` records. Folder layout drives metadata:

    data/raw/<category>/<company?>/<...>/file.ext

  * the FIRST folder is the document *category* (pyq, hr, process, ...), e.g.
    ``data/raw/pyq/tcs/questions.md`` -> category ``pyq``.
  * any folder(s) BETWEEN the category and the file are the *company* / group, e.g.
    ``pyq/tcs/questions.md`` -> company ``tcs`` (nested like ``pyq/faang/google/..`` ->
    company ``faang/google``). This lets you keep company-wise PYQs in their own folders.
  * files placed directly under ``raw/`` get category ``misc`` and no company.

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
    doc_id: str          # stable id, e.g. "pyq/tcs/questions.md"
    source: str          # citation label, e.g. "tcs/questions.md"
    category: str        # one of config.DOC_CATEGORIES (or "misc")
    text: str
    company: str | None = None   # sub-folder(s) under the category, e.g. "tcs"
    metadata: dict = field(default_factory=dict)


def _rel_info(path: Path) -> tuple[str, str | None, str]:
    """Return (category, company, source_label) inferred from the path layout."""
    rel = path.relative_to(config.RAW_DIR)
    parts = rel.parts
    if len(parts) >= 2 and parts[0] in config.DOC_CATEGORIES:
        category = parts[0]
        middle = parts[1:-1]            # folders between category and the file
    else:
        category = "misc"
        middle = parts[:-1]
    company = "/".join(middle) if middle else None
    source_label = f"{company}/{path.name}" if company else path.name
    return category, company, source_label


def _load_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages = [(page.extract_text() or "") for page in reader.pages]
    return "\n\n".join(pages)


def _load_csv(path: Path) -> Iterator[RawDoc]:
    """Each CSV row becomes a document. A 'text'/'answer'/'content' column is used as the
    body; a 'question'/'title' column (if present) is prepended for context."""
    rel = str(path.relative_to(config.RAW_DIR))
    category, company, source_label = _rel_info(path)
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
                source=source_label,
                category=category,
                text=text,
                company=company,
                metadata={k: v for k, v in row.items()},
            )


def load_raw_docs() -> Iterator[RawDoc]:
    """Yield every document found under ``data/raw`` (recursively)."""
    for path in sorted(config.RAW_DIR.rglob("*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        rel = str(path.relative_to(config.RAW_DIR))
        category, company, source_label = _rel_info(path)
        suffix = path.suffix.lower()
        if suffix in (".md", ".txt"):
            yield RawDoc(rel, source_label, category, path.read_text(encoding="utf-8"), company)
        elif suffix == ".pdf":
            yield RawDoc(rel, source_label, category, _load_pdf(path), company)
        elif suffix == ".csv":
            yield from _load_csv(path)
        # silently skip unsupported extensions
