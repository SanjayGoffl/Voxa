"""Semantic theme signal: cosine similarity between a clause and each theme's
natural-language prototype sentences, using BAAI/bge-small-en-v1.5.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config.settings import EMBEDDING_MODEL
from app.config.themes import THEME_PROTOTYPES, THEMES

# bge models are trained with an instruction prefix for queries; prototypes
# and clauses are both short natural-language sentences so we embed them
# the same way (no prefix) for a symmetric comparison.


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    return SentenceTransformer(EMBEDDING_MODEL)


@lru_cache(maxsize=1)
def _get_prototype_matrix() -> tuple[list[str], np.ndarray]:
    """Returns (theme_order_per_row, normalized_embedding_matrix) for all prototypes."""
    model = _get_model()
    rows: list[str] = []
    sentences: list[str] = []
    for theme in THEMES:
        for sent in THEME_PROTOTYPES[theme]:
            rows.append(theme)
            sentences.append(sent)
    embeddings = model.encode(sentences, normalize_embeddings=True)
    return rows, np.asarray(embeddings)


def score_clauses_semantic(clause_texts: list[str]) -> list[dict[str, float]]:
    """For each clause, returns {theme: max_cosine_similarity_to_its_prototypes}."""
    if not clause_texts:
        return []
    model = _get_model()
    theme_rows, proto_matrix = _get_prototype_matrix()
    clause_embeddings = np.asarray(model.encode(clause_texts, normalize_embeddings=True))

    # cosine similarity since both sides are L2-normalized -> dot product
    sims = clause_embeddings @ proto_matrix.T  # (n_clauses, n_prototypes)

    results: list[dict[str, float]] = []
    for row in sims:
        per_theme_max: dict[str, float] = {t: 0.0 for t in THEMES}
        for theme, sim in zip(theme_rows, row):
            if sim > per_theme_max[theme]:
                per_theme_max[theme] = float(sim)
        results.append(per_theme_max)
    return results
