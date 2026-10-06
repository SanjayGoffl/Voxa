"""CLI for inspecting the pipeline so far: clause split + sentiment, per clause.

Usage:
    python -m app.cli --csv sample_reviews.csv --limit 10
"""
from __future__ import annotations

import argparse

from app.pipeline.fusion import analyze_review
from app.pipeline.ingest import load_and_validate_csv
from app.pipeline.sentiment import score_texts


def run(csv_path: str, limit: int | None) -> None:
    df, report = load_and_validate_csv(csv_path)
    if limit:
        df = df.head(limit)

    for _, row in df.iterrows():
        review_id = row["review_id"]
        text = row["review_text"]
        rating = row["rating"]
        review_score = score_texts([text])[0]
        clause_results = analyze_review(review_id, text, rating=int(rating))

        print(f"\n=== {review_id} (rating={rating}) ===")
        print(f"  full text: {text}")
        print(
            f"  review-level sentiment: {review_score.label} "
            f"(neg={review_score.probs['negative']:.2f}, "
            f"neu={review_score.probs['neutral']:.2f}, "
            f"pos={review_score.probs['positive']:.2f})"
        )
        for cr in clause_results:
            cue = f"[{cr.contrast_cue}] " if cr.contrast_cue else ""
            themes_str = ", ".join(f"{t.theme}={t.score:.2f}" for t in cr.themes) or "none"
            print(
                f"    clause {cr.clause_index}: {cue}\"{cr.text}\"\n"
                f"      sentiment={cr.sentiment_label} "
                f"(neg={cr.sentiment_probs['negative']:.2f}, neu={cr.sentiment_probs['neutral']:.2f}, "
                f"pos={cr.sentiment_probs['positive']:.2f}) | "
                f"themes=[{themes_str}] | "
                f"confidence={cr.confidence_tier} ({cr.confidence_agreement:.2f})"
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="sample_reviews.csv")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    run(args.csv, args.limit)
