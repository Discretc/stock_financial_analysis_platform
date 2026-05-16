"""
Pydantic schemas — Watchlists, Portfolios.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class WatchlistItemCreate(BaseModel):
    ticker: str = Field(max_length=20)
    exchange: str | None = Field(default=None, max_length=20)
    notes: str | None = None
    alert_price_above: float | None = None
    alert_price_below: float | None = None


class WatchlistCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None


class WatchlistItemSchema(BaseModel):
    id: UUID
    ticker: str
    exchange: str | None
    notes: str | None
    alert_price_above: float | None
    alert_price_below: float | None
    added_at: datetime

    model_config = {"from_attributes": True}


class WatchlistSchema(BaseModel):
    id: UUID
    name: str
    description: str | None
    is_default: bool
    created_at: datetime
    items: list[WatchlistItemSchema] = []

    model_config = {"from_attributes": True}


class PortfolioHoldingCreate(BaseModel):
    ticker: str = Field(max_length=20)
    shares: float = Field(gt=0)
    average_cost: float = Field(gt=0)
    currency: str = Field(default="USD", max_length=3)
    notes: str | None = None


class PortfolioCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    currency: str = Field(default="USD", max_length=3)


class PortfolioHoldingSchema(BaseModel):
    id: UUID
    ticker: str
    shares: float
    average_cost: float
    currency: str

    model_config = {"from_attributes": True}


class PortfolioSchema(BaseModel):
    id: UUID
    name: str
    description: str | None
    currency: str
    is_public: bool
    created_at: datetime
    holdings: list[PortfolioHoldingSchema] = []

    model_config = {"from_attributes": True}
