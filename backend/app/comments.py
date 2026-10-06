"""Reddit-style comment threads on products. In-memory, product-scoped,
flat storage with parent_id for nesting. Comments are about the PRODUCT,
never about a specific reviewer -- this is a discussion layer on top of the
review analytics, not a reviewer-identity feature.
"""
from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Comment:
    id: str
    product_id: str
    author_id: str
    author_name: str
    text: str
    created_at: str
    parent_id: str | None = None
    upvotes: int = 0


_comments: dict[str, list[Comment]] = {}  # product_id -> comments
_upvoted_by: dict[str, set[str]] = {}  # comment_id -> set of user_ids who upvoted


def add_comment(product_id: str, author_id: str, author_name: str, text: str, parent_id: str | None) -> Comment:
    text = text.strip()
    if not text:
        raise ValueError("Comment text cannot be empty")
    if len(text) > 2000:
        raise ValueError("Comment too long (max 2000 characters)")

    comment = Comment(
        id=secrets.token_hex(6),
        product_id=product_id,
        author_id=author_id,
        author_name=author_name,
        text=text,
        created_at=datetime.now(timezone.utc).isoformat(),
        parent_id=parent_id,
    )
    _comments.setdefault(product_id, []).append(comment)
    return comment


def list_comments(product_id: str) -> list[Comment]:
    return _comments.get(product_id, [])


def upvote(comment_id: str, user_id: str, product_id: str) -> Comment | None:
    for c in _comments.get(product_id, []):
        if c.id == comment_id:
            voters = _upvoted_by.setdefault(comment_id, set())
            if user_id not in voters:
                voters.add(user_id)
                c.upvotes += 1
            return c
    return None


def comment_to_dict(c: Comment) -> dict:
    return {
        "id": c.id,
        "product_id": c.product_id,
        "author_name": c.author_name,
        "text": c.text,
        "created_at": c.created_at,
        "parent_id": c.parent_id,
        "upvotes": c.upvotes,
    }


def build_thread(product_id: str) -> list[dict]:
    """Returns top-level comments with nested `replies`, newest top-level first,
    replies oldest-first for readability.
    """
    comments = list_comments(product_id)
    by_parent: dict[str | None, list[Comment]] = {}
    for c in comments:
        by_parent.setdefault(c.parent_id, []).append(c)

    def build(parent_id: str | None) -> list[dict]:
        children = sorted(by_parent.get(parent_id, []), key=lambda c: c.created_at)
        return [{**comment_to_dict(c), "replies": build(c.id)} for c in children]

    top_level = build(None)
    return list(reversed(top_level))
