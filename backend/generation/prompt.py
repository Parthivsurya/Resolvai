"""Grounded prompt construction and citation formatting.

The system prompt enforces the paper's core guarantee: answer **only** from the retrieved
context, cite sources inline as ``[n]``, and say you don't know rather than inventing facts.
"""
from __future__ import annotations

GROUNDED_SYSTEM = (
    "You are ResolvAI, a campus placement and interview-preparation assistant for students. "
    "Answer the question using ONLY the numbered context passages provided. "
    "Cite the passages you use inline with their number in square brackets, e.g. [1], [2]. "
    "If the context does not contain the answer, reply exactly: "
    "\"I don't have that information in my knowledge base.\" "
    "Do not invent companies, questions, salaries, or policies. Be concise and student-friendly."
)


def build_context(hits: list[dict]) -> tuple[str, list[dict]]:
    """Render retrieved chunks into a numbered context block and a parallel citation list."""
    lines, citations = [], []
    for i, hit in enumerate(hits, start=1):
        company = hit.get("company")
        label = f"{company} · {hit['source']}" if company else hit["source"]
        lines.append(f"[{i}] (source: {label}) {hit['text']}")
        citations.append(
            {
                "n": i,
                "source": hit["source"],
                "company": company,
                "doc_id": hit.get("doc_id"),
                "category": hit.get("category"),
                "score": round(float(hit.get("dense_score", 0.0)), 3),
            }
        )
    return "\n\n".join(lines), citations


def build_prompt(question: str, context: str) -> str:
    return (
        f"Context passages:\n{context}\n\n"
        f"Question: {question}\n\n"
        f"Answer (cite passages as [n]):"
    )
