"""Product-level analytics computed from the stored clause-level pipeline
results. Pure aggregation/selection logic -- no NLP model calls except the
evidence selector's reuse of the embedding model for centroid ranking.
"""
from __future__ import annotations

from collections import defaultdict

import numpy as np
import pandas as pd

from app.config.themes import THEMES
from app.pipeline.fusion import ClauseResult
from app.pipeline.summary import build_summary_text, build_theme_quick_summaries
from app.pipeline.theme_semantic import _get_model
from app.store import get_all_product_owners, get_clause_results, get_product_owner, get_review_sentiments, get_reviews

SENTIMENT_TO_SCORE = {"negative": -1.0, "neutral": 0.0, "positive": 1.0}
EVIDENCE_TOP_N = 3


def _product_review_ids(product_id: str) -> list[str]:
    df = get_reviews()
    if df is None:
        return []
    return df[df["product_id"] == product_id]["review_id"].tolist()


def list_products() -> list[dict]:
    df = get_reviews()
    if df is None:
        return []
    grouped = df.groupby(["product_id", "product_name"]).agg(
        review_count=("review_id", "count"), avg_rating=("rating", "mean")
    )
    owners = get_all_product_owners()
    out = []
    for (pid, pname), row in grouped.iterrows():
        owner = owners.get(pid)
        out.append(
            {
                "product_id": pid,
                "product_name": pname,
                "review_count": int(row["review_count"]),
                "avg_rating": round(float(row["avg_rating"]), 2),
                "verified_brand": owner["brand_name"] if owner else None,
            }
        )
    return sorted(out, key=lambda r: -r["review_count"])


def _clause_sentiment_numeric(cr: ClauseResult) -> float:
    return SENTIMENT_TO_SCORE[cr.sentiment_label]


def _select_evidence(clauses: list[ClauseResult]) -> list[dict]:
    """Picks the top EVIDENCE_TOP_N clauses closest to the group's embedding
    centroid -- extractive, verbatim excerpts, ranked by representativeness
    rather than by score alone.
    """
    if not clauses:
        return []
    if len(clauses) <= EVIDENCE_TOP_N:
        chosen = clauses
    else:
        model = _get_model()
        texts = [c.text for c in clauses]
        embeddings = np.asarray(model.encode(texts, normalize_embeddings=True))
        centroid = embeddings.mean(axis=0)
        centroid = centroid / (np.linalg.norm(centroid) + 1e-9)
        sims = embeddings @ centroid
        order = np.argsort(-sims)[:EVIDENCE_TOP_N]
        chosen = [clauses[i] for i in order]
    return [
        {
            "review_id": c.review_id,
            "text": c.text,
            "sentiment": c.sentiment_label,
            "confidence_tier": c.confidence_tier,
        }
        for c in chosen
    ]


def build_product_insights(
    product_id: str, min_rating: int | None = None, max_rating: int | None = None
) -> dict | None:
    review_ids = _product_review_ids(product_id)
    if not review_ids:
        return None

    df = get_reviews()
    product_rows = df[df["product_id"] == product_id]
    if product_rows.empty:
        return None
    product_name = product_rows.iloc[0]["product_name"]

    if min_rating is not None:
        product_rows = product_rows[product_rows["rating"] >= min_rating]
    if max_rating is not None:
        product_rows = product_rows[product_rows["rating"] <= max_rating]
    review_ids = product_rows["review_id"].tolist()
    if not review_ids:
        return {
            "product_id": product_id,
            "product_name": product_name,
            "review_count": 0,
            "sentiment_distribution": {"negative": 0, "neutral": 0, "positive": 0},
            "top_positive_themes": [],
            "top_issues": [],
            "theme_summary": [],
            "avg_rating": None,
            "avg_text_sentiment": None,
            "rating_sentiment_gap": None,
            "confidence_tier_counts": {"High": 0, "Medium": 0, "Ambiguous": 0},
            "needs_review_count": 0,
            "evidence": {t: {"positive": [], "negative": []} for t in THEMES},
            "trend": [],
            "summary_text": f"No reviews for {product_name} in the selected rating range.",
        }

    clause_results_all = get_clause_results()
    review_sentiments = get_review_sentiments()

    review_sentiment_counts = {"negative": 0, "neutral": 0, "positive": 0}
    rating_values = []
    text_sentiment_values = []
    confidence_tier_counts = {"High": 0, "Medium": 0, "Ambiguous": 0}

    theme_clause_by_sentiment: dict[str, dict[str, list[ClauseResult]]] = {
        t: {"positive": [], "negative": [], "neutral": []} for t in THEMES
    }
    monthly: dict[str, dict] = defaultdict(
        lambda: {"pos": 0, "neu": 0, "neg": 0, "theme_neg": defaultdict(int), "theme_total": defaultdict(int)}
    )

    for _, row in product_rows.iterrows():
        review_id = row["review_id"]
        rating_values.append(row["rating"])
        month_key = pd.Timestamp(row["date"]).strftime("%Y-%m")

        rs = review_sentiments.get(review_id)
        if rs:
            review_sentiment_counts[rs["label"]] += 1
            text_sentiment_values.append(SENTIMENT_TO_SCORE[rs["label"]])
            monthly[month_key][{"negative": "neg", "neutral": "neu", "positive": "pos"}[rs["label"]]] += 1

        for cr in clause_results_all.get(review_id, []):
            confidence_tier_counts[cr.confidence_tier] += 1
            for theme_result in cr.themes:
                theme_clause_by_sentiment[theme_result.theme][cr.sentiment_label].append(cr)
                monthly[month_key]["theme_total"][theme_result.theme] += 1
                if cr.sentiment_label == "negative":
                    monthly[month_key]["theme_neg"][theme_result.theme] += 1

    theme_summary = []
    for theme in THEMES:
        pos = len(theme_clause_by_sentiment[theme]["positive"])
        neg = len(theme_clause_by_sentiment[theme]["negative"])
        neu = len(theme_clause_by_sentiment[theme]["neutral"])
        total = pos + neg + neu
        theme_summary.append(
            {
                "theme": theme,
                "positive_count": pos,
                "negative_count": neg,
                "neutral_count": neu,
                "total_mentions": total,
                "negative_share": round(neg / total, 3) if total else 0.0,
            }
        )

    top_positive_themes = sorted(
        [t for t in theme_summary if t["positive_count"] > 0],
        key=lambda t: -t["positive_count"],
    )[:3]
    top_issues = sorted(
        [t for t in theme_summary if t["negative_count"] > 0],
        key=lambda t: -t["negative_count"],
    )[:3]

    avg_rating = float(np.mean(rating_values)) if rating_values else None
    avg_text_sentiment = float(np.mean(text_sentiment_values)) if text_sentiment_values else None
    rating_sentiment_gap = None
    if avg_rating is not None and avg_text_sentiment is not None:
        normalized_rating = (avg_rating - 3) / 2  # map 1..5 -> -1..1
        rating_sentiment_gap = round(normalized_rating - avg_text_sentiment, 3)

    evidence = {}
    for theme in THEMES:
        evidence[theme] = {
            "positive": _select_evidence(theme_clause_by_sentiment[theme]["positive"]),
            "negative": _select_evidence(theme_clause_by_sentiment[theme]["negative"]),
        }

    trend = []
    for month_key in sorted(monthly.keys()):
        m = monthly[month_key]
        total_reviews_month = m["pos"] + m["neu"] + m["neg"]
        theme_negative_rate = {
            theme: round(m["theme_neg"][theme] / m["theme_total"][theme], 3)
            for theme in THEMES
            if m["theme_total"][theme] > 0
        }
        trend.append(
            {
                "month": month_key,
                "review_count": total_reviews_month,
                "positive": m["pos"],
                "neutral": m["neu"],
                "negative": m["neg"],
                "theme_negative_rate": theme_negative_rate,
            }
        )

    needs_review_count = confidence_tier_counts["Ambiguous"]

    result = {
        "product_id": product_id,
        "product_name": product_name,
        "review_count": len(review_ids),
        "sentiment_distribution": review_sentiment_counts,
        "top_positive_themes": top_positive_themes,
        "top_issues": top_issues,
        "theme_summary": theme_summary,
        "avg_rating": round(avg_rating, 2) if avg_rating is not None else None,
        "avg_text_sentiment": round(avg_text_sentiment, 3) if avg_text_sentiment is not None else None,
        "rating_sentiment_gap": rating_sentiment_gap,
        "confidence_tier_counts": confidence_tier_counts,
        "needs_review_count": needs_review_count,
        "evidence": evidence,
        "trend": trend,
    }
    result["summary_text"] = build_summary_text(result)
    result["theme_quick_summaries"] = build_theme_quick_summaries(result)
    owner = get_product_owner(product_id)
    result["verified_brand"] = owner["brand_name"] if owner else None
    return result


def compare_products(product_a: str, product_b: str) -> dict | None:
    a = build_product_insights(product_a)
    b = build_product_insights(product_b)
    if a is None or b is None:
        return None
    return {"a": a, "b": b}


def explain_review(review_id: str) -> dict | None:
    row = get_reviews()
    if row is None:
        return None
    row_match = row[row["review_id"] == review_id]
    if row_match.empty:
        return None
    row_dict = row_match.iloc[0].to_dict()

    clause_results = get_clause_results().get(review_id, [])
    review_sentiment = get_review_sentiments().get(review_id)

    clauses_out = []
    for cr in clause_results:
        clauses_out.append(
            {
                "clause_index": cr.clause_index,
                "text": cr.text,
                "contrast_cue": cr.contrast_cue,
                "sentiment": {"label": cr.sentiment_label, "probs": cr.sentiment_probs},
                "assigned_themes": [
                    {
                        "theme": t.theme,
                        "fused_score": round(t.score, 3),
                        "semantic_score": round(t.semantic_score, 3),
                        "lexical_score": t.lexical_score,
                        "lexical_negated": t.lexical_negated,
                    }
                    for t in cr.themes
                ],
                "all_theme_scores": {k: round(v, 3) for k, v in cr.all_theme_scores.items()},
                "confidence_tier": cr.confidence_tier,
                "confidence_agreement": round(cr.confidence_agreement, 3),
            }
        )

    return {
        "review_id": review_id,
        "product_id": row_dict["product_id"],
        "rating": int(row_dict["rating"]),
        "review_text": row_dict["review_text"],
        "review_level_sentiment": review_sentiment,
        "clauses": clauses_out,
    }


def needs_review_list(limit: int = 100) -> list[dict]:
    out = []
    for review_id, clauses in get_clause_results().items():
        for cr in clauses:
            if cr.confidence_tier == "Ambiguous":
                row = get_reviews()
                product_id = None
                if row is not None:
                    m = row[row["review_id"] == review_id]
                    if not m.empty:
                        product_id = m.iloc[0]["product_id"]
                out.append(
                    {
                        "review_id": review_id,
                        "product_id": product_id,
                        "clause_index": cr.clause_index,
                        "text": cr.text,
                        "sentiment": cr.sentiment_label,
                        "theme_scores": {k: round(v, 3) for k, v in cr.all_theme_scores.items()},
                        "confidence_agreement": round(cr.confidence_agreement, 3),
                    }
                )
    return out[:limit]
