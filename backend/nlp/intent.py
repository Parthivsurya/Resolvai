"""Intent classification via a fine-tuned DistilBERT (paper pillar #6).

``train()`` fine-tunes ``distilbert-base-uncased`` on the labelled utterances in
``data/intents/intents.csv`` and saves the checkpoint to ``models/intent-distilbert``.
``predict()`` loads that checkpoint and returns the intent plus its document category for
retrieval routing. If no fine-tuned model exists yet, prediction falls back to a lightweight
keyword heuristic so the pipeline still runs.

Train with:  ``python3 -m backend.nlp.intent``
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache

from .. import config


@dataclass
class IntentResult:
    intent: str
    category: str | None
    confidence: float
    escalate: bool       # sensitive intent -> immediate human handoff
    smalltalk: bool      # greeting/out_of_scope -> answer without retrieval


# --------------------------------------------------------------------------------------
# Data
# --------------------------------------------------------------------------------------
def _load_dataset() -> tuple[list[str], list[int]]:
    texts, labels = [], []
    label2id = {name: i for i, name in enumerate(config.INTENTS)}
    with (config.INTENTS_DIR / "intents.csv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            intent = row["intent"].strip()
            if intent not in label2id:
                continue
            texts.append(row["utterance"].strip())
            labels.append(label2id[intent])
    return texts, labels


# --------------------------------------------------------------------------------------
# Training
# --------------------------------------------------------------------------------------
def train(epochs: int = 8, test_size: float = 0.2) -> dict:
    """Fine-tune DistilBERT and save it. Returns held-out metrics."""
    import numpy as np
    from datasets import Dataset
    from sklearn.metrics import accuracy_score, f1_score
    from sklearn.model_selection import train_test_split
    from transformers import (
        AutoModelForSequenceClassification,
        AutoTokenizer,
        Trainer,
        TrainingArguments,
    )

    texts, labels = _load_dataset()
    id2label = {i: name for i, name in enumerate(config.INTENTS)}
    label2id = {name: i for i, name in id2label.items()}

    x_train, x_val, y_train, y_val = train_test_split(
        texts, labels, test_size=test_size, random_state=42, stratify=None
    )

    tokenizer = AutoTokenizer.from_pretrained(config.INTENT_BASE_MODEL)

    def tok(batch):
        return tokenizer(batch["text"], truncation=True, padding="max_length", max_length=64)

    ds_train = Dataset.from_dict({"text": x_train, "label": y_train}).map(tok, batched=True)
    ds_val = Dataset.from_dict({"text": x_val, "label": y_val}).map(tok, batched=True)

    model = AutoModelForSequenceClassification.from_pretrained(
        config.INTENT_BASE_MODEL,
        num_labels=len(config.INTENTS),
        id2label=id2label,
        label2id=label2id,
    )

    def metrics(pred):
        preds = np.argmax(pred.predictions, axis=1)
        return {
            "accuracy": accuracy_score(pred.label_ids, preds),
            "macro_f1": f1_score(pred.label_ids, preds, average="macro", zero_division=0),
        }

    args = TrainingArguments(
        output_dir=str(config.INTENT_MODEL_DIR / "_trainer"),
        num_train_epochs=epochs,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=16,
        learning_rate=3e-5,
        eval_strategy="epoch",
        save_strategy="no",
        logging_steps=10,
        report_to=[],
    )
    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=ds_train,
        eval_dataset=ds_val,
        compute_metrics=metrics,
    )
    trainer.train()
    result = trainer.evaluate()

    config.INTENT_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(config.INTENT_MODEL_DIR)
    tokenizer.save_pretrained(config.INTENT_MODEL_DIR)
    print(f"Saved intent model to {config.INTENT_MODEL_DIR}")
    print(f"Held-out: accuracy={result.get('eval_accuracy'):.3f} "
          f"macro_f1={result.get('eval_macro_f1'):.3f}")
    return result


# --------------------------------------------------------------------------------------
# Inference
# --------------------------------------------------------------------------------------
@lru_cache(maxsize=1)
def _pipeline():
    """Load the fine-tuned classifier, or None if it hasn't been trained yet."""
    if not (config.INTENT_MODEL_DIR / "config.json").exists():
        return None
    from transformers import (
        AutoModelForSequenceClassification,
        AutoTokenizer,
        TextClassificationPipeline,
    )

    tokenizer = AutoTokenizer.from_pretrained(config.INTENT_MODEL_DIR)
    model = AutoModelForSequenceClassification.from_pretrained(config.INTENT_MODEL_DIR)
    return TextClassificationPipeline(
        model=model, tokenizer=tokenizer, truncation=True, top_k=1
    )


# Minimal keyword fallback so predict() works before the model is trained.
_FALLBACK_KEYWORDS = {
    "talk_to_placement_officer": ["human", "real person", "placement officer", "speak to"],
    "greeting": ["hi", "hello", "hey", "good morning", "what can you do"],
    "company_pyq": ["pyq", "previous year", "past question", "last year"],
    "aptitude_prep": ["aptitude", "quant", "reasoning"],
    "coding_round": ["coding", "dsa", "data structure"],
    "hr_interview": ["hr", "tell me about yourself", "weakness"],
    "eligibility_criteria": ["eligibility", "cgpa", "backlog", "percentage"],
    "ctc_salary": ["ctc", "salary", "package", "pay"],
    "placement_process": ["process", "rounds", "recruitment"],
    "resume_help": ["resume", "cv"],
    "interview_experience": ["experience"],
}


def _fallback(query: str) -> IntentResult:
    q = query.lower()
    for intent, kws in _FALLBACK_KEYWORDS.items():
        if any(kw in q for kw in kws):
            return _build(intent, 0.5)
    return _build("out_of_scope", 0.3)


def _build(intent: str, confidence: float) -> IntentResult:
    return IntentResult(
        intent=intent,
        category=config.DOC_CATEGORY.get(intent),
        confidence=confidence,
        escalate=intent in config.SENSITIVE_INTENTS,
        smalltalk=intent in config.SMALLTALK_INTENTS or intent == "out_of_scope",
    )


def predict(query: str) -> IntentResult:
    pipe = _pipeline()
    if pipe is None:
        return _fallback(query)
    out = pipe(query)[0]
    if isinstance(out, list):  # top_k returns a list of dicts
        out = out[0]
    score = float(out["score"])
    # If the (weak, small-data) model isn't confident, trust a keyword match when we have one.
    if score < config.INTENT_MIN_CONF:
        fb = _fallback(query)
        if fb.intent != "out_of_scope":
            return fb
    return _build(out["label"], score)


if __name__ == "__main__":
    train()
