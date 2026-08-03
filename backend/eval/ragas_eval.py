"""RAGAS evaluation of the RAG pipeline (RQ5).

Runs each question in ``data/eval/qa.csv`` through the pipeline, collects the generated answer
and the retrieved contexts, and scores groundedness with RAGAS (faithfulness, answer
relevancy, context precision/recall). Uses the *local* Ollama LLM and local embeddings so no
paid API is required.

Extra dependency:  ``pip install langchain-ollama``
Prereqs: Ollama running, indexes built, model pulled.

Run:  ``python3 -m backend.eval.ragas_eval``
"""
from __future__ import annotations

import csv

from .. import config
from ..generation import prompt as prompt_mod
from ..nlp import intent as intent_mod
from ..retrieval import hybrid


def _load_qa() -> list[dict]:
    path = config.DATA_DIR / "eval" / "qa.csv"
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _collect_samples(qa: list[dict]) -> dict:
    """Run retrieval + generation to build the RAGAS evaluation dataset."""
    from .. import pipeline

    questions, answers, contexts, ground_truths = [], [], [], []
    for row in qa:
        q = row["question"]
        intent = intent_mod.predict(q)
        hits = hybrid.search(q, category=intent.category)
        ctx, _ = prompt_mod.build_context(hits)
        result = pipeline.answer(q)

        questions.append(q)
        answers.append(result.answer)
        contexts.append([h["text"] for h in hits])
        ground_truths.append(row.get("ground_truth", ""))
    return {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    }


def main() -> None:
    from datasets import Dataset
    from langchain_ollama import ChatOllama, OllamaEmbeddings
    from ragas import evaluate
    from ragas.metrics import (
        answer_relevancy,
        context_precision,
        context_recall,
        faithfulness,
    )

    qa = _load_qa()
    dataset = Dataset.from_dict(_collect_samples(qa))

    llm = ChatOllama(model=config.OLLAMA_MODEL, base_url=config.OLLAMA_HOST, temperature=0)
    embeddings = OllamaEmbeddings(model=config.OLLAMA_MODEL, base_url=config.OLLAMA_HOST)

    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=llm,
        embeddings=embeddings,
    )
    print(result)


if __name__ == "__main__":
    main()
