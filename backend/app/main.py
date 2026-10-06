"""FastAPI app entrypoint.

/upload/preview lets the caller see the auto-detected column mapping (and
what it couldn't confidently detect) before committing to an import -- not
every spreadsheet has clean, predictable headers. /upload accepts an
optional explicit mapping (as produced/edited from that preview); without
one it falls back to full auto-detection.
"""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.analytics import (
    build_product_insights,
    compare_products,
    explain_review,
    list_products,
    needs_review_list,
)
from app.export import build_csv, build_pdf
from app.pipeline.ingest import (
    SUPPORTED_EXTENSIONS,
    apply_mapping,
    detect_mapping,
    load_and_validate_csv,
    preview_to_dict,
    report_to_dict,
)
from app.pipeline.run_pipeline import analyze_dataframe
from app.store import set_analysis, set_reviews

app = FastAPI(title="Retail Review Insights")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _save_upload(file: UploadFile) -> Path:
    ext = Path(file.filename or "").suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
        )
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        return Path(tmp.name)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/upload/preview")
async def upload_preview(file: UploadFile = File(...)) -> dict:
    """Reads the file and returns the auto-detected column mapping, sample
    rows, and any required fields it couldn't confidently map -- so the
    caller can let a human confirm or correct the mapping before import.
    """
    tmp_path = _save_upload(file)
    try:
        preview = detect_mapping(str(tmp_path))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        tmp_path.unlink(missing_ok=True)
    return preview_to_dict(preview)


@app.post("/upload")
async def upload(file: UploadFile = File(...), mapping: str | None = Form(None)) -> dict:
    """Imports a review file. If `mapping` (JSON object: canonical field ->
    source column) is supplied, it is used as-is -- this is how a
    human-corrected mapping from /upload/preview gets applied. Otherwise the
    importer auto-detects the mapping and fails loudly if it can't do so
    confidently, rather than guessing.
    """
    tmp_path = _save_upload(file)
    try:
        if mapping:
            try:
                mapping_dict = json.loads(mapping)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="mapping must be a JSON object")
            df, report = apply_mapping(str(tmp_path), mapping_dict)
        else:
            df, report = load_and_validate_csv(str(tmp_path))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        tmp_path.unlink(missing_ok=True)

    set_reviews(df)
    clause_results, review_sentiments = analyze_dataframe(df)
    set_analysis(clause_results, review_sentiments)

    return {"message": "upload complete", "report": report_to_dict(report)}


@app.get("/products")
def get_products() -> list[dict]:
    return list_products()


@app.get("/products/{product_id}/insights")
def get_product_insights(
    product_id: str,
    min_rating: int | None = Query(None, ge=1, le=5),
    max_rating: int | None = Query(None, ge=1, le=5),
) -> dict:
    insights = build_product_insights(product_id, min_rating=min_rating, max_rating=max_rating)
    if insights is None:
        raise HTTPException(status_code=404, detail=f"No data for product '{product_id}'")
    return insights


@app.get("/compare")
def get_compare(a: str = Query(...), b: str = Query(...)) -> dict:
    result = compare_products(a, b)
    if result is None:
        raise HTTPException(status_code=404, detail="One or both products not found")
    return result


@app.get("/review/{review_id}/explain")
def get_review_explain(review_id: str) -> dict:
    result = explain_review(review_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No data for review '{review_id}'")
    return result


@app.get("/needs-review")
def get_needs_review(limit: int = 100) -> list[dict]:
    return needs_review_list(limit=limit)


@app.get("/export")
def export_report(product: str = Query(...), format: str = Query("csv")) -> Response:
    insights = build_product_insights(product)
    if insights is None:
        raise HTTPException(status_code=404, detail=f"No data for product '{product}'")

    if format == "csv":
        content = build_csv(insights)
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{product}_insights.csv"'},
        )
    if format == "pdf":
        content = build_pdf(insights)
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{product}_insights.pdf"'},
        )
    raise HTTPException(status_code=400, detail="format must be 'csv' or 'pdf'")
