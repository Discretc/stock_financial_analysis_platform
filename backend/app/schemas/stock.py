"""
Pydantic v2 schemas — Stocks, Quotes, Historical Prices, Company Profiles.
"""

from datetime import date, datetime

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Company Profile
# ---------------------------------------------------------------------------

class CompanyProfileSchema(BaseModel):
    ticker: str
    company_name: str
    exchange: str | None
    sector: str | None
    industry: str | None
    country: str | None
    currency: str | None
    website: str | None
    logo_url: str | None
    description: str | None
    ceo: str | None
    employees: int | None
    ipo_date: date | None
    market_cap: float | None
    price: float | None
    beta: float | None
    is_etf: bool
    is_actively_trading: bool

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Stock Quote
# ---------------------------------------------------------------------------

class StockQuoteSchema(BaseModel):
    ticker: str
    price: float | None
    change: float | None
    change_percent: float | None
    volume: int | None
    avg_volume: int | None
    open: float | None
    high: float | None
    low: float | None
    previous_close: float | None
    high_52w: float | None
    low_52w: float | None
    market_cap: float | None
    pe_ratio: float | None
    eps: float | None
    timestamp: datetime | None
    is_market_open: bool

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Historical Price
# ---------------------------------------------------------------------------

class HistoricalPriceSchema(BaseModel):
    date: date
    open: float | None
    high: float | None
    low: float | None
    close: float | None
    adj_close: float | None
    volume: int | None
    change: float | None
    change_percent: float | None

    model_config = {"from_attributes": True}


class HistoricalPriceResponse(BaseModel):
    ticker: str
    data: list[HistoricalPriceSchema]


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

class StockSearchResult(BaseModel):
    ticker: str
    name: str
    exchange: str | None
    sector: str | None
    currency: str | None
    logo_url: str | None


class StockSearchResponse(BaseModel):
    query: str
    results: list[StockSearchResult]
    total: int


# ---------------------------------------------------------------------------
# Stock Detail (aggregated)
# ---------------------------------------------------------------------------

class StockDetailResponse(BaseModel):
    profile: CompanyProfileSchema
    quote: StockQuoteSchema | None


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------

class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
