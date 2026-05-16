"""
Authentication service — registration, login, token management, lockout logic.
"""

import hashlib
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AccountLockedError,
    AuthenticationError,
    ConflictError,
    NotFoundError,
    TokenInvalidError,
)
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    password_needs_rehash,
    verify_password,
)
from app.models.user import RefreshToken, User
from app.schemas.auth import RegisterRequest, TokenResponse

logger = get_logger(__name__)


def _hash_token(token: str) -> str:
    """Store only the SHA-256 hash of the refresh token — never the raw value."""
    return hashlib.sha256(token.encode()).hexdigest()


class AuthService:
    def __init__(self, db: AsyncSession):
        self._db = db

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    async def register(self, data: RegisterRequest) -> User:
        # Check for existing email (case-insensitive)
        result = await self._db.execute(
            select(User).where(User.email == data.email.lower())
        )
        if result.scalar_one_or_none():
            raise ConflictError(f"Email already registered: {data.email}")

        user = User(
            email=data.email.lower(),
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            role="user",
            is_active=True,
            is_verified=True,  # Auto-verify: no email service configured
            verification_token=None,
            verification_token_expires=None,
        )
        self._db.add(user)
        await self._db.flush()
        logger.info("user_registered", user_id=str(user.id), email=user.email)
        return user

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    async def login(
        self, email: str, password: str, ip_address: str | None = None, device_info: str | None = None
    ) -> TokenResponse:
        result = await self._db.execute(select(User).where(User.email == email.lower()))
        user: User | None = result.scalar_one_or_none()

        # Generic message to prevent user enumeration
        generic_msg = "Invalid email or password"

        if user is None:
            # Still run a dummy hash to resist timing attacks
            hash_password("dummy_timing_resistance")
            raise AuthenticationError(generic_msg)

        # Lockout check
        if user.locked_until and user.locked_until > datetime.now(tz=timezone.utc):
            raise AccountLockedError("Account temporarily locked. Try again later.")

        if not verify_password(password, user.hashed_password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                user.locked_until = datetime.now(tz=timezone.utc) + timedelta(
                    minutes=settings.LOGIN_LOCKOUT_MINUTES
                )
                logger.warning("account_locked", user_id=str(user.id), ip=ip_address)
            await self._db.flush()
            raise AuthenticationError(generic_msg)

        if not user.is_active:
            raise AuthenticationError("Account is disabled")

        # Successful login — reset counters
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.now(tz=timezone.utc)

        # Rehash if password params are outdated
        if password_needs_rehash(user.hashed_password):
            user.hashed_password = hash_password(password)
            logger.info("password_rehashed", user_id=str(user.id))

        # Issue tokens
        access_token = create_access_token(subject=str(user.id), extra_claims={"role": user.role})
        refresh_token = create_refresh_token(subject=str(user.id))

        # Persist refresh token hash (not the raw token)
        rt = RefreshToken(
            user_id=user.id,
            token_hash=_hash_token(refresh_token),
            device_info=device_info,
            ip_address=ip_address,
            expires_at=datetime.now(tz=timezone.utc)
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        self._db.add(rt)
        await self._db.flush()

        logger.info("user_login", user_id=str(user.id), ip=ip_address)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    # ------------------------------------------------------------------
    # Token refresh (rotation)
    # ------------------------------------------------------------------

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
        except Exception as exc:
            raise TokenInvalidError("Invalid refresh token") from exc

        if payload.get("type") != "refresh":
            raise TokenInvalidError("Not a refresh token")

        token_hash = _hash_token(refresh_token)
        result = await self._db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked.is_(False),
            )
        )
        rt: RefreshToken | None = result.scalar_one_or_none()

        if rt is None or rt.expires_at < datetime.now(tz=timezone.utc):
            raise TokenInvalidError("Refresh token expired or revoked")

        # Rotate: revoke old, issue new pair
        rt.revoked = True

        user_result = await self._db.execute(select(User).where(User.id == rt.user_id))
        user: User | None = user_result.scalar_one_or_none()
        if user is None or not user.is_active:
            raise AuthenticationError("User not found or inactive")

        new_access = create_access_token(str(user.id), extra_claims={"role": user.role})
        new_refresh = create_refresh_token(str(user.id))

        new_rt = RefreshToken(
            user_id=user.id,
            token_hash=_hash_token(new_refresh),
            device_info=rt.device_info,
            ip_address=rt.ip_address,
            expires_at=datetime.now(tz=timezone.utc)
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        self._db.add(new_rt)
        await self._db.flush()

        return TokenResponse(
            access_token=new_access,
            refresh_token=new_refresh,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    # ------------------------------------------------------------------
    # Logout
    # ------------------------------------------------------------------

    async def logout(self, refresh_token: str) -> None:
        """Revoke the provided refresh token. Silently ignores missing tokens."""
        token_hash = _hash_token(refresh_token)
        result = await self._db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        rt = result.scalar_one_or_none()
        if rt:
            rt.revoked = True
            await self._db.flush()

    # ------------------------------------------------------------------
    # Email verification
    # ------------------------------------------------------------------

    async def verify_email(self, token: str) -> User:
        result = await self._db.execute(
            select(User).where(User.verification_token == token)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("Invalid verification token")
        if user.verification_token_expires and user.verification_token_expires < datetime.now(tz=timezone.utc):
            raise AuthenticationError("Verification token expired")
        user.is_verified = True
        user.verification_token = None
        user.verification_token_expires = None
        await self._db.flush()
        return user
