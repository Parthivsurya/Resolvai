"""Evaluate the fine-tuned intent classifier.

Reports accuracy and macro-F1 on a stratified held-out split of the labelled utterances, plus
a per-intent classification report. Requires the model to be trained first
(``python3 -m backend.nlp.intent``).

Run:  ``python3 -m backend.eval.intent_eval``
"""
from __future__ import annotations

from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split

from .. import config
from ..nlp import intent as intent_mod


def main() -> None:
    texts, labels = intent_mod._load_dataset()
    id2label = {i: name for i, name in enumerate(config.INTENTS)}

    _, x_val, _, y_val = train_test_split(
        texts, labels, test_size=0.3, random_state=42
    )

    if intent_mod._pipeline() is None:
        print("No trained model found. Run: python3 -m backend.nlp.intent")
        return

    y_pred = [config.INTENTS.index(intent_mod.predict(t).intent) for t in x_val]

    print(f"Accuracy : {accuracy_score(y_val, y_pred):.3f}")
    print(f"Macro-F1 : {f1_score(y_val, y_pred, average='macro', zero_division=0):.3f}\n")
    labels_present = sorted(set(y_val) | set(y_pred))
    print(classification_report(
        y_val, y_pred,
        labels=labels_present,
        target_names=[id2label[i] for i in labels_present],
        zero_division=0,
    ))


if __name__ == "__main__":
    main()
