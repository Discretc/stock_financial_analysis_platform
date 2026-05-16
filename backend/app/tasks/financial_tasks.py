"""
Background tasks for financial data refresh.
These run as Celery workers outside the main FastAPI process.
"""

import asyncio

from app.core.logging import get_logger
from app.tasks.celery_app import celery_app

logger = get_logger(__name__)

# Popular tickers to keep warm — extend based on user activity data
HOT_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B",
    "JPM", "V", "UNH", "JNJ", "XOM", "WMT", "PG", "MA", "HD", "CVX",
    "ABBV", "LLY", "MRK", "AVGO", "PEP", "COST", "KO", "ADBE", "CRM",
]


def _run_async(coro):
    """Execute an async coroutine in a Celery worker (sync context)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    name="app.tasks.financial_tasks.refresh_financial_data",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def refresh_financial_data(self, ticker: str) -> dict:
    """
    Fetch and store all financial statements for a single ticker.
    Triggered on-demand or as part of the nightly batch.
    """
    from app.core.database import AsyncSessionLocal
    from app.services.financial_service import FinancialService

    async def _fetch(ticker: str):
        async with AsyncSessionLocal() as db:
            svc = FinancialService(db)
            await svc.fetch_and_store_income_statements(ticker, "annual", 10)
            await svc.fetch_and_store_income_statements(ticker, "quarterly", 12)
            await svc.fetch_and_store_balance_sheets(ticker, "annual", 10)
            await svc.fetch_and_store_balance_sheets(ticker, "quarterly", 12)
            await svc.fetch_and_store_cash_flows(ticker, "annual", 10)
            await svc.fetch_and_store_cash_flows(ticker, "quarterly", 12)
            await db.commit()

    try:
        _run_async(_fetch(ticker))
        logger.info("financial_data_refreshed", ticker=ticker)
        return {"ticker": ticker, "status": "success"}
    except Exception as exc:
        logger.error("financial_data_refresh_failed", ticker=ticker, error=str(exc))
        raise self.retry(exc=exc)


@celery_app.task(
    name="app.tasks.financial_tasks.refresh_all_financial_data",
    bind=True,
)
def refresh_all_financial_data(self) -> dict:
    """Nightly batch: refresh all hot tickers."""
    results = []
    for ticker in HOT_TICKERS:
        result = refresh_financial_data.delay(ticker)
        results.append({"ticker": ticker, "task_id": str(result.id)})
    logger.info("nightly_refresh_dispatched", count=len(results))
    return {"dispatched": len(results)}
