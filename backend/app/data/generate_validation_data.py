"""Generates a small (20-item) labeled validation set for eval.py.

Every row has review_id, product_id, rating, review_text, date, PLUS
expected_sentiment (negative/neutral/positive, review-level) and
expected_themes (pipe-separated theme names, union across the review).
All reviews are fictional -- no real names, contacts, or copied reviews.

Deliberately includes the "hard case" categories eval.py breaks results
down by: multi-theme, "but" contrast sentences, rating-text conflict,
short reviews, and sarcasm-like wording.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROWS = [
    # -- straightforward single-theme cases --
    dict(review_id="V001", product_id="P001", rating=5, review_text="The build quality is fantastic and it still looks new after months of use.", date="2025-02-10", expected_sentiment="positive", expected_themes="quality", hard_case="plain"),
    dict(review_id="V002", product_id="P002", rating=1, review_text="It broke within a week. Total waste of money.", date="2025-03-02", expected_sentiment="negative", expected_themes="quality|value", hard_case="multi_theme"),
    dict(review_id="V003", product_id="P003", rating=5, review_text="Delivery was super fast, arrived two days early.", date="2025-01-20", expected_sentiment="positive", expected_themes="delivery", hard_case="plain"),
    dict(review_id="V004", product_id="P004", rating=2, review_text="Shipping took almost a month and tracking never updated.", date="2025-04-11", expected_sentiment="negative", expected_themes="delivery", hard_case="plain"),

    # -- multi-theme --
    dict(review_id="V005", product_id="P001", rating=4, review_text="Great value for the price, and the packaging was sturdy too.", date="2025-02-15", expected_sentiment="positive", expected_themes="value|packaging", hard_case="multi_theme"),
    dict(review_id="V006", product_id="P002", rating=2, review_text="The box arrived crushed and the item inside was scratched.", date="2025-03-18", expected_sentiment="negative", expected_themes="packaging|quality", hard_case="multi_theme"),
    dict(review_id="V007", product_id="P005", rating=3, review_text="Easy to set up but the sizing chart was way off, way too small.", date="2025-05-01", expected_sentiment="negative", expected_themes="usability|size_fit", hard_case="but_sentence"),

    # -- "but" contrast sentences --
    dict(review_id="V008", product_id="P003", rating=3, review_text="The material feels cheap but it fits true to size.", date="2025-02-28", expected_sentiment="negative", expected_themes="quality|size_fit", hard_case="but_sentence"),
    dict(review_id="V009", product_id="P004", rating=4, review_text="Setup was confusing at first, but once I figured it out it worked great.", date="2025-06-02", expected_sentiment="positive", expected_themes="usability", hard_case="but_sentence"),
    dict(review_id="V010", product_id="P001", rating=3, review_text="Shipping was fast, although the packaging was flimsy and torn.", date="2025-03-09", expected_sentiment="negative", expected_themes="delivery|packaging", hard_case="but_sentence"),

    # -- rating-text conflict (rating doesn't match the text's actual sentiment) --
    dict(review_id="V011", product_id="P002", rating=5, review_text="It's okay I guess, does the job, nothing special.", date="2025-04-22", expected_sentiment="neutral", expected_themes="quality", hard_case="rating_text_conflict"),
    dict(review_id="V012", product_id="P005", rating=1, review_text="Honestly it's fine, just arrived a little later than I hoped.", date="2025-01-30", expected_sentiment="neutral", expected_themes="delivery", hard_case="rating_text_conflict"),
    dict(review_id="V013", product_id="P003", rating=5, review_text="It broke the second day but I guess that's expected for the price.", date="2025-05-14", expected_sentiment="negative", expected_themes="quality|value", hard_case="rating_text_conflict"),

    # -- short reviews --
    dict(review_id="V014", product_id="P004", rating=5, review_text="Love it!", date="2025-02-02", expected_sentiment="positive", expected_themes="", hard_case="short"),
    dict(review_id="V015", product_id="P001", rating=1, review_text="Terrible quality.", date="2025-03-25", expected_sentiment="negative", expected_themes="quality", hard_case="short"),
    dict(review_id="V016", product_id="P002", rating=3, review_text="It's fine.", date="2025-04-05", expected_sentiment="neutral", expected_themes="", hard_case="short"),

    # -- sarcasm-like wording --
    dict(review_id="V017", product_id="P005", rating=1, review_text="Oh great, another product that falls apart in two days. Exactly what I wanted.", date="2025-05-20", expected_sentiment="negative", expected_themes="quality", hard_case="sarcasm_like"),
    dict(review_id="V018", product_id="P003", rating=1, review_text="Wow, five days late and the box was soaked, just perfect.", date="2025-06-10", expected_sentiment="negative", expected_themes="delivery|packaging", hard_case="sarcasm_like"),
    dict(review_id="V019", product_id="P001", rating=2, review_text="Sure, it's 'true to size' if you're a doll.", date="2025-02-19", expected_sentiment="negative", expected_themes="size_fit", hard_case="sarcasm_like"),

    # -- plain negation (litotes) --
    dict(review_id="V020", product_id="P004", rating=5, review_text="No complaints at all, works exactly as described.", date="2025-03-30", expected_sentiment="positive", expected_themes="quality", hard_case="negation"),
]


def generate(out_path: str | Path = "validation_reviews.csv") -> Path:
    out_path = Path(out_path)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        fieldnames = list(ROWS[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(ROWS)
    return out_path


if __name__ == "__main__":
    path = generate()
    print(f"Wrote {path.resolve()} ({len(ROWS)} labeled rows)")
