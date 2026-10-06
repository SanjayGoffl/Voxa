"""Splits review text into clauses on sentence boundaries and contrast cues.

Keeps an explicit clause -> review mapping so every downstream signal can be
traced back to the exact review it came from (required for evidence display).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

import spacy

from app.config.settings import SPACY_MODEL
from app.config.themes import CONTRAST_CUES

_CONTRAST_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(c) for c in CONTRAST_CUES) + r")\b",
    flags=re.IGNORECASE,
)


@dataclass
class Clause:
    review_id: str
    clause_index: int
    text: str
    contrast_cue: str | None  # the contrast word that *introduced* this clause, if any


@lru_cache(maxsize=1)
def _get_nlp():
    return spacy.load(SPACY_MODEL, disable=["ner", "lemmatizer"])


def _split_on_contrast(sentence: str) -> list[tuple[str, str | None]]:
    """Splits one sentence into sub-clauses on contrast cues.

    Returns a list of (clause_text, introducing_cue) pairs. The first clause
    of a sentence has cue=None; any clause starting at a contrast word is
    tagged with that cue.
    """
    matches = list(_CONTRAST_PATTERN.finditer(sentence))
    if not matches:
        return [(sentence.strip(), None)]

    pieces: list[tuple[str, str | None]] = []
    start = 0
    cue_for_next: str | None = None
    for m in matches:
        chunk = sentence[start:m.start()].strip().strip(",").strip()
        if chunk:
            pieces.append((chunk, cue_for_next))
        cue_for_next = m.group(1).lower()
        start = m.end()
    tail = sentence[start:].strip().strip(",").strip()
    if tail:
        pieces.append((tail, cue_for_next))
    return [p for p in pieces if p[0]]


def split_review(review_id: str, text: str) -> list[Clause]:
    """Splits a single review's text into clauses, preserving order."""
    nlp = _get_nlp()
    doc = nlp(text)
    clauses: list[Clause] = []
    idx = 0
    for sent in doc.sents:
        for clause_text, cue in _split_on_contrast(sent.text):
            if not clause_text:
                continue
            clauses.append(
                Clause(review_id=review_id, clause_index=idx, text=clause_text, contrast_cue=cue)
            )
            idx += 1
    return clauses


def split_reviews(reviews: list[tuple[str, str]]) -> list[Clause]:
    """Splits many (review_id, text) pairs, returning a flat clause list."""
    all_clauses: list[Clause] = []
    for review_id, text in reviews:
        all_clauses.extend(split_review(review_id, text))
    return all_clauses
