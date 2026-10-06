"""3-class sentiment scoring (negative/neutral/positive) for clauses and reviews.

Single model, name configurable via app.config.settings.SENTIMENT_MODEL.
No extra negation hacks: negation handling is left entirely to the model,
per the hard constraint in the project brief.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from app.config.settings import SENTIMENT_MODEL

LABELS = ["negative", "neutral", "positive"]


@dataclass
class SentimentScore:
    label: str
    probs: dict[str, float]  # {"negative": .., "neutral": .., "positive": ..}


@lru_cache(maxsize=1)
def _get_model_and_tokenizer():
    tokenizer = AutoTokenizer.from_pretrained(SENTIMENT_MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(SENTIMENT_MODEL)
    model.eval()
    return model, tokenizer


def _label_order(model) -> list[str]:
    """Maps the model's own id2label onto our canonical negative/neutral/positive order."""
    id2label = model.config.id2label
    order = []
    for i in range(len(id2label)):
        raw = id2label[i].lower()
        if "neg" in raw:
            order.append("negative")
        elif "neu" in raw:
            order.append("neutral")
        else:
            order.append("positive")
    return order


def score_texts(texts: list[str]) -> list[SentimentScore]:
    """Batch-scores a list of texts. Empty list returns empty list."""
    if not texts:
        return []
    model, tokenizer = _get_model_and_tokenizer()
    order = _label_order(model)

    inputs = tokenizer(texts, return_tensors="pt", padding=True, truncation=True, max_length=256)
    with torch.no_grad():
        logits = model(**inputs).logits
    probs = torch.softmax(logits, dim=-1).tolist()

    results = []
    for p in probs:
        prob_map = {order[i]: p[i] for i in range(len(order))}
        # ensure all three canonical labels exist even if a model has fewer classes
        for label in LABELS:
            prob_map.setdefault(label, 0.0)
        top_label = max(prob_map, key=prob_map.get)
        results.append(SentimentScore(label=top_label, probs=prob_map))
    return results


def score_text(text: str) -> SentimentScore:
    return score_texts([text])[0]
