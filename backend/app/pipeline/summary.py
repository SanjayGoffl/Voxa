"""Template-based strengths/issues summary, filled from the numbers and
evidence excerpts analytics already computed. No LLM call -- pure string
templating, deterministic and offline.
"""
from __future__ import annotations


def build_summary_text(insights: dict) -> str:
    name = insights["product_name"]
    review_count = insights["review_count"]
    dist = insights["sentiment_distribution"]
    pos, neu, neg = dist["positive"], dist["neutral"], dist["negative"]

    lines = [
        f"{name} has {review_count} reviews analyzed "
        f"({pos} positive, {neu} neutral, {neg} negative)."
    ]

    top_positive = insights["top_positive_themes"]
    if top_positive:
        theme_names = ", ".join(t["theme"] for t in top_positive)
        lines.append(f"Customers most often praise: {theme_names}.")

    top_issues = insights["top_issues"]
    if top_issues:
        issue_bits = ", ".join(
            f"{t['theme']} ({t['negative_count']} mentions, "
            f"{t['negative_share'] * 100:.0f}% negative)"
            for t in top_issues
        )
        lines.append(f"Recurring issues: {issue_bits}.")
    else:
        lines.append("No recurring issues stood out above the detection threshold.")

    gap = insights.get("rating_sentiment_gap")
    if gap is not None and abs(gap) > 0.3:
        direction = "more negative than" if gap < 0 else "more positive than"
        lines.append(
            f"Review text sentiment runs {direction} the star ratings would suggest "
            "-- worth a manual look."
        )

    needs_review = insights.get("needs_review_count", 0)
    if needs_review:
        lines.append(
            f"{needs_review} clause(s) landed in the Ambiguous confidence tier and are "
            "queued for human review."
        )

    return " ".join(lines)
