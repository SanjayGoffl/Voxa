"""Lexical theme signal: keyword/phrase dictionary match per theme, with a
simple negation check (a negation cue appearing shortly before the matched
phrase flags it, rather than discarding the match outright).
"""
from __future__ import annotations

import re

from app.config.themes import NEGATION_CUES, THEME_KEYWORDS, THEMES

_NEGATION_WINDOW_CHARS = 25  # how far back to look for a negation cue before a match


def _build_patterns() -> dict[str, list[re.Pattern]]:
    patterns: dict[str, list[re.Pattern]] = {}
    for theme, phrases in THEME_KEYWORDS.items():
        patterns[theme] = [
            re.compile(r"\b" + re.escape(p) + r"\b", flags=re.IGNORECASE) for p in phrases
        ]
    return patterns


_PATTERNS = _build_patterns()
_NEGATION_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(c) for c in NEGATION_CUES) + r")\b", flags=re.IGNORECASE
)


def _is_negated_before(text: str, match_start: int) -> bool:
    window_start = max(0, match_start - _NEGATION_WINDOW_CHARS)
    window = text[window_start:match_start]
    return bool(_NEGATION_PATTERN.search(window))


def score_clause_lexical(text: str) -> dict[str, dict[str, float | bool]]:
    """Returns {theme: {"score": 0..1, "negated": bool}} for one clause.

    score is 1.0 if any keyword/phrase for that theme matched, else 0.0.
    negated is True if a negation cue appeared immediately before a match
    (signals the matched sentiment may be inverted; fusion consumes this).
    """
    result: dict[str, dict[str, float | bool]] = {
        t: {"score": 0.0, "negated": False} for t in THEMES
    }
    for theme in THEMES:
        for pattern in _PATTERNS[theme]:
            m = pattern.search(text)
            if m:
                result[theme]["score"] = 1.0
                if _is_negated_before(text, m.start()):
                    result[theme]["negated"] = True
                break
    return result


def score_clauses_lexical(texts: list[str]) -> list[dict[str, dict[str, float | bool]]]:
    return [score_clause_lexical(t) for t in texts]
