"""Process-local in-memory store for the currently uploaded dataset and its
analysis results. Step-4 scope: holds everything analytics/API need to read
without re-running NLP per request.
"""
from __future__ import annotations

import pandas as pd

from app.pipeline.fusion import ClauseResult

_state: dict[str, object] = {
    "reviews": None,  # cleaned dataframe from ingest
    "clause_results": {},  # review_id -> list[ClauseResult]
    "review_sentiments": {},  # review_id -> {"label": str, "probs": dict}
}


def set_reviews(df: pd.DataFrame) -> None:
    _state["reviews"] = df


def get_reviews() -> pd.DataFrame | None:
    return _state["reviews"]


def set_analysis(
    clause_results: dict[str, list[ClauseResult]], review_sentiments: dict[str, dict]
) -> None:
    _state["clause_results"] = clause_results
    _state["review_sentiments"] = review_sentiments


def get_clause_results() -> dict[str, list[ClauseResult]]:
    return _state["clause_results"]  # type: ignore[return-value]


def get_review_sentiments() -> dict[str, dict]:
    return _state["review_sentiments"]  # type: ignore[return-value]


def get_review_row(review_id: str) -> dict | None:
    df = get_reviews()
    if df is None:
        return None
    match = df[df["review_id"] == review_id]
    if match.empty:
        return None
    return match.iloc[0].to_dict()
