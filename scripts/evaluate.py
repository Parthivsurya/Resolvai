"""Run the full ResolvAI evaluation suite and dump the results as JSON.

Produces every number reported on the evaluation page:

  intent      accuracy, macro/weighted precision-recall-F1, per-class table, confusion matrix
  retrieval   Recall@K, Precision@K and MRR for an ablation over retrieval configurations
              (dense only / sparse only / hybrid RRF / hybrid + intent routing)   [RQ2]
  abstention  correct-abstention and unnecessary-escalation rates swept over the
              confidence threshold, with the best operating point                 [RQ1]
  latency     per-stage wall-clock timings

Retrieval relevance labels are *weak*: each evaluation question is attributed to the source
document whose text has the highest token-overlap F1 with its reference answer, and a
retrieved chunk counts as relevant when it comes from that document. This is documented
rather than hidden — it measures document-level retrieval, not chunk-level.

Run:  ``python3 -m scripts.evaluate``   (from the repository root)
"""
from __future__ import annotations

import csv
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend import config  # noqa: E402
from backend.ingest.loaders import load_raw_docs  # noqa: E402
from backend.nlp import intent as intent_mod  # noqa: E402
from backend.retrieval import confidence, dense, hybrid, sparse  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "docs" / "evaluation_results.json"
K_VALUES = (1, 3, 5, 8)
_TOK = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> Counter:
    return Counter(_TOK.findall(text.lower()))


def _overlap_f1(a: Counter, b: Counter) -> float:
    common = sum((a & b).values())
    if not common:
        return 0.0
    precision, recall = common / sum(a.values()), common / sum(b.values())
    return 2 * precision * recall / (precision + recall)


# ----------------------------------------------------------------------------------------
# Intent classification
# ----------------------------------------------------------------------------------------
def eval_intent() -> dict:
    from sklearn.metrics import (
        accuracy_score,
        confusion_matrix,
        f1_score,
        precision_recall_fscore_support,
        precision_score,
        recall_score,
    )

    _, x_val, _, y_val = intent_mod.split_dataset()
    y_pred = [config.INTENTS.index(intent_mod.predict(t).intent) for t in x_val]

    present = sorted(set(y_val) | set(y_pred))
    p, r, f1, support = precision_recall_fscore_support(
        y_val, y_pred, labels=present, zero_division=0
    )
    per_class = [
        {
            "intent": config.INTENTS[c],
            "precision": round(float(p[i]), 3),
            "recall": round(float(r[i]), 3),
            "f1": round(float(f1[i]), 3),
            "support": int(support[i]),
        }
        for i, c in enumerate(present)
    ]
    return {
        "n_train": len(intent_mod.split_dataset()[0]),
        "n_test": len(y_val),
        "n_classes": len(config.INTENTS),
        "accuracy": round(accuracy_score(y_val, y_pred), 4),
        "macro_precision": round(precision_score(y_val, y_pred, average="macro", zero_division=0), 4),
        "macro_recall": round(recall_score(y_val, y_pred, average="macro", zero_division=0), 4),
        "macro_f1": round(f1_score(y_val, y_pred, average="macro", zero_division=0), 4),
        "weighted_f1": round(f1_score(y_val, y_pred, average="weighted", zero_division=0), 4),
        "per_class": sorted(per_class, key=lambda d: d["f1"]),
        "labels": [config.INTENTS[c] for c in present],
        "confusion_matrix": confusion_matrix(y_val, y_pred, labels=present).tolist(),
    }


# ----------------------------------------------------------------------------------------
# Retrieval ablation (RQ2)
# ----------------------------------------------------------------------------------------
def _gold_documents() -> list[dict]:
    """Attribute each evaluation question to its source document by lexical overlap."""
    docs = [(d.doc_id, _tokens(d.text)) for d in load_raw_docs()]
    rows = []
    with (config.DATA_DIR / "eval" / "qa.csv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            gt = _tokens(row["ground_truth"])
            best = max(docs, key=lambda d: _overlap_f1(gt, d[1]))
            rows.append({"question": row["question"], "gold_doc": best[0]})
    return rows


def _metrics(ranked_doc_ids: list[str], gold: str) -> dict:
    hit_rank = next((i + 1 for i, d in enumerate(ranked_doc_ids) if d == gold), 0)
    out = {"rr": 1.0 / hit_rank if hit_rank else 0.0}
    for k in K_VALUES:
        top = ranked_doc_ids[:k]
        out[f"recall@{k}"] = 1.0 if gold in top else 0.0
        out[f"precision@{k}"] = (top.count(gold) / k) if top else 0.0
    return out


def eval_retrieval() -> dict:
    gold = _gold_documents()
    top_n = max(K_VALUES)

    def run(name, fn):
        acc = []
        for row in gold:
            hits = fn(row["question"])
            acc.append(_metrics([h["doc_id"] for h in hits[:top_n]], row["gold_doc"]))
        keys = acc[0].keys()
        res = {k: round(sum(a[k] for a in acc) / len(acc), 4) for k in keys}
        res["mrr"] = res.pop("rr")
        res["config"] = name
        return res

    def routed(q):
        cat = intent_mod.predict(q).category
        hits = hybrid.search(q, top_k=top_n, category=cat)
        if cat:
            alt = hybrid.search(q, top_k=top_n, category=None)
            if confidence.score(alt) > confidence.score(hits):
                return alt
        return hits

    return {
        "n_questions": len(gold),
        "configs": [
            run("Dense only (Chroma embeddings)", lambda q: dense.search(q, top_k=top_n)),
            run("Sparse only (BM25)", lambda q: sparse.search(q, top_k=top_n)),
            run("Hybrid (RRF fusion)", lambda q: hybrid.search(q, top_k=top_n)),
            run("Hybrid + intent routing (full system)", routed),
        ],
    }


# ----------------------------------------------------------------------------------------
# Abstention (RQ1)
# ----------------------------------------------------------------------------------------
def eval_abstention() -> dict:
    rows = []
    with (config.DATA_DIR / "eval" / "abstention.csv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            q = row["question"]
            cat = intent_mod.predict(q).category
            conf = confidence.score(hybrid.search(q, category=cat))
            if cat:
                conf = max(conf, confidence.score(hybrid.search(q, category=None)))
            rows.append({"answerable": row["answerable"] == "yes", "conf": conf})

    sweep = []
    for i in range(1, 20):
        t = round(i * 0.05, 2)
        # positive class = "correctly abstained on an unanswerable question"
        tp = sum(1 for r in rows if not r["answerable"] and r["conf"] < t)
        fp = sum(1 for r in rows if r["answerable"] and r["conf"] < t)   # unnecessary escalation
        fn = sum(1 for r in rows if not r["answerable"] and r["conf"] >= t)  # missed abstention
        tn = sum(1 for r in rows if r["answerable"] and r["conf"] >= t)
        n_unans = tp + fn
        n_ans = fp + tn
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / n_unans if n_unans else 0.0
        sweep.append({
            "threshold": t,
            "correct_abstention_rate": round(rec, 3),
            "unnecessary_escalation_rate": round(fp / n_ans, 3) if n_ans else 0.0,
            "precision": round(prec, 3),
            "f1": round(2 * prec * rec / (prec + rec), 3) if (prec + rec) else 0.0,
            "accuracy": round((tp + tn) / len(rows), 3),
        })
    best = max(sweep, key=lambda s: s["f1"])
    current = min(sweep, key=lambda s: abs(s["threshold"] - config.CONFIDENCE_THRESHOLD))
    return {
        "n": len(rows),
        "n_answerable": sum(1 for r in rows if r["answerable"]),
        "mean_conf_answerable": round(
            sum(r["conf"] for r in rows if r["answerable"]) / max(1, sum(1 for r in rows if r["answerable"])), 3),
        "mean_conf_unanswerable": round(
            sum(r["conf"] for r in rows if not r["answerable"]) / max(1, sum(1 for r in rows if not r["answerable"])), 3),
        "sweep": sweep,
        "best": best,
        "current_threshold": config.CONFIDENCE_THRESHOLD,
        "current": current,
    }


# ----------------------------------------------------------------------------------------
# Latency
# ----------------------------------------------------------------------------------------
def eval_latency() -> dict:
    from backend.ingest.clean import normalize_query
    from backend.ingest.pii import mask_pii

    queries = [
        "What is the CGPA cutoff for Amazon?",
        "How many rounds are there in the TCS interview?",
        "What DSA questions does Microsoft ask?",
        "What are common HR interview questions?",
        "How do I design the Facebook news feed?",
    ]
    stages = {"preprocess": [], "intent": [], "dense": [], "sparse": [], "hybrid": []}
    for q in queries:
        t = time.perf_counter(); c = mask_pii(normalize_query(q)); stages["preprocess"].append(time.perf_counter() - t)
        t = time.perf_counter(); intent_mod.predict(c); stages["intent"].append(time.perf_counter() - t)
        t = time.perf_counter(); dense.search(c); stages["dense"].append(time.perf_counter() - t)
        t = time.perf_counter(); sparse.search(c); stages["sparse"].append(time.perf_counter() - t)
        t = time.perf_counter(); hybrid.search(c); stages["hybrid"].append(time.perf_counter() - t)
    return {
        "n_queries": len(queries),
        "stages": [
            {"stage": k, "mean_ms": round(sum(v) / len(v) * 1000, 1),
             "max_ms": round(max(v) * 1000, 1)}
            for k, v in stages.items()
        ],
        "note": "Retrieval stages only. Generation latency is dominated by the local LLM and "
                "varies with prompt length and hardware; it is excluded here.",
    }


def corpus_stats() -> dict:
    import pickle

    chunks = pickle.load(config.BM25_PATH.open("rb"))["chunks"]
    return {
        "chunks": len(chunks),
        "documents": len(set(c["doc_id"] for c in chunks)),
        "categories": dict(Counter(c["category"] for c in chunks)),
        "companies": len(set(c["company"] for c in chunks if c["company"])),
        "mean_chunk_chars": sum(len(c["text"]) for c in chunks) // len(chunks),
        "chunk_size": config.CHUNK_SIZE,
        "chunk_overlap": config.CHUNK_OVERLAP,
        "embed_model": config.EMBED_MODEL,
        "llm": config.OLLAMA_MODEL,
    }


def main() -> None:
    print("corpus …");     corpus = corpus_stats()
    print("intent …");     intent_res = eval_intent()
    print("retrieval …");  retrieval = eval_retrieval()
    print("abstention …"); abstention = eval_abstention()
    print("latency …");    latency = eval_latency()

    results = {
        "generated": time.strftime("%Y-%m-%d"),
        "corpus": corpus,
        "intent": intent_res,
        "retrieval": retrieval,
        "abstention": abstention,
        "latency": latency,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=2))
    print(f"\nwrote {OUT}")
    print(f"  intent   acc={intent_res['accuracy']} macroF1={intent_res['macro_f1']}")
    for c in retrieval["configs"]:
        print(f"  retrieval {c['config']:42} R@5={c['recall@5']} MRR={c['mrr']}")
    print(f"  abstention best t={abstention['best']['threshold']} F1={abstention['best']['f1']}")


if __name__ == "__main__":
    main()
