"""
Celery application configuration.
Uses Redis as both the broker and result backend.
"""

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "finplatform",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.financial_tasks",
        "app.tasks.cache_tasks",
    ],
)

# ---------------------------------------------------------------------------
# Celery configuration
# ---------------------------------------------------------------------------

celery_app.conf.update(
    # Serialization — JSON only (never pickle; security risk)
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Task routing
    task_track_started=True,
    task_acks_late=True,          # Ack after completion for reliability
    worker_prefetch_multiplier=1, # Prevent workers hoarding tasks

    # Result expiry
    result_expires=3600,

    # Beat schedule — periodic tasks
    beat_schedule={
        # Refresh top watchlist tickers every 30 seconds during market hours
        "refresh-hot-quotes": {
            "task": "app.tasks.cache_tasks.warm_quote_cache",
            "schedule": 30.0,
        },
        # Nightly financial statement refresh at 2 AM UTC
        "nightly-financials-refresh": {
            "task": "app.tasks.financial_tasks.refresh_all_financial_data",
            "schedule": crontab(hour=2, minute=0),
        },
    },
)
