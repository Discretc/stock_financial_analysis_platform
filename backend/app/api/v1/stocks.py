"""
Stocks API endpoints — search, profile, quote, historical prices.
"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ExternalAPIError, NotFoundError
from app.schemas.stock import (
    HistoricalPriceResponse,
    StockDetailResponse,
    StockSearchResponse,
    StockQuoteSchema,
    CompanyProfileSchema,
)
from app.services.fmp_service import fmp_client

router = APIRouter(prefix="/stocks", tags=["Stocks"])


@router.get(
    "/search",
    response_model=StockSearchResponse,
    summary="Search for stocks by ticker or company name",
)
async def search_stocks(
    q: str = Query(min_length=1, max_length=100, description="Search query"),
    limit: int = Query(default=20, ge=1, le=50),
):
    try:
        raw = await fmp_client.search(query=q, limit=limit)
    except ExternalAPIError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    results = [
        {
            "ticker": item.get("symbol", ""),
            "name": item.get("name", ""),
            "exchange": item.get("exchange"),
            "sector": None,
            "currency": item.get("currency"),
            "logo_url": None,
        }
        for item in raw
    ]
    return StockSearchResponse(query=q, results=results, total=len(results))


@router.get(
    "/{ticker}/profile",
    response_model=CompanyProfileSchema,
    summary="Get company profile",
)
async def get_company_profile(ticker: str):
    try:
        raw = await fmp_client.get_company_profile(ticker)
    except ExternalAPIError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    if raw is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Company not found: {ticker}")

    return CompanyProfileSchema(
        ticker=raw.get("symbol", ticker),
        company_name=raw.get("companyName", ""),
        exchange=raw.get("exchange"),
        sector=raw.get("sector"),
        industry=raw.get("industry"),
        country=raw.get("country"),
        currency=raw.get("currency"),
        website=raw.get("website"),
        logo_url=raw.get("image"),
        description=raw.get("description"),
        ceo=raw.get("ceo"),
        employees=raw.get("fullTimeEmployees"),
        ipo_date=raw.get("ipoDate"),
        market_cap=raw.get("marketCap"),
        price=raw.get("price"),
        beta=raw.get("beta"),
        is_etf=raw.get("isEtf", False),
        is_actively_trading=raw.get("isActivelyTrading", True),
    )


@router.get(
    "/{ticker}/quote",
    response_model=StockQuoteSchema,
    summary="Get real-time stock quote",
)
async def get_stock_quote(ticker: str):
    try:
        raw = await fmp_client.get_quote(ticker)
    except ExternalAPIError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    if raw is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Quote not found: {ticker}")

    return StockQuoteSchema(
        ticker=raw.get("symbol", ticker),
        price=raw.get("price"),
        change=raw.get("change"),
        change_percent=raw.get("changePercentage"),
        volume=raw.get("volume"),
        avg_volume=raw.get("avgVolume"),
        open=raw.get("open"),
        high=raw.get("dayHigh"),
        low=raw.get("dayLow"),
        previous_close=raw.get("previousClose"),
        high_52w=raw.get("yearHigh"),
        low_52w=raw.get("yearLow"),
        market_cap=raw.get("marketCap"),
        pe_ratio=raw.get("pe"),
        eps=raw.get("eps"),
        timestamp=raw.get("timestamp"),
        is_market_open=raw.get("isEarningAnnouncement", False),
    )


@router.get(
    "/{ticker}/historical",
    response_model=HistoricalPriceResponse,
    summary="Get historical daily OHLCV prices",
)
async def get_historical_prices(
    ticker: str,
    from_date: str | None = Query(default=None, description="YYYY-MM-DD"),
    to_date: str | None = Query(default=None, description="YYYY-MM-DD"),
):
    try:
        raw = await fmp_client.get_historical_prices(ticker, from_date=from_date, to_date=to_date)
    except ExternalAPIError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    data = [
        {
            "date": item.get("date"),
            "open": item.get("open"),
            "high": item.get("high"),
            "low": item.get("low"),
            "close": item.get("close"),
            "adj_close": item.get("adjClose"),
            "volume": item.get("volume"),
            "change": item.get("change"),
            "change_percent": item.get("changePercent"),
        }
        for item in raw
    ]
    return HistoricalPriceResponse(ticker=ticker.upper(), data=data)


@router.get(
    "/{ticker}",
    response_model=StockDetailResponse,
    summary="Get full stock detail (profile + quote)",
)
async def get_stock_detail(ticker: str):
    """Aggregated endpoint that fetches profile and live quote in parallel."""
    import asyncio

    try:
        profile_raw, quote_raw = await asyncio.gather(
            fmp_client.get_company_profile(ticker),
            fmp_client.get_quote(ticker),
            return_exceptions=True,
        )
    except ExternalAPIError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    if isinstance(profile_raw, Exception) or profile_raw is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Stock not found: {ticker}")

    # Build profile
    profile = CompanyProfileSchema(
        ticker=profile_raw.get("symbol", ticker),
        company_name=profile_raw.get("companyName", ""),
        exchange=profile_raw.get("exchange"),
        sector=profile_raw.get("sector"),
        industry=profile_raw.get("industry"),
        country=profile_raw.get("country"),
        currency=profile_raw.get("currency"),
        website=profile_raw.get("website"),
        logo_url=profile_raw.get("image"),
        description=profile_raw.get("description"),
        ceo=profile_raw.get("ceo"),
        employees=profile_raw.get("fullTimeEmployees"),
        ipo_date=profile_raw.get("ipoDate"),
        market_cap=profile_raw.get("marketCap"),
        price=profile_raw.get("price"),
        beta=profile_raw.get("beta"),
        is_etf=profile_raw.get("isEtf", False),
        is_actively_trading=profile_raw.get("isActivelyTrading", True),
    )

    # Build quote (may be unavailable)
    quote = None
    if quote_raw and not isinstance(quote_raw, Exception):
        quote = StockQuoteSchema(
            ticker=quote_raw.get("symbol", ticker),
            price=quote_raw.get("price"),
            change=quote_raw.get("change"),
            change_percent=quote_raw.get("changePercentage"),
            volume=quote_raw.get("volume"),
            avg_volume=quote_raw.get("avgVolume"),
            open=quote_raw.get("open"),
            high=quote_raw.get("dayHigh"),
            low=quote_raw.get("dayLow"),
            previous_close=quote_raw.get("previousClose"),
            high_52w=quote_raw.get("yearHigh"),
            low_52w=quote_raw.get("yearLow"),
            market_cap=quote_raw.get("marketCap"),
            pe_ratio=quote_raw.get("pe"),
            eps=quote_raw.get("eps"),
            timestamp=quote_raw.get("timestamp"),
            is_market_open=False,
        )

    return StockDetailResponse(profile=profile, quote=quote)
