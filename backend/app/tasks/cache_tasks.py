"""Cache warming tasks."""
import asyncio

from app.core.logging import get_logger
from app.tasks.celery_app import celery_app
from app.tasks.financial_tasks import HOT_TICKERS

logger = get_logger(__name__)


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.tasks.cache_tasks.warm_quote_cache")
def warm_quote_cache() -> dict:
    """Pre-fetch and cache quotes for hot tickers."""
    from app.services.fmp_service import fmp_client

    async def _warm():
        data = await fmp_client.get_batch_quotes(HOT_TICKERS)
        return len(data)

    count = _run_async(_warm())
    logger.info("quote_cache_warmed", count=count)
    return {"count": count}
