"""
Financial Modeling Prep (FMP) HTTP client.

Design decisions:
  - All API calls happen server-side — the FMP key is never sent to the frontend.
  - Tenacity retries on transient HTTP 5xx / network errors with exponential back-off.
  - Each method normalises the raw FMP payload into a clean internal dict,
    decoupling the rest of the codebase from FMP's response shape.
  - Redis caching is applied transparently at this layer.
"""

import hashlib
import time
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.core.exceptions import (
    ExternalAPIError,
    ExternalAPITimeoutError,
    RateLimitExceededError,
)
from app.core.logging import get_logger
from app.core.redis import cache_get, cache_set

logger = get_logger(__name__)


def _cache_key(path: str, params: dict[str, Any]) -> str:
    """
    Deterministic Redis key: sha256 of sorted param string to avoid
    key-injection from user-supplied tickers.
    """
    raw = path + "::" + "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return f"fmp:{digest}"


class FMPClient:
    """
    Async HTTP client wrapping the FMP REST API.
    Instantiated once and reused (shared httpx.AsyncClient with connection pooling).
    """

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None
        self._stable_client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=settings.FMP_BASE_URL,
                timeout=httpx.Timeout(settings.FMP_TIMEOUT_SECONDS),
                limits=httpx.Limits(max_connections=50, max_keepalive_connections=20),
                headers={"Accept": "application/json"},
            )
        return self._client

    async def _get_stable_client(self) -> httpx.AsyncClient:
        """Separate client for the /stable API (financial statements)."""
        if self._stable_client is None or self._stable_client.is_closed:
            self._stable_client = httpx.AsyncClient(
                base_url=settings.FMP_BASE_URL_STABLE,
                timeout=httpx.Timeout(settings.FMP_TIMEOUT_SECONDS),
                limits=httpx.Limits(max_connections=50, max_keepalive_connections=20),
                headers={"Accept": "application/json"},
            )
        return self._stable_client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
        if self._stable_client and not self._stable_client.is_closed:
            await self._stable_client.aclose()

    # ------------------------------------------------------------------
    # Core request method with retry + caching
    # ------------------------------------------------------------------

    @retry(
        retry=retry_if_exception_type((httpx.TransportError, httpx.TimeoutException)),
        stop=stop_after_attempt(settings.FMP_MAX_RETRIES),
        wait=wait_exponential(multiplier=settings.FMP_RETRY_BACKOFF_SECONDS, min=1, max=10),
        reraise=True,
    )
    async def _request(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        cache_ttl: int | None = None,
        stable: bool = False,
    ) -> Any:
        """
        Execute a GET request against the FMP base URL.
        Injects the API key, handles errors, and optionally caches the result.
        """
        params = params or {}
        # API key injected server-side — never exposed in frontend/logs
        params["apikey"] = settings.FMP_API_KEY

        # Attempt cache hit first
        cache_key = _cache_key(path, {k: v for k, v in params.items() if k != "apikey"})
        if cache_ttl:
            cached = await cache_get(cache_key)
            if cached is not None:
                logger.debug("fmp_cache_hit", path=path)
                return cached

        client = await (self._get_stable_client() if stable else self._get_client())
        t0 = time.monotonic()
        try:
            response = await client.get(path, params=params)
            latency_ms = int((time.monotonic() - t0) * 1000)
            logger.info("fmp_request", path=path, status=response.status_code, latency_ms=latency_ms)
        except httpx.TimeoutException as exc:
            raise ExternalAPITimeoutError(f"FMP timeout: {path}") from exc
        except httpx.TransportError as exc:
            raise ExternalAPIError(f"FMP transport error: {path} — {exc}") from exc

        if response.status_code == 429:
            raise RateLimitExceededError("FMP rate limit exceeded")

        if response.status_code >= 500:
            raise ExternalAPIError(f"FMP server error {response.status_code}: {path}")

        if response.status_code == 401:
            raise ExternalAPIError("FMP authentication failed — check API key")

        if response.status_code >= 400:
            raise ExternalAPIError(f"FMP client error {response.status_code}: {path}")

        data = response.json()

        # Cache successful non-empty responses
        if cache_ttl and data:
            await cache_set(cache_key, data, cache_ttl)

        return data

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    async def search(self, query: str, limit: int = 20) -> list[dict]:
        """Ticker/company search with autocomplete (uses stable /search-symbol endpoint)."""
        data = await self._request(
            "/search-symbol",
            params={"query": query, "limit": limit},
            cache_ttl=settings.CACHE_TTL_SEARCH_RESULTS,
            stable=True,
        )
        return data if isinstance(data, list) else []

    async def get_company_profile(self, ticker: str) -> dict | None:
        """Full company profile (name, sector, description, logo, etc.)."""
        data = await self._request(
            "/profile",
            params={"symbol": ticker.upper()},
            cache_ttl=settings.CACHE_TTL_COMPANY_PROFILE,
            stable=True,
        )
        if isinstance(data, list) and data:
            return data[0]
        return None

    async def get_quote(self, ticker: str) -> dict | None:
        """Real-time/delayed stock quote."""
        data = await self._request(
            "/quote",
            params={"symbol": ticker.upper()},
            cache_ttl=settings.CACHE_TTL_STOCK_QUOTE,
            stable=True,
        )
        if isinstance(data, list) and data:
            return data[0]
        return None

    async def get_batch_quotes(self, tickers: list[str]) -> list[dict]:
        """Batch quote fetch for watchlist rendering."""
        symbols = ",".join(t.upper() for t in tickers)
        data = await self._request(
            "/quote",
            params={"symbol": symbols},
            cache_ttl=settings.CACHE_TTL_STOCK_QUOTE,
            stable=True,
        )
        return data if isinstance(data, list) else []

    async def get_historical_prices(
        self,
        ticker: str,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> list[dict]:
        """Daily OHLCV historical prices."""
        params: dict[str, Any] = {"symbol": ticker.upper()}
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        data = await self._request(
            "/historical-price-eod/full",
            params=params,
            cache_ttl=86400,  # 24 h
            stable=True,
        )
        return data if isinstance(data, list) else []

    # FMP free plan caps the `limit` parameter at 5 for financial statement endpoints.
    # Sending limit > 5 returns a premium error (not JSON), which results in an empty list.
    _FMP_FREE_LIMIT = 5

    async def get_income_statement(
        self, ticker: str, period: str = "annual", limit: int = 10
    ) -> list[dict]:
        """Income statement — uses FMP stable API (/stable/income-statement?symbol=)."""
        return await self._request(
            "/income-statement",
            params={"symbol": ticker.upper(), "period": period, "limit": min(limit, self._FMP_FREE_LIMIT)},
            cache_ttl=settings.CACHE_TTL_FINANCIAL_STATEMENTS,
            stable=True,
        ) or []

    async def get_balance_sheet(
        self, ticker: str, period: str = "annual", limit: int = 10
    ) -> list[dict]:
        """Balance sheet — uses FMP stable API (/stable/balance-sheet-statement?symbol=)."""
        return await self._request(
            "/balance-sheet-statement",
            params={"symbol": ticker.upper(), "period": period, "limit": min(limit, self._FMP_FREE_LIMIT)},
            cache_ttl=settings.CACHE_TTL_FINANCIAL_STATEMENTS,
            stable=True,
        ) or []

    async def get_cash_flow_statement(
        self, ticker: str, period: str = "annual", limit: int = 10
    ) -> list[dict]:
        """Cash flow statement — uses FMP stable API (/stable/cash-flow-statement?symbol=)."""
        return await self._request(
            "/cash-flow-statement",
            params={"symbol": ticker.upper(), "period": period, "limit": min(limit, self._FMP_FREE_LIMIT)},
            cache_ttl=settings.CACHE_TTL_FINANCIAL_STATEMENTS,
            stable=True,
        ) or []

    async def get_key_metrics(self, ticker: str, period: str = "annual") -> list[dict]:
        """Key financial metrics (PE, PB, EV/EBITDA, etc.)."""
        return await self._request(
            "/key-metrics",
            params={"symbol": ticker.upper(), "period": period},
            cache_ttl=settings.CACHE_TTL_ANALYTICS,
            stable=True,
        ) or []

    async def get_ratios(self, ticker: str, period: str = "annual") -> list[dict]:
        """Financial ratios (margins, ROE, ROA, etc.)."""
        return await self._request(
            "/ratios",
            params={"symbol": ticker.upper(), "period": period},
            cache_ttl=settings.CACHE_TTL_ANALYTICS,
            stable=True,
        ) or []


# Singleton instance — shared across the app lifecycle
fmp_client = FMPClient()
