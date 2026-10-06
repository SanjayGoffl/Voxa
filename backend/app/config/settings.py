"""Global pipeline configuration: model names, thresholds, fusion weights.

Weights and thresholds here are fixed and documented, not tuned on the
validation set (see eval.py / README "Evaluation" section).
"""

# --- Model names (swappable) ---
SENTIMENT_MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
NLI_MODEL = "cross-encoder/nli-deberta-v3-small"
SPACY_MODEL = "en_core_web_sm"

# --- Feature flags ---
USE_NLI_VERIFIER = True  # run NLI only on low-confidence clauses
NLI_CONFIDENCE_TRIGGER = 0.15  # semantic/lexical score gap below which NLI is invoked

# --- Fusion weights (theme score = semantic * W_SEM + lexical * W_LEX [+ nli * W_NLI]) ---
THEME_FUSION_WEIGHTS = {
    "semantic": 0.6,
    "lexical": 0.4,
    "nli": 0.3,  # applied additively, renormalized when NLI is invoked
}
THEME_ASSIGNMENT_THRESHOLD = 0.45

# --- Rating prior (star rating -> sentiment prior probabilities [neg, neu, pos]) ---
RATING_SENTIMENT_PRIOR = {
    1: [0.85, 0.10, 0.05],
    2: [0.65, 0.25, 0.10],
    3: [0.20, 0.60, 0.20],
    4: [0.10, 0.25, 0.65],
    5: [0.05, 0.10, 0.85],
}
RATING_PRIOR_WEIGHT_AT_REVIEW_LEVEL = 0.2  # nudges review-level sentiment only

# --- Confidence tiers ---
# Agreement is measured as 1 - |signal_a - signal_b| across available signal pairs.
CONFIDENCE_HIGH_THRESHOLD = 0.75
CONFIDENCE_MEDIUM_THRESHOLD = 0.5
# Below CONFIDENCE_MEDIUM_THRESHOLD -> "Ambiguous" (goes to needs-human-review list)

# --- CSV import ---
REQUIRED_COLUMNS_ANY_OF = {
    "product": ["product_id", "product_name"],
}
REQUIRED_COLUMNS = ["review_id", "rating", "review_text", "date"]
DROPPED_COLUMN_PATTERNS = ["reviewer", "user", "username", "customer_name", "author"]
RATING_MIN, RATING_MAX = 1, 5

# --- Storage ---
SQLITE_PATH = "data/app.db"
