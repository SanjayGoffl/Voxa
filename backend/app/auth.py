"""Minimal in-memory auth for the hackathon demo: email+password signup/login,
bearer tokens, two roles (customer, brand). Passwords are hashed with
per-user-salted PBKDF2-HMAC-SHA256 (200k iterations); no persistence across
restarts, and still not a substitute for a real auth provider in production.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass

from fastapi import Header, HTTPException

_PBKDF2_ITERATIONS = 200_000

ROLES = {"customer", "brand"}


@dataclass
class User:
    id: str
    email: str
    password_hash: str
    role: str  # "customer" | "brand"
    display_name: str
    brand_name: str | None = None  # set when role == "brand"


_users_by_email: dict[str, User] = {}
_users_by_id: dict[str, User] = {}
_tokens: dict[str, str] = {}  # token -> user_id


def _hash_password(password: str, salt: str) -> str:
    derived = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), _PBKDF2_ITERATIONS)
    return derived.hex()


def _make_password_hash(password: str) -> str:
    salt = secrets.token_hex(16)
    return f"{salt}${_hash_password(password, salt)}"


def _verify_password(password: str, stored: str) -> bool:
    salt, _, expected = stored.partition("$")
    if not salt or not expected:
        return False
    return hmac.compare_digest(_hash_password(password, salt), expected)


def signup(email: str, password: str, role: str, display_name: str, brand_name: str | None) -> tuple[User, str]:
    email = email.strip().lower()
    if role not in ROLES:
        raise ValueError(f"role must be one of {sorted(ROLES)}")
    if email in _users_by_email:
        raise ValueError("An account with this email already exists")
    if role == "brand" and not brand_name:
        raise ValueError("brand_name is required for brand accounts")

    user = User(
        id=secrets.token_hex(8),
        email=email,
        password_hash=_make_password_hash(password),
        role=role,
        display_name=display_name or email.split("@")[0],
        brand_name=brand_name,
    )
    _users_by_email[email] = user
    _users_by_id[user.id] = user
    token = secrets.token_urlsafe(24)
    _tokens[token] = user.id
    return user, token


def login(email: str, password: str) -> tuple[User, str]:
    email = email.strip().lower()
    user = _users_by_email.get(email)
    if user is None or not _verify_password(password, user.password_hash):
        raise ValueError("Invalid email or password")
    token = secrets.token_urlsafe(24)
    _tokens[token] = user.id
    return user, token


def get_user_by_token(token: str) -> User | None:
    user_id = _tokens.get(token)
    if user_id is None:
        return None
    return _users_by_id.get(user_id)


def user_to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "display_name": user.display_name,
        "brand_name": user.brand_name,
    }


async def optional_user(authorization: str | None = Header(default=None)) -> User | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ").strip()
    return get_user_by_token(token)


async def require_user(authorization: str | None = Header(default=None)) -> User:
    user = await optional_user(authorization)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


async def require_brand(authorization: str | None = Header(default=None)) -> User:
    user = await require_user(authorization)
    if user.role != "brand":
        raise HTTPException(status_code=403, detail="Brand account required")
    return user
