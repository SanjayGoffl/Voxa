"""Generates a synthetic review CSV for local dev/testing.

Produces ~100 reviews across a handful of products, with deliberate
multi-theme sentences and "but" contrast cases so downstream clause
splitting and theme fusion have real test material.
"""
from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

PRODUCTS = [
    ("P001", "Aurora Running Shoes"),
    ("P002", "Nimbus Backpack"),
    ("P003", "Cascade Water Bottle"),
    ("P004", "Halcyon Desk Lamp"),
    ("P005", "Drift Bluetooth Speaker"),
]

POSITIVE_CLAUSES = {
    "quality": ["the build quality is excellent", "it feels really sturdy and well made", "no defects at all after weeks of use"],
    "delivery": ["it arrived earlier than expected", "shipping was fast", "delivery was right on time"],
    "packaging": ["the packaging was secure and protective", "it came in a nice sturdy box", "the unboxing experience was great"],
    "size_fit": ["the size was exactly as described", "it fits perfectly", "true to size as listed"],
    "value": ["it's a great price for what you get", "excellent value for money", "worth every penny"],
    "usability": ["it was so easy to set up", "very intuitive to use", "the instructions were clear and simple"],
}

NEGATIVE_CLAUSES = {
    "quality": ["it broke after just a few days", "the material feels cheap and flimsy", "it arrived defective"],
    "delivery": ["shipping took way longer than expected", "the delivery was delayed by two weeks", "tracking info was never updated"],
    "packaging": ["the box arrived crushed", "there was barely any padding inside", "the packaging was torn open"],
    "size_fit": ["it runs way too small", "the fit was way too loose", "sizing was completely off"],
    "value": ["it feels overpriced for what you get", "not worth the money at all", "way too expensive for this quality"],
    "usability": ["the instructions were confusing", "it was way too complicated to set up", "I couldn't figure out how to use it"],
}

NEUTRAL_OPENERS = ["Overall", "So far", "Honestly", "In my experience", "After a month of use"]
CONTRASTS = ["but", "however", "although", "though", "while"]


def _clause(themes_pool: dict, theme: str, positive: bool) -> str:
    pool = POSITIVE_CLAUSES if positive else NEGATIVE_CLAUSES
    return random.choice(pool[theme])


def _make_review(themes: list[str]) -> tuple[str, int]:
    """Builds one review text referencing 1-2 themes, sometimes with a contrast clause."""
    opener = random.choice(NEUTRAL_OPENERS)
    n_themes = random.choice([1, 1, 2])  # mostly single-theme, some multi-theme
    chosen = random.sample(themes, k=min(n_themes, len(themes)))

    sentiments = []
    parts = []
    for i, theme in enumerate(chosen):
        positive = random.random() > 0.4
        sentiments.append(positive)
        clause = _clause(None, theme, positive)
        if i == 0:
            parts.append(f"{opener}, {clause}")
        else:
            contrast = random.choice(CONTRASTS)
            parts.append(f"{contrast} {clause}")

    # occasionally add an explicit contrast between two sentiments on the same theme
    if random.random() < 0.25 and len(chosen) == 1:
        theme = chosen[0]
        opposite_clause = _clause(None, theme, not sentiments[0])
        contrast = random.choice(CONTRASTS)
        parts.append(f"{contrast} {opposite_clause}")

    text = ". ".join(parts) + "."
    text = text[0].upper() + text[1:]

    pos_count = sum(1 for s in sentiments if s)
    neg_count = len(sentiments) - pos_count
    if pos_count > neg_count:
        rating = random.choice([4, 5])
    elif neg_count > pos_count:
        rating = random.choice([1, 2])
    else:
        rating = 3
    return text, rating


def generate(n_reviews: int = 100, out_path: str | Path = "sample_reviews.csv") -> Path:
    from app.config.themes import THEMES

    out_path = Path(out_path)
    start_date = datetime(2025, 1, 1)
    rows = []
    for i in range(n_reviews):
        product_id, product_name = random.choice(PRODUCTS)
        text, rating = _make_review(THEMES)
        date = start_date + timedelta(days=random.randint(0, 270))
        rows.append(
            {
                "review_id": f"R{i+1:04d}",
                "product_id": product_id,
                "product_name": product_name,
                "rating": rating,
                "review_text": text,
                "date": date.strftime("%Y-%m-%d"),
            }
        )

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    return out_path


if __name__ == "__main__":
    path = generate()
    print(f"Wrote {path.resolve()}")
