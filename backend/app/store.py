"""Process-local in-memory store for uploaded review data and its analysis.

Multiple uploads accumulate into one running dataset (concat + dedupe by
review_id) rather than replacing each other, so a customer-facing catalog
can show products from more than one import -- e.g. a brand's own upload
sitting alongside a separately-imported dataset for the same or other
products.
"""
from __future__ import annotations

import pandas as pd

from app.pipeline.fusion import ClauseResult

_state: dict[str, object] = {
    "reviews": None,  # accumulated cleaned dataframe from all uploads
    "clause_results": {},  # review_id -> list[ClauseResult]
    "review_sentiments": {},  # review_id -> {"label": str, "probs": dict, ...}
    "product_owners": {},  # product_id -> {"brand_id", "brand_name", "verified"}
}


def add_reviews(df: pd.DataFrame) -> None:
    """Appends new rows to the running dataset, de-duplicating by review_id
    (a re-upload of the same review_id replaces the earlier row).
    """
    existing = _state["reviews"]
    if existing is None:
        _state["reviews"] = df
        return
    combined = pd.concat([existing, df], ignore_index=True)
    combined = combined.drop_duplicates(subset="review_id", keep="last").reset_index(drop=True)
    _state["reviews"] = combined


def get_reviews() -> pd.DataFrame | None:
    return _state["reviews"]


def add_analysis(
    clause_results: dict[str, list[ClauseResult]], review_sentiments: dict[str, dict]
) -> None:
    _state["clause_results"].update(clause_results)  # type: ignore[union-attr]
    _state["review_sentiments"].update(review_sentiments)  # type: ignore[union-attr]


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


def set_product_owner(product_id: str, brand_id: str, brand_name: str) -> None:
    owners: dict = _state["product_owners"]  # type: ignore[assignment]
    owners[product_id] = {"brand_id": brand_id, "brand_name": brand_name, "verified": True}


def get_product_owner(product_id: str) -> dict | None:
    owners: dict = _state["product_owners"]  # type: ignore[assignment]
    return owners.get(product_id)


def get_all_product_owners() -> dict[str, dict]:
    return _state["product_owners"]  # type: ignore[return-value]
