"""
SQLAlchemy models — precomputed financial ratios and audit/API logs.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FinancialRatios(Base):
    """
    Precomputed financial ratios per reporting period.
    Stored to avoid recalculating on every request.
    """

    __tablename__ = "financial_ratios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    period: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    period_end_date: Mapped[date] = mapped_column(Date, nullable=False)

    # ---- Profitability ---------------------------------------------------
    gross_margin: Mapped[float | None] = mapped_column(Float)
    operating_margin: Mapped[float | None] = mapped_column(Float)
    ebitda_margin: Mapped[float | None] = mapped_column(Float)
    net_margin: Mapped[float | None] = mapped_column(Float)
    roa: Mapped[float | None] = mapped_column(Float)
    roe: Mapped[float | None] = mapped_column(Float)
    roic: Mapped[float | None] = mapped_column(Float)

    # ---- Valuation -------------------------------------------------------
    pe_ratio: Mapped[float | None] = mapped_column(Float)
    pb_ratio: Mapped[float | None] = mapped_column(Float)
    ps_ratio: Mapped[float | None] = mapped_column(Float)
    peg_ratio: Mapped[float | None] = mapped_column(Float)
    ev_ebitda: Mapped[float | None] = mapped_column(Float)
    fcf_yield: Mapped[float | None] = mapped_column(Float)

    # ---- Liquidity -------------------------------------------------------
    current_ratio: Mapped[float | None] = mapped_column(Float)
    quick_ratio: Mapped[float | None] = mapped_column(Float)
    cash_ratio: Mapped[float | None] = mapped_column(Float)

    # ---- Leverage --------------------------------------------------------
    debt_to_equity: Mapped[float | None] = mapped_column(Float)
    debt_to_assets: Mapped[float | None] = mapped_column(Float)
    interest_coverage: Mapped[float | None] = mapped_column(Float)
    net_debt_to_ebitda: Mapped[float | None] = mapped_column(Float)

    # ---- Cash Flow -------------------------------------------------------
    fcf_per_share: Mapped[float | None] = mapped_column(Float)
    ocf_conversion: Mapped[float | None] = mapped_column(Float)  # OCF / Net Income
    capex_intensity: Mapped[float | None] = mapped_column(Float)  # CapEx / Revenue

    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("company_id", "period", "period_end_date", name="uq_ratios_period"),
    )


class AuditLog(Base):
    """
    Immutable audit trail for security-sensitive events.
    Never updated — only inserted.
    """

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str | None] = mapped_column(String(100))
    resource_id: Mapped[str | None] = mapped_column(String(100))
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    detail: Mapped[str | None] = mapped_column(Text)  # JSON-encoded extra data
    success: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )


class APILog(Base):
    """
    Logs of upstream FMP API calls for monitoring and rate-limit tracking.
    """

    __tablename__ = "api_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="fmp")
    endpoint: Mapped[str] = mapped_column(String(500), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False, default="GET")
    status_code: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    cached: Mapped[bool] = mapped_column(nullable=False, default=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
