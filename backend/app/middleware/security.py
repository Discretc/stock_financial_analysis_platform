"""
Security middleware:
  - Adds enterprise-grade HTTP security headers (CSP, HSTS, X-Frame-Options, etc.)
  - Enforces HTTPS in production
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Injects security headers on every HTTP response.

    Headers applied:
      - X-Content-Type-Options: nosniff (prevents MIME-type sniffing)
      - X-Frame-Options: DENY (clickjacking protection)
      - X-XSS-Protection: 1; mode=block (legacy XSS filter)
      - Strict-Transport-Security (HSTS, production only)
      - Referrer-Policy: strict-origin-when-cross-origin
      - Permissions-Policy: disable browser features we don't need
      - Content-Security-Policy: restrictive default-src
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )

        if settings.is_production:
            # HSTS: 1 year, include subdomains, preload eligible
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Content Security Policy — adjust src lists for your CDN/static assets
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline'",  # tighten in production
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com",
            "img-src 'self' data: https:",
            "connect-src 'self' wss:",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        return response
