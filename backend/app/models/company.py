"""
SQLAlchemy models — Company profiles and real-time / historical stock quotes.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Company(Base):
    """
    Master company/security record.
    Populated and refreshed via FMP /profile endpoint.
    """

    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    exchange: Mapped[str | None] = mapped_column(String(30), index=True)
    exchange_short: Mapped[str | None] = mapped_column(String(20))
    company_name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    sector: Mapped[str | None] = mapped_column(String(100), index=True)
    industry: Mapped[str | None] = mapped_column(String(200), index=True)
    country: Mapped[str | None] = mapped_column(String(100), index=True)
    currency: Mapped[str | None] = mapped_column(String(10))
    website: Mapped[str | None] = mapped_column(String(500))
    logo_url: Mapped[str | None] = mapped_column(String(500))
    ceo: Mapped[str | None] = mapped_column(String(200))
    employees: Mapped[int | None] = mapped_column(BigInteger)
    ipo_date: Mapped[date | None] = mapped_column(Date)
    is_etf: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_actively_trading: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    market_cap: Mapped[float | None] = mapped_column(Numeric(24, 2))
    price: Mapped[float | None] = mapped_column(Numeric(18, 4))
    beta: Mapped[float | None] = mapped_column(Float)
    vol_avg: Mapped[float | None] = mapped_column(BigInteger)
    last_dividend: Mapped[float | None] = mapped_column(Numeric(10, 4))

    data_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    income_statements: Mapped[list["IncomeStatement"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="company", cascade="all, delete-orphan"
    )
    balance_sheets: Mapped[list["BalanceSheet"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="company", cascade="all, delete-orphan"
    )
    cash_flow_statements: Mapped[list["CashFlowStatement"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="company", cascade="all, delete-orphan"
    )
    historical_prices: Mapped[list["HistoricalPrice"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )


class StockQuote(Base):
    """
    Latest real-time/delayed quote snapshot for a ticker.
    One row per ticker; overwritten on each refresh.
    """

    __tablename__ = "stock_quotes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    price: Mapped[float | None] = mapped_column(Numeric(18, 4))
    change: Mapped[float | None] = mapped_column(Numeric(18, 4))
    change_percent: Mapped[float | None] = mapped_column(Float)
    volume: Mapped[int | None] = mapped_column(BigInteger)
    avg_volume: Mapped[int | None] = mapped_column(BigInteger)
    open: Mapped[float | None] = mapped_column(Numeric(18, 4))
    high: Mapped[float | None] = mapped_column(Numeric(18, 4))
    low: Mapped[float | None] = mapped_column(Numeric(18, 4))
    previous_close: Mapped[float | None] = mapped_column(Numeric(18, 4))
    year_high: Mapped[float | None] = mapped_column(Numeric(18, 4))
    year_low: Mapped[float | None] = mapped_column(Numeric(18, 4))
    market_cap: Mapped[float | None] = mapped_column(Numeric(24, 2))
    pe_ratio: Mapped[float | None] = mapped_column(Float)
    eps: Mapped[float | None] = mapped_column(Float)
    timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_market_open: Mapped[bool] = mapped_column(Boolean, default=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class HistoricalPrice(Base):
    """
    Daily OHLCV historical prices.
    Indexed on (company_id, date) for fast range queries.
    """

    __tablename__ = "historical_prices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    open: Mapped[float | None] = mapped_column(Numeric(18, 4))
    high: Mapped[float | None] = mapped_column(Numeric(18, 4))
    low: Mapped[float | None] = mapped_column(Numeric(18, 4))
    close: Mapped[float | None] = mapped_column(Numeric(18, 4))
    adj_close: Mapped[float | None] = mapped_column(Numeric(18, 4))
    volume: Mapped[int | None] = mapped_column(BigInteger)
    vwap: Mapped[float | None] = mapped_column(Numeric(18, 4))
    change: Mapped[float | None] = mapped_column(Numeric(18, 4))
    change_percent: Mapped[float | None] = mapped_column(Float)

    company: Mapped["Company"] = relationship(back_populates="historical_prices")

    __table_args__ = (
        UniqueConstraint("company_id", "date", name="uq_historical_price_company_date"),
    )
