"""CSV/Excel import: flexible column mapping, validation, reviewer-column
scrubbing.

Not every uploaded file has clean, predictable headers. This module splits
import into two phases so the caller (the API/UI) can let a human confirm or
fix the mapping before any row gets validated:

1. detect_mapping(path) -- read the file, auto-detect a canonical-column
   mapping by alias matching, and report what's missing/ambiguous.
2. apply_mapping(path, mapping) -- re-read the file and build the clean
   dataframe using an explicit (possibly human-corrected) mapping.

Never store or expose reviewer/user identifiers -- any column matching
DROPPED_COLUMN_PATTERNS is dropped before anything else happens, in both
phases.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from app.config.settings import (
    DROPPED_COLUMN_PATTERNS,
    RATING_MAX,
    RATING_MIN,
    REQUIRED_COLUMNS,
)

# Case-insensitive aliases accepted for each canonical column.
COLUMN_ALIASES = {
    "review_id": ["review_id", "id", "reviewid", "review_number"],
    "product_id": ["product_id", "productid", "product_sku", "sku"],
    "product_name": ["product_name", "productname", "product", "item_name"],
    "rating": ["rating", "stars", "star_rating", "score", "rating_1_5", "review_rating"],
    "review_text": [
        "review_text", "text", "review", "body", "comment", "content",
        "review_body", "review_comment", "feedback",
    ],
    "date": ["date", "review_date", "created_at", "timestamp", "date_posted"],
}

CANONICAL_FIELDS = list(COLUMN_ALIASES.keys())
SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


@dataclass
class MappingPreview:
    columns: list[str]
    sample_rows: list[dict[str, Any]]
    detected_mapping: dict[str, str]  # canonical -> source column
    unmapped_required: list[str]  # canonical fields we couldn't auto-detect
    dropped_reviewer_columns: list[str]
    row_count: int


@dataclass
class ImportReport:
    total_rows: int = 0
    valid_rows: int = 0
    dropped_rows: int = 0
    dropped_reviewer_columns: list[str] = field(default_factory=list)
    column_mapping: dict[str, str] = field(default_factory=dict)
    row_errors: list[dict[str, Any]] = field(default_factory=list)
    used_synthetic_product_id: bool = False


def _normalize_colname(name: str) -> str:
    return str(name).strip().lower().replace(" ", "_").replace("-", "_")


def _find_column(columns: list[str], aliases: list[str]) -> str | None:
    normalized = {_normalize_colname(c): c for c in columns}
    for alias in aliases:
        if alias in normalized:
            return normalized[alias]
    return None


def _is_reviewer_column(colname: str) -> bool:
    norm = _normalize_colname(colname)
    return any(pattern in norm for pattern in DROPPED_COLUMN_PATTERNS)


def read_any(path: str) -> pd.DataFrame:
    """Reads a CSV or Excel file into a raw dataframe based on its extension."""
    ext = Path(path).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{ext}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )
    if ext == ".csv":
        return pd.read_csv(path)
    return pd.read_excel(path)


def _strip_reviewer_columns(raw: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    reviewer_cols = [c for c in raw.columns if _is_reviewer_column(c)]
    if reviewer_cols:
        raw = raw.drop(columns=reviewer_cols)
    return raw, reviewer_cols


def detect_mapping(path: str) -> MappingPreview:
    """Reads the file and proposes a column mapping without validating rows.

    Lets the caller show the user what was auto-detected and fix anything
    wrong (differently named columns, ambiguous headers, an Excel sheet with
    extra decorative columns, etc.) before the file is actually imported.
    """
    raw = read_any(path)
    raw, reviewer_cols = _strip_reviewer_columns(raw)

    columns = list(raw.columns)
    mapping: dict[str, str] = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        found = _find_column(columns, aliases)
        if found:
            mapping[canonical] = found

    required_canonical = [f for f in CANONICAL_FIELDS if f not in ("product_id", "product_name")]
    unmapped = [f for f in required_canonical if f not in mapping]
    if "product_id" not in mapping and "product_name" not in mapping:
        unmapped.append("product_id_or_product_name")

    sample = raw.head(5).astype(str).to_dict(orient="records")

    return MappingPreview(
        columns=columns,
        sample_rows=sample,
        detected_mapping=mapping,
        unmapped_required=unmapped,
        dropped_reviewer_columns=reviewer_cols,
        row_count=len(raw),
    )


def apply_mapping(path: str, mapping: dict[str, str]) -> tuple[pd.DataFrame, ImportReport]:
    """Builds the clean, validated dataframe from an explicit canonical-field
    mapping (as produced/edited from detect_mapping's output).

    `mapping` keys are canonical fields (review_id, product_id, product_name,
    rating, review_text, date); values are the source column names in the
    file. product_id and/or product_name must be present.
    """
    raw = read_any(path)
    raw, reviewer_cols = _strip_reviewer_columns(raw)

    report = ImportReport(total_rows=len(raw), dropped_reviewer_columns=reviewer_cols)

    has_product_id = bool(mapping.get("product_id")) and mapping["product_id"] in raw.columns
    has_product_name = bool(mapping.get("product_name")) and mapping["product_name"] in raw.columns
    if not has_product_id and not has_product_name:
        raise ValueError("Mapping must include a valid product_id or product_name column.")

    required = ["review_id", "rating", "review_text", "date"]
    missing = [f for f in required if not mapping.get(f) or mapping[f] not in raw.columns]
    if missing:
        raise ValueError(f"Mapping missing or invalid for required fields: {missing}")

    report.column_mapping = dict(mapping)

    df = pd.DataFrame()
    df["review_id"] = raw[mapping["review_id"]].astype(str)
    if has_product_id:
        df["product_id"] = raw[mapping["product_id"]].astype(str)
    else:
        df["product_id"] = raw[mapping["product_name"]].astype(str)
        report.used_synthetic_product_id = True
    if has_product_name:
        df["product_name"] = raw[mapping["product_name"]].astype(str)
    else:
        df["product_name"] = df["product_id"]
    df["rating_raw"] = raw[mapping["rating"]]
    df["review_text"] = raw[mapping["review_text"]].astype(str)
    df["date_raw"] = raw[mapping["date"]]

    valid_mask = pd.Series(True, index=df.index)

    def mark_bad(mask: pd.Series, reason: str) -> None:
        nonlocal valid_mask
        bad_idx = df.index[mask & valid_mask]
        for idx in bad_idx:
            report.row_errors.append(
                {"row": int(idx), "review_id": df.at[idx, "review_id"], "reason": reason}
            )
        valid_mask &= ~mask

    mark_bad(df["review_text"].str.strip().eq("") | df["review_text"].isna(), "empty review_text")

    rating_numeric = pd.to_numeric(df["rating_raw"], errors="coerce")
    mark_bad(rating_numeric.isna(), "non-numeric rating")
    mark_bad(
        rating_numeric.notna() & ((rating_numeric < RATING_MIN) | (rating_numeric > RATING_MAX)),
        f"rating out of range [{RATING_MIN},{RATING_MAX}]",
    )

    parsed_date = pd.to_datetime(df["date_raw"], errors="coerce")
    mark_bad(parsed_date.isna(), "unparsable date")

    clean = df[valid_mask].copy()
    clean["rating"] = rating_numeric[valid_mask].astype(int)
    clean["date"] = parsed_date[valid_mask]
    clean = clean.drop(columns=["rating_raw", "date_raw"])
    clean = clean.reset_index(drop=True)

    report.valid_rows = len(clean)
    report.dropped_rows = report.total_rows - report.valid_rows
    return clean, report


def load_and_validate_csv(path: str) -> tuple[pd.DataFrame, ImportReport]:
    """Convenience wrapper: auto-detect mapping then apply it in one call.
    Used by the CLI and by /upload when no explicit mapping is supplied.
    """
    preview = detect_mapping(path)
    if preview.unmapped_required:
        raise ValueError(
            "Could not confidently map all required columns: "
            f"{preview.unmapped_required}. Detected columns: {preview.columns}. "
            "Use /upload/preview to review and correct the mapping."
        )
    return apply_mapping(path, preview.detected_mapping)


def report_to_dict(report: ImportReport) -> dict[str, Any]:
    return {
        "total_rows": report.total_rows,
        "valid_rows": report.valid_rows,
        "dropped_rows": report.dropped_rows,
        "dropped_reviewer_columns": report.dropped_reviewer_columns,
        "column_mapping": report.column_mapping,
        "row_errors": report.row_errors[:50],
        "used_synthetic_product_id": report.used_synthetic_product_id,
    }


def preview_to_dict(preview: MappingPreview) -> dict[str, Any]:
    return {
        "columns": preview.columns,
        "sample_rows": preview.sample_rows,
        "detected_mapping": preview.detected_mapping,
        "unmapped_required": preview.unmapped_required,
        "dropped_reviewer_columns": preview.dropped_reviewer_columns,
        "row_count": preview.row_count,
        "canonical_fields": CANONICAL_FIELDS,
    }
