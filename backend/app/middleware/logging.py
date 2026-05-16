"""
Request/response structured logging middleware.
Logs method, path, status, latency, and request ID on every HTTP call.
"""

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Attaches a unique request ID to each request and logs structured access logs.
    The request ID is also forwarded in the response headers for tracing.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        start = time.monotonic()

        # Make request_id available via structlog contextvars
        import structlog
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        try:
            response: Response = await call_next(request)
        except Exception as exc:
            latency_ms = int((time.monotonic() - start) * 1000)
            logger.error(
                "request_error",
                method=request.method,
                path=request.url.path,
                latency_ms=latency_ms,
                error=str(exc),
            )
            raise

        latency_ms = int((time.monotonic() - start) * 1000)
        logger.info(
            "request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            latency_ms=latency_ms,
        )

        response.headers["X-Request-ID"] = request_id
        return response
