"""Evaluates the pipeline against the small labeled validation set.

Run: python eval.py [--csv validation_reviews.csv]

Reports:
- Sentiment: rating-only baseline vs single-sentiment-model vs full hybrid
  (accuracy, macro-F1), review-level.
- Themes: embedding-only vs lexical-only vs hybrid (micro-F1, macro-F1),
  multi-label, review-level (union of a review's clause themes).
- Hard-case breakdown: hybrid sentiment accuracy per hard_case category
  (multi_theme, but_sentence, rating_text_conflict, short, sarcasm_like).

IMPORTANT: fusion weights and thresholds (app/config/settings.py) are NOT
tuned against this set -- it exists purely to report where the pipeline
stands, per the project's evaluation constraints. This is a 20-row set;
treat every number here as directional, not a real-world accuracy claim.
"""
from __future__ import annotations

import argparse
from collections import defaultdict

import pandas as pd
from sklearn.metrics import f1_score

from app.config.settings import THEME_ASSIGNMENT_THRESHOLD
from app.config.themes import THEMES
from app.pipeline.clause_split import split_review
from app.pipeline.fusion import analyze_review, apply_rating_prior
from app.pipeline.sentiment import score_texts
from app.pipeline.theme_lexical import score_clauses_lexical
from app.pipeline.theme_semantic import score_clauses_semantic

SENTIMENT_LABELS = ["negative", "neutral", "positive"]


def rating_only_sentiment(rating: int) -> str:
    if rating <= 2:
        return "negative"
    if rating == 3:
        return "neutral"
    return "positive"


def review_themes_from_clauses(clause_texts: list[str], mode: str) -> set[str]:
    """mode: 'semantic', 'lexical', or 'hybrid' -- which signal(s) decide
    theme assignment, mirroring fusion.py's threshold logic for a fair
    single-signal vs hybrid comparison.
    """
    if not clause_texts:
        return set()
    semantic_scores = score_clauses_semantic(clause_texts)
    lexical_scores = score_clauses_lexical(clause_texts)

    themes: set[str] = set()
    for sem, lex in zip(semantic_scores, lexical_scores):
        for theme in THEMES:
            s = sem[theme]
            l = lex[theme]["score"]
            if mode == "semantic" and s >= THEME_ASSIGNMENT_THRESHOLD:
                themes.add(theme)
            elif mode == "lexical" and l >= THEME_ASSIGNMENT_THRESHOLD:
                themes.add(theme)
            elif mode == "hybrid":
                fused = s * 0.6 + l * 0.4
                if fused >= THEME_ASSIGNMENT_THRESHOLD:
                    themes.add(theme)
    return themes


def multilabel_f1(y_true: list[set[str]], y_pred: list[set[str]], labels: list[str]) -> tuple[float, float]:
    """Returns (micro_f1, macro_f1) for multi-label sets over a fixed label space."""
    y_true_bin = [[1 if l in s else 0 for l in labels] for s in y_true]
    y_pred_bin = [[1 if l in s else 0 for l in labels] for s in y_pred]
    micro = f1_score(y_true_bin, y_pred_bin, average="micro", zero_division=0)
    macro = f1_score(y_true_bin, y_pred_bin, average="macro", zero_division=0)
    return micro, macro


def run(csv_path: str) -> None:
    df = pd.read_csv(csv_path)
    df["expected_themes"] = df["expected_themes"].fillna("")

    texts = df["review_text"].tolist()
    ratings = df["rating"].astype(int).tolist()
    model_scores = score_texts(texts)

    rating_only_preds, model_only_preds, hybrid_preds = [], [], []
    semantic_theme_preds, lexical_theme_preds, hybrid_theme_preds = [], [], []
    expected_sentiments, expected_theme_sets = [], []
    hard_case_rows = defaultdict(list)  # category -> list of (expected, predicted)

    for i, row in df.iterrows():
        rating = ratings[i]
        text = row["review_text"]
        expected_sentiment = row["expected_sentiment"]
        expected_themes = set(t for t in row["expected_themes"].split("|") if t)

        rating_pred = rating_only_sentiment(rating)
        model_pred = model_scores[i].label
        hybrid_probs = apply_rating_prior(model_scores[i].probs, rating)
        hybrid_pred = max(hybrid_probs, key=hybrid_probs.get)

        rating_only_preds.append(rating_pred)
        model_only_preds.append(model_pred)
        hybrid_preds.append(hybrid_pred)
        expected_sentiments.append(expected_sentiment)

        clauses = split_review(row["review_id"], text)
        clause_texts = [c.text for c in clauses]
        semantic_theme_preds.append(review_themes_from_clauses(clause_texts, "semantic"))
        lexical_theme_preds.append(review_themes_from_clauses(clause_texts, "lexical"))
        hybrid_theme_preds.append(review_themes_from_clauses(clause_texts, "hybrid"))
        expected_theme_sets.append(expected_themes)

        hard_case_rows[row["hard_case"]].append((expected_sentiment, hybrid_pred))

    def acc_macro_f1(y_true: list[str], y_pred: list[str]) -> tuple[float, float]:
        correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
        acc = correct / len(y_true)
        macro = f1_score(y_true, y_pred, labels=SENTIMENT_LABELS, average="macro", zero_division=0)
        return acc, macro

    print(f"\nValidation set: {len(df)} labeled rows ({csv_path})\n")

    print("=== Sentiment (review-level) ===")
    print(f"{'Method':<24}{'Accuracy':>10}{'Macro-F1':>10}")
    for name, preds in [
        ("Rating-only baseline", rating_only_preds),
        ("Sentiment model only", model_only_preds),
        ("Hybrid (model+rating)", hybrid_preds),
    ]:
        acc, macro = acc_macro_f1(expected_sentiments, preds)
        print(f"{name:<24}{acc:>10.2%}{macro:>10.2%}")

    print("\n=== Themes (review-level, multi-label) ===")
    print(f"{'Method':<24}{'Micro-F1':>10}{'Macro-F1':>10}")
    for name, preds in [
        ("Embedding-only", semantic_theme_preds),
        ("Lexical-only", lexical_theme_preds),
        ("Hybrid", hybrid_theme_preds),
    ]:
        micro, macro = multilabel_f1(expected_theme_sets, preds, THEMES)
        print(f"{name:<24}{micro:>10.2%}{macro:>10.2%}")

    print("\n=== Hard-case breakdown (hybrid sentiment accuracy) ===")
    print(f"{'Category':<24}{'N':>4}{'Accuracy':>10}")
    for category, pairs in sorted(hard_case_rows.items()):
        correct = sum(1 for t, p in pairs if t == p)
        print(f"{category:<24}{len(pairs):>4}{correct / len(pairs):>10.2%}")

    print(
        "\nNote: 20-row validation set, not a real-world accuracy claim. "
        "Fusion weights/thresholds were not tuned on this set."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="validation_reviews.csv")
    args = parser.parse_args()
    run(args.csv)
