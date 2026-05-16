"""
Security utilities:
  - Argon2 password hashing (OWASP recommended over bcrypt for new systems)
  - JWT access/refresh token creation and verification
  - Secure token generation for email verification / password reset
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError
from jose import jwt

from app.core.config import settings

# ---------------------------------------------------------------------------
# Password hashing — Argon2id (time=2, memory=65536, parallelism=2)
# These parameters are a sensible default for web workloads.
# Increase time/memory for higher-security environments.
# ---------------------------------------------------------------------------

_ph = PasswordHasher(
    time_cost=2,
    memory_cost=65536,  # 64 MB
    parallelism=2,
    hash_len=32,
    salt_len=16,
    encoding="utf-8",
)


def hash_password(plain_password: str) -> str:
    """Return the Argon2id hash of *plain_password*."""
    return _ph.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify *plain_password* against its stored hash.
    Returns False on mismatch — never raises.
    """
    try:
        return _ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError):
        return False


def password_needs_rehash(hashed_password: str) -> bool:
    """
    Check whether the stored hash uses outdated parameters and should be
    upgraded on next successful login.
    """
    return _ph.check_needs_rehash(hashed_password)


# ---------------------------------------------------------------------------
# JWT tokens
# ---------------------------------------------------------------------------

def _create_token(data: dict[str, Any], expire_delta: timedelta) -> str:
    """Internal helper — create a signed JWT."""
    payload = data.copy()
    payload["exp"] = datetime.now(tz=timezone.utc) + expire_delta
    payload["iat"] = datetime.now(tz=timezone.utc)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(subject: str, extra_claims: dict[str, Any] | None = None) -> str:
    """
    Create a short-lived JWT access token.
    *subject* is typically the user UUID string.
    """
    data: dict[str, Any] = {"sub": subject, "type": "access"}
    if extra_claims:
        data.update(extra_claims)
    return _create_token(data, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))


def create_refresh_token(subject: str) -> str:
    """
    Create a long-lived opaque-looking JWT refresh token.
    Stored in the DB; rotation invalidates the previous one.
    """
    data: dict[str, Any] = {"sub": subject, "type": "refresh", "jti": secrets.token_hex(16)}
    return _create_token(data, timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT.
    Raises jose.JWTError on invalid/expired tokens — callers must handle.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


# ---------------------------------------------------------------------------
# One-time secure tokens (email verification, password reset)
# ---------------------------------------------------------------------------

def generate_secure_token(nbytes: int = 32) -> str:
    """Generate a URL-safe secure random token suitable for email links."""
    return secrets.token_urlsafe(nbytes)
