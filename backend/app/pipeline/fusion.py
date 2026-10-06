"""Fuses semantic + lexical (+ optional NLI, added in a later step) theme
signals into a final per-clause result, plus confidence tiers.

Weights/thresholds are fixed in app.config.settings and are NOT tuned on the
validation set (see eval.py / README "Evaluation" section).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.config.settings import (
    CONFIDENCE_HIGH_THRESHOLD,
    CONFIDENCE_MEDIUM_THRESHOLD,
    RATING_PRIOR_WEIGHT_AT_REVIEW_LEVEL,
    RATING_SENTIMENT_PRIOR,
    THEME_ASSIGNMENT_THRESHOLD,
    THEME_FUSION_WEIGHTS,
)
from app.config.themes import THEMES
from app.pipeline.clause_split import Clause, split_review
from app.pipeline.sentiment import SentimentScore, score_texts
from app.pipeline.theme_lexical import score_clauses_lexical
from app.pipeline.theme_semantic import score_clauses_semantic

SENTIMENT_LABELS = ["negative", "neutral", "positive"]


@dataclass
class ThemeResult:
    theme: str
    score: float
    semantic_score: float
    lexical_score: float
    lexical_negated: bool


@dataclass
class ClauseResult:
    review_id: str
    clause_index: int
    text: str
    contrast_cue: str | None
    sentiment_label: str
    sentiment_probs: dict[str, float]
    themes: list[ThemeResult]  # themes assigned (score >= threshold), may be empty
    all_theme_scores: dict[str, float]  # every theme's fused score, for the explain view
    confidence_tier: str  # "High" | "Medium" | "Ambiguous"
    confidence_agreement: float


def _fuse_theme_score(semantic: float, lexical: float) -> float:
    w = THEME_FUSION_WEIGHTS
    return semantic * w["semantic"] + lexical * w["lexical"]


def _confidence_tier(semantic: float, lexical: float, sentiment_probs: dict[str, float], rating_prior_label: str | None) -> tuple[str, float]:
    """Agreement = 1 - |semantic - lexical| for the winning theme's two core
    signals, further discounted if the model's top sentiment disagrees with
    the rating-derived prior label. Not a raw softmax percentage.
    """
    semantic_lexical_agreement = 1.0 - abs(semantic - lexical)

    top_sentiment = max(sentiment_probs, key=sentiment_probs.get)
    sentiment_rating_agreement = 1.0 if (rating_prior_label is None or top_sentiment == rating_prior_label) else 0.5

    agreement = 0.7 * semantic_lexical_agreement + 0.3 * sentiment_rating_agreement

    if agreement >= CONFIDENCE_HIGH_THRESHOLD:
        tier = "High"
    elif agreement >= CONFIDENCE_MEDIUM_THRESHOLD:
        tier = "Medium"
    else:
        tier = "Ambiguous"
    return tier, agreement


def _rating_prior_label(rating: int | None) -> str | None:
    if rating is None or rating not in RATING_SENTIMENT_PRIOR:
        return None
    prior = RATING_SENTIMENT_PRIOR[rating]
    idx = max(range(3), key=lambda i: prior[i])
    return SENTIMENT_LABELS[idx]


def apply_rating_prior(sentiment_probs: dict[str, float], rating: int | None) -> dict[str, float]:
    """Nudges review-level sentiment probabilities toward the rating prior.
    Only used at review level, per the spec (clause-level sentiment stays
    purely model-driven).
    """
    if rating is None or rating not in RATING_SENTIMENT_PRIOR:
        return sentiment_probs
    prior = RATING_SENTIMENT_PRIOR[rating]
    w = RATING_PRIOR_WEIGHT_AT_REVIEW_LEVEL
    blended = {
        label: (1 - w) * sentiment_probs[label] + w * prior_val
        for label, prior_val in zip(SENTIMENT_LABELS, prior)
    }
    total = sum(blended.values())
    return {k: v / total for k, v in blended.items()}


def analyze_review(review_id: str, text: str, rating: int | None = None) -> list[ClauseResult]:
    """Runs clause_split -> sentiment -> theme signals -> fusion -> confidence
    for a single review. Returns one ClauseResult per clause.
    """
    clauses: list[Clause] = split_review(review_id, text)
    if not clauses:
        return []

    clause_texts = [c.text for c in clauses]
    sentiments: list[SentimentScore] = score_texts(clause_texts)
    semantic_scores = score_clauses_semantic(clause_texts)
    lexical_scores = score_clauses_lexical(clause_texts)
    rating_prior_label = _rating_prior_label(rating)

    results: list[ClauseResult] = []
    for clause, sentiment, sem, lex in zip(clauses, sentiments, semantic_scores, lexical_scores):
        theme_scores: dict[str, float] = {}
        assigned: list[ThemeResult] = []
        for theme in THEMES:
            s = sem[theme]
            l = lex[theme]["score"]
            fused = _fuse_theme_score(s, l)
            theme_scores[theme] = fused
            if fused >= THEME_ASSIGNMENT_THRESHOLD:
                assigned.append(
                    ThemeResult(
                        theme=theme,
                        score=fused,
                        semantic_score=s,
                        lexical_score=l,
                        lexical_negated=bool(lex[theme]["negated"]),
                    )
                )

        if assigned:
            top = max(assigned, key=lambda t: t.score)
            tier, agreement = _confidence_tier(
                top.semantic_score, top.lexical_score, sentiment.probs, rating_prior_label
            )
        else:
            # no theme matched strongly enough -- confidence reflects
            # semantic/lexical agreement on the globally highest-scoring theme
            best_theme = max(theme_scores, key=theme_scores.get)
            tier, agreement = _confidence_tier(
                sem[best_theme], lex[best_theme]["score"], sentiment.probs, rating_prior_label
            )

        results.append(
            ClauseResult(
                review_id=review_id,
                clause_index=clause.clause_index,
                text=clause.text,
                contrast_cue=clause.contrast_cue,
                sentiment_label=sentiment.label,
                sentiment_probs=sentiment.probs,
                themes=sorted(assigned, key=lambda t: -t.score),
                all_theme_scores=theme_scores,
                confidence_tier=tier,
                confidence_agreement=agreement,
            )
        )
    return results
