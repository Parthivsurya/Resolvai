"""Document loaders for the knowledge base.

Reads raw files from ``data/raw`` and yields ``RawDoc`` records. Folder layout drives metadata:

    data/raw/<category>/<company?>/<...>/file.ext

  * the FIRST folder is the document *category* (pyq, hr, process, ...), e.g.
    ``data/raw/pyq/tcs/questions.md`` -> category ``pyq``.
  * any folder(s) BETWEEN the category and the file are the *company* / group, e.g.
    ``pyq/tcs/questions.md`` -> company ``tcs`` (nested like ``pyq/faang/google/..`` ->
    company ``faang/google``). This lets you keep company-wise PYQs in their own folders.
  * files placed directly under ``raw/`` get category ``misc`` and no company.

Supported formats: .md / .txt (plain text), .pdf (via pypdf), .docx (Word, converted to
Markdown), .csv (each row -> one doc).
"""
from __future__ import annotations

import csv
import re
import xml.etree.ElementTree as ET
import zipfile
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


# Word XML namespace. A .docx is a zip whose word/document.xml holds the body, so we read it
# with the standard library instead of adding a dependency.
_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_HEADING_STYLE_RE = re.compile(r"Heading(\d)")


def _docx_paragraph(para: ET.Element) -> tuple[str, list[tuple[bool, str]]]:
    """Return a paragraph's style name and its runs as ``(is_bold, text)`` pairs."""
    style_el = para.find(f"{_W}pPr/{_W}pStyle")
    style = style_el.get(f"{_W}val") if style_el is not None else ""
    runs = [
        (
            run.find(f"{_W}rPr/{_W}b") is not None,
            "".join(t.text or "" for t in run.iter(f"{_W}t")),
        )
        for run in para.iter(f"{_W}r")
    ]
    return style or "", [(bold, text) for bold, text in runs if text.strip()]


def _load_docx(path: Path) -> str:
    """Extract a Word document as Markdown.

    Word's own structure is translated into Markdown headings so that the structure-aware
    chunker (:mod:`.chunk`) can still split on logical sections rather than treating the
    document as one flat blob:

      * ``Heading<N>`` style        -> ``#`` * (N+1), leaving ``#`` for the document title
      * a fully bold paragraph     -> ``###`` (this is how question/topic entries are marked)
      * ``List*`` styles           -> ``-`` bullets
      * a bold lead-in + body text -> ``**Label:** body`` when the lead-in ends with a colon,
                                      otherwise the lead-in becomes a ``###`` heading
    """
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    body = root.find(f"{_W}body")
    if body is None:
        return ""

    blocks: list[str] = []
    seen_title = False
    for para in body.iter(f"{_W}p"):
        style, runs = _docx_paragraph(para)
        if not runs:
            continue
        full = "".join(text for _, text in runs).strip()

        heading = _HEADING_STYLE_RE.fullmatch(style)
        if heading:
            blocks.append("#" * min(int(heading.group(1)) + 1, 6) + f" {full}")
            continue
        if style.startswith("List"):
            blocks.append(f"- {full}")
            continue

        # split the leading run of bold text (a label or an entry title) from the body
        lead = 0
        while lead < len(runs) and runs[lead][0]:
            lead += 1
        prefix = "".join(text for _, text in runs[:lead]).strip()
        rest = "".join(text for _, text in runs[lead:]).strip()

        if prefix and not rest:
            # the first all-bold paragraph is the document title; later ones are entries
            if seen_title:
                blocks.append(f"### {prefix}")
            else:
                blocks.append(f"# {prefix}")
                seen_title = True
        elif prefix.endswith(":"):
            blocks.append(f"**{prefix}** {rest}")
        elif prefix:
            blocks.extend([f"### {prefix}", rest])
        else:
            blocks.append(full)
    return "\n\n".join(blocks)


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
        # skip dotfiles and Word's "~$name.docx" lock files left behind by an open document
        if not path.is_file() or path.name.startswith((".", "~$")):
            continue
        rel = str(path.relative_to(config.RAW_DIR))
        category, company, source_label = _rel_info(path)
        suffix = path.suffix.lower()
        if suffix in (".md", ".txt"):
            yield RawDoc(rel, source_label, category, path.read_text(encoding="utf-8"), company)
        elif suffix == ".pdf":
            yield RawDoc(rel, source_label, category, _load_pdf(path), company)
        elif suffix == ".docx":
            yield RawDoc(rel, source_label, category, _load_docx(path), company)
        elif suffix == ".csv":
            yield from _load_csv(path)
        # silently skip unsupported extensions
