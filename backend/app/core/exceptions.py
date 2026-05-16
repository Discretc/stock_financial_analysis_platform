"""
Domain-specific exception hierarchy.
Using named exceptions keeps error handling explicit and avoids bare Exception catches.
"""

from typing import Any


class AppError(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, detail: Any = None):
        super().__init__(message)
        self.message = message
        self.detail = detail


# ---------------------------------------------------------------------------
# Authentication / Authorization
# ---------------------------------------------------------------------------


class AuthenticationError(AppError):
    """Raised when credentials are invalid or missing."""


class TokenExpiredError(AuthenticationError):
    """Raised when a JWT has expired."""


class TokenInvalidError(AuthenticationError):
    """Raised when a JWT signature or structure is invalid."""


class PermissionDeniedError(AppError):
    """Raised when a user lacks the required permission."""


class AccountLockedError(AuthenticationError):
    """Raised when the account is temporarily locked due to too many failures."""


# ---------------------------------------------------------------------------
# Resource errors
# ---------------------------------------------------------------------------


class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""


class ConflictError(AppError):
    """Raised when a resource already exists (e.g. duplicate email)."""


class ValidationError(AppError):
    """Raised when user-supplied data fails domain validation."""


# ---------------------------------------------------------------------------
# External API errors
# ---------------------------------------------------------------------------


class ExternalAPIError(AppError):
    """Raised when an upstream API (e.g. FMP) returns an unexpected error."""


class RateLimitExceededError(ExternalAPIError):
    """Raised when the FMP rate limit is hit."""


class ExternalAPITimeoutError(ExternalAPIError):
    """Raised when a downstream API call times out."""


# ---------------------------------------------------------------------------
# Infrastructure errors
# ---------------------------------------------------------------------------


class CacheError(AppError):
    """Raised on Redis failures (non-fatal; callers should degrade gracefully)."""


class DatabaseError(AppError):
    """Raised on unexpected database errors."""
