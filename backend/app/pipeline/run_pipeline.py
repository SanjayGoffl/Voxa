"""Runs the full per-clause pipeline (clause_split -> sentiment -> theme
signals -> fusion -> confidence) over an entire reviews dataframe, once,
so analytics/API can read structured results without re-running NLP per
request.
"""
from __future__ import annotations

import pandas as pd

from app.pipeline.fusion import ClauseResult, analyze_review, apply_rating_prior
from app.pipeline.sentiment import score_texts


def analyze_dataframe(df: pd.DataFrame) -> tuple[dict[str, list[ClauseResult]], dict[str, dict]]:
    """Returns (review_id -> clause results, review_id -> review-level sentiment dict).

    Review-level sentiment is the model's own 3-class score nudged by the
    star-rating prior (per spec: the rating prior only ever touches
    review-level sentiment, never clause-level, which stays model-pure).
    """
    clause_results: dict[str, list[ClauseResult]] = {}
    review_sentiments: dict[str, dict] = {}

    texts = df["review_text"].tolist()
    review_level_scores = score_texts(texts)

    for (_, row), score in zip(df.iterrows(), review_level_scores):
        review_id = row["review_id"]
        rating = int(row["rating"])
        clause_results[review_id] = analyze_review(review_id, row["review_text"], rating=rating)

        blended_probs = apply_rating_prior(score.probs, rating)
        blended_label = max(blended_probs, key=blended_probs.get)
        review_sentiments[review_id] = {
            "label": blended_label,
            "probs": blended_probs,
            "model_only_label": score.label,
            "model_only_probs": score.probs,
        }

    return clause_results, review_sentiments
