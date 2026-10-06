"""FastAPI app entrypoint.

Two kinds of accounts: "customer" (browses products, reads/writes comments)
and "brand" (everything a customer can do, plus importing their own review
data for their products -- imports from a brand account mark that product
as a verified brand listing rather than an anonymous import).
"""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from app.analytics import (
    build_product_insights,
    compare_products,
    explain_review,
    list_products,
    needs_review_list,
)
from app.auth import User, login, optional_user, require_user, signup, user_to_dict
from app.comments import add_comment, build_thread, upvote
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
from app.store import add_analysis, add_reviews, get_product_owner, set_product_owner

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


# --- Auth -------------------------------------------------------------


class SignupBody(BaseModel):
    email: str
    password: str
    role: str  # "customer" | "brand"
    display_name: str = ""
    brand_name: str | None = None


class LoginBody(BaseModel):
    email: str
    password: str


@app.post("/auth/signup")
def auth_signup(body: SignupBody) -> dict:
    try:
        user, token = signup(body.email, body.password, body.role, body.display_name, body.brand_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"token": token, "user": user_to_dict(user)}


@app.post("/auth/login")
def auth_login(body: LoginBody) -> dict:
    try:
        user, token = login(body.email, body.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    return {"token": token, "user": user_to_dict(user)}


@app.get("/auth/me")
def auth_me(user: User = Depends(require_user)) -> dict:
    return user_to_dict(user)


# --- Import -------------------------------------------------------------


@app.post("/upload/preview")
async def upload_preview(file: UploadFile = File(...)) -> dict:
    tmp_path = _save_upload(file)
    try:
        preview = detect_mapping(str(tmp_path))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        tmp_path.unlink(missing_ok=True)
    return preview_to_dict(preview)


@app.post("/upload")
async def upload(
    file: UploadFile = File(...),
    mapping: str | None = Form(None),
    as_brand: bool = Form(False),
    user: User | None = Depends(optional_user),
) -> dict:
    """Imports a review file into the shared running dataset.

    If `as_brand` is true, the caller must be authenticated as a brand
    account; every product_id in this file is then marked as a verified
    listing owned by that brand (shown with a verified badge to customers),
    distinct from an anonymous/unverified import of the same product.

    A product_id already owned by a *different* brand can never be claimed
    or touched by this upload -- that would let anyone overwrite another
    brand's verified listing (or dilute it with anonymous rows) just by
    reusing its product_id. The whole upload is rejected in that case,
    before any data is written.
    """
    if as_brand and (user is None or user.role != "brand"):
        raise HTTPException(status_code=403, detail="Brand account required to import as a brand")

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

    conflicting_products = []
    for product_id in df["product_id"].unique():
        owner = get_product_owner(product_id)
        if owner is not None and (user is None or owner["brand_id"] != user.id):
            conflicting_products.append(product_id)
    if conflicting_products:
        raise HTTPException(
            status_code=403,
            detail=(
                "These products are already verified under another brand and cannot be "
                f"modified by this upload: {conflicting_products}"
            ),
        )

    add_reviews(df)
    clause_results, review_sentiments = analyze_dataframe(df)
    add_analysis(clause_results, review_sentiments)

    if as_brand and user is not None:
        for product_id in df["product_id"].unique():
            set_product_owner(product_id, user.id, user.brand_name or user.display_name)

    return {"message": "upload complete", "report": report_to_dict(report)}


# --- Analytics -------------------------------------------------------------


@app.get("/products")
def get_products() -> list[dict]:
    return list_products()


@app.get("/products/{product_id}/insights")
def get_product_insights(
    product_id: str,
    min_rating: int | None = Query(None, ge=1, le=5),
    max_rating: int | None = Query(None, ge=1, le=5),
    polish_summary: bool = Query(False),
) -> dict:
    insights = build_product_insights(product_id, min_rating=min_rating, max_rating=max_rating)
    if insights is None:
        raise HTTPException(status_code=404, detail=f"No data for product '{product_id}'")
    if polish_summary:
        from app.pipeline.llm_rewrite import rewrite_summary

        insights["summary_text"] = rewrite_summary(insights["summary_text"])
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


# --- Comments -------------------------------------------------------------


class CommentBody(BaseModel):
    text: str
    parent_id: str | None = None


@app.get("/products/{product_id}/comments")
def get_comments(product_id: str) -> list[dict]:
    return build_thread(product_id)


@app.post("/products/{product_id}/comments")
def post_comment(product_id: str, body: CommentBody, user: User = Depends(require_user)) -> dict:
    try:
        comment = add_comment(product_id, user.id, user.display_name, body.text, body.parent_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": comment.id}


@app.post("/products/{product_id}/comments/{comment_id}/upvote")
def upvote_comment(product_id: str, comment_id: str, user: User = Depends(require_user)) -> dict:
    comment = upvote(comment_id, user.id, product_id)
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    return {"id": comment.id, "upvotes": comment.upvotes}
