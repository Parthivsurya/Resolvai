"""Build the released ResolvAI dataset from the committed corpus.

Produces the CSV components described in the IEEE DataPort document under ``dataset/``:

  placement_questions.csv  structured company interview-question bank, extracted from the
                           Word archives in data/raw/pyq/<company>/ (one row per entry)
  placement_intents.csv    copy of the labelled intent corpus (utterance, intent)
  placement_qa_eval.csv    copy of the grounded evaluation set (question, ground_truth)
  placement_abstention.csv copy of the abstention set (question, answerable, note), used to
                           score correct-abstention and unnecessary-escalation rates (RQ1)

Only ``placement_questions.csv`` is derived; the other two are curated by hand and are
copied verbatim so that one command refreshes the whole release.

Run:  ``python3 -m scripts.export_dataset``   (from the repository root)
"""
from __future__ import annotations

import csv
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend import config  # noqa: E402
from backend.ingest.loaders import _load_docx  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent.parent / "dataset"

QUESTION_FIELDS = [
    "company",
    "section",
    "entry_type",
    "title",
    "difficulty",
    "problem_statement",
    "sample_io",
    "expected_solution",
    "followups",
    "source_file",
]

# "### Question 3: Word Ladder I & II [Hard]" -> kind, title, difficulty
_ENTRY_RE = re.compile(r"^(Question\s*\d+|Scenario|Topic|Concept)\s*:\s*(.+)$", re.IGNORECASE)
_DIFFICULTY_RE = re.compile(r"\s*\[([^\]]+)\]\s*$")
_LABEL_RE = re.compile(r"^\*\*(.+?):\*\*\s*(.*)$", re.DOTALL)
# a bullet entry: "- Customer Obsession: Tell me about a time ..."
_BULLET_RE = re.compile(r"^-\s*(.+?):\s*(.+)$", re.DOTALL)

# bold labels inside an entry -> column they populate
_LABEL_TO_FIELD = {
    "problem statement": "problem_statement",
    "sample constraints / i/o": "sample_io",
    "expected solution & complexity": "expected_solution",
    "interviewer follow-ups": "followups",
}


def _blank_row(company: str, section: str, source: str) -> dict:
    row = {field: "" for field in QUESTION_FIELDS}
    row.update(company=company, section=section, source_file=source)
    return row


def _extract_entries(markdown: str, company: str, source: str) -> list[dict]:
    """Walk the converted Markdown and emit one row per question / scenario / topic."""
    rows: list[dict] = []
    section = ""
    current: dict | None = None

    def flush() -> None:
        nonlocal current
        if current and current["title"]:
            rows.append(current)
        current = None

    for block in markdown.split("\n\n"):
        block = block.strip()
        if not block:
            continue

        if block.startswith("## "):
            flush()
            section = block[3:].strip()
            continue
        if block.startswith("# "):
            flush()
            continue

        if block.startswith("### "):
            flush()
            heading = block[4:].strip()
            match = _ENTRY_RE.match(heading)
            if not match:
                continue  # document metadata heading, not a question entry
            kind, title = match.group(1), match.group(2).strip()
            difficulty = ""
            diff_match = _DIFFICULTY_RE.search(title)
            if diff_match:
                difficulty = diff_match.group(1).strip()
                title = _DIFFICULTY_RE.sub("", title).strip()
            current = _blank_row(company, section, source)
            current.update(
                entry_type="coding_question" if kind.lower().startswith("question") else kind.lower(),
                title=title,
                difficulty=difficulty,
            )
            continue

        if block.startswith("- "):
            # standalone bullet entry (leadership principles, viva topics)
            flush()
            bullet = _BULLET_RE.match(block)
            row = _blank_row(company, section, source)
            if bullet:
                row.update(entry_type="topic", title=bullet.group(1).strip(),
                           problem_statement=bullet.group(2).strip())
            else:
                row.update(entry_type="topic", title=block[2:].strip()[:120],
                           problem_statement=block[2:].strip())
            rows.append(row)
            continue

        if current is None:
            continue

        label = _LABEL_RE.match(block)
        if label:
            field = _LABEL_TO_FIELD.get(label.group(1).strip().lower())
            if field:
                current[field] = label.group(2).strip()
            elif not current["problem_statement"]:
                current["problem_statement"] = f"{label.group(1).strip()}: {label.group(2).strip()}"
        elif not current["problem_statement"]:
            current["problem_statement"] = block
        else:
            current["problem_statement"] += " " + block

    flush()
    return rows


def build_questions() -> int:
    rows: list[dict] = []
    for path in sorted((config.RAW_DIR / "pyq").rglob("*.docx")):
        if path.name.startswith((".", "~$")):
            continue
        company = path.parent.name
        rows.extend(_extract_entries(_load_docx(path), company, path.name))

    out = OUT_DIR / "placement_questions.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=QUESTION_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"placement_questions.csv  {len(rows):4} rows  ({out})")
    return len(rows)


def _copy(src: Path, name: str) -> int:
    dst = OUT_DIR / name
    shutil.copyfile(src, dst)
    with dst.open(encoding="utf-8") as fh:
        n = sum(1 for _ in csv.DictReader(fh))
    print(f"{name:24} {n:4} rows  ({dst})")
    return n


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    build_questions()
    _copy(config.INTENTS_DIR / "intents.csv", "placement_intents.csv")
    _copy(config.DATA_DIR / "eval" / "qa.csv", "placement_qa_eval.csv")
    _copy(config.DATA_DIR / "eval" / "abstention.csv", "placement_abstention.csv")


if __name__ == "__main__":
    main()
