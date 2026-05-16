"""
FastAPI application factory.

Startup responsibilities:
  1. Configure structured logging
  2. Initialise Redis connection pool
  3. Register all API routers
  4. Apply CORS, security headers, rate limiting, and logging middleware
  5. Register global exception handlers

Shutdown responsibilities:
  1. Close FMP HTTP client
  2. Close Redis pool
"""

from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging, get_logger
from app.core.redis import close_redis, init_redis
from app.middleware.logging import LoggingMiddleware
from app.middleware.security import SecurityHeadersMiddleware
from app.services.fmp_service import fmp_client

# ---------------------------------------------------------------------------
# Logging — must be configured before anything logs
# ---------------------------------------------------------------------------

configure_logging()
logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Sentry (production error tracking)
# ---------------------------------------------------------------------------

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
        send_default_pii=False,  # Never send PII to Sentry
    )

# ---------------------------------------------------------------------------
# Rate limiter (slowapi wraps limits.storage.RedisStorage in production)
# ---------------------------------------------------------------------------

limiter = Limiter(key_func=get_remote_address)


# ---------------------------------------------------------------------------
# Application lifespan (replaces deprecated on_event handlers)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("app_startup", environment=settings.ENVIRONMENT)
    await init_redis()
    logger.info("redis_connected")
    yield
    # Shutdown
    await fmp_client.close()
    await close_redis()
    logger.info("app_shutdown")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/docs" if settings.is_development else None,   # Disable Swagger in production
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
    )

    # ---- Middleware (outermost to innermost) ----------------------------

    # 1. CORS — validate origins strictly
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
        max_age=600,
    )

    # 2. Security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # 3. Request logging / tracing
    app.add_middleware(LoggingMiddleware)

    # ---- Rate limiting --------------------------------------------------
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # ---- Prometheus metrics ---------------------------------------------
    Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

    # ---- API routes -----------------------------------------------------
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # ---- Health check (no auth required) --------------------------------
    @app.get("/health", include_in_schema=False)
    async def health():
        return {"status": "ok", "version": settings.APP_VERSION}

    # ---- Global exception handler ---------------------------------------
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        """Convert domain exceptions to structured JSON error responses."""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.message},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("unhandled_exception", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    return app


app = create_application()
