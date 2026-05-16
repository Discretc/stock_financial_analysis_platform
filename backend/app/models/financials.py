"""
SQLAlchemy models — Income Statement, Balance Sheet, Cash Flow Statement.
Each row represents one reporting period (annual or quarterly).
Common-size percentages are stored alongside raw values for fast retrieval.
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
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pct() -> Mapped[float | None]:
    """Shorthand for a nullable percent column (stored as float, e.g. 45.32)."""
    return mapped_column(Float, nullable=True)  # type: ignore[return-value]


def _money() -> Mapped[float | None]:
    """Shorthand for a nullable large monetary value column."""
    return mapped_column(Numeric(24, 0), nullable=True)  # type: ignore[return-value]


class IncomeStatement(Base):
    __tablename__ = "income_statements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    period: Mapped[str] = mapped_column(String(10), nullable=False, index=True)  # "annual" | "quarterly" | "ttm"
    fiscal_year: Mapped[int | None] = mapped_column(nullable=True)
    fiscal_quarter: Mapped[int | None] = mapped_column(nullable=True)
    period_end_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    reported_currency: Mapped[str | None] = mapped_column(String(10))
    cik: Mapped[str | None] = mapped_column(String(20))
    filing_date: Mapped[date | None] = mapped_column(Date)

    # ---- Raw values (in reporting currency, absolute) -------------------
    revenue: Mapped[float | None] = _money()
    cost_of_revenue: Mapped[float | None] = _money()
    gross_profit: Mapped[float | None] = _money()

    research_and_development: Mapped[float | None] = _money()
    selling_general_administrative: Mapped[float | None] = _money()
    other_operating_expenses: Mapped[float | None] = _money()
    total_operating_expenses: Mapped[float | None] = _money()

    operating_income: Mapped[float | None] = _money()
    interest_income: Mapped[float | None] = _money()
    interest_expense: Mapped[float | None] = _money()
    total_other_income_expense: Mapped[float | None] = _money()
    ebitda: Mapped[float | None] = _money()
    depreciation_amortization: Mapped[float | None] = _money()

    income_before_tax: Mapped[float | None] = _money()
    income_tax_expense: Mapped[float | None] = _money()
    net_income: Mapped[float | None] = _money()
    net_income_attributable: Mapped[float | None] = _money()

    eps: Mapped[float | None] = mapped_column(Float)
    eps_diluted: Mapped[float | None] = mapped_column(Float)
    shares_outstanding: Mapped[float | None] = mapped_column(Numeric(20, 0))
    shares_diluted: Mapped[float | None] = mapped_column(Numeric(20, 0))

    # ---- Common-size % of Revenue ---------------------------------------
    cs_cost_of_revenue_pct: Mapped[float | None] = _pct()
    cs_gross_profit_pct: Mapped[float | None] = _pct()
    cs_rd_pct: Mapped[float | None] = _pct()
    cs_sga_pct: Mapped[float | None] = _pct()
    cs_total_opex_pct: Mapped[float | None] = _pct()
    cs_operating_income_pct: Mapped[float | None] = _pct()
    cs_ebitda_pct: Mapped[float | None] = _pct()
    cs_net_income_pct: Mapped[float | None] = _pct()

    # ---- YoY Growth % ---------------------------------------------------
    yoy_revenue_growth: Mapped[float | None] = _pct()
    yoy_gross_profit_growth: Mapped[float | None] = _pct()
    yoy_operating_income_growth: Mapped[float | None] = _pct()
    yoy_net_income_growth: Mapped[float | None] = _pct()
    yoy_eps_growth: Mapped[float | None] = _pct()

    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    company: Mapped["Company"] = relationship(back_populates="income_statements")  # type: ignore[name-defined]

    __table_args__ = (
        UniqueConstraint("company_id", "period", "period_end_date", name="uq_income_stmt_period"),
    )


class BalanceSheet(Base):
    __tablename__ = "balance_sheets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    period: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    fiscal_year: Mapped[int | None] = mapped_column(nullable=True)
    fiscal_quarter: Mapped[int | None] = mapped_column(nullable=True)
    period_end_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    reported_currency: Mapped[str | None] = mapped_column(String(10))

    # ---- Assets -----------------------------------------------------------
    cash_and_equivalents: Mapped[float | None] = _money()
    short_term_investments: Mapped[float | None] = _money()
    cash_and_short_term_investments: Mapped[float | None] = _money()
    net_receivables: Mapped[float | None] = _money()
    inventory: Mapped[float | None] = _money()
    other_current_assets: Mapped[float | None] = _money()
    total_current_assets: Mapped[float | None] = _money()

    property_plant_equipment_net: Mapped[float | None] = _money()
    goodwill: Mapped[float | None] = _money()
    intangible_assets: Mapped[float | None] = _money()
    long_term_investments: Mapped[float | None] = _money()
    other_non_current_assets: Mapped[float | None] = _money()
    total_non_current_assets: Mapped[float | None] = _money()

    total_assets: Mapped[float | None] = _money()

    # ---- Liabilities ------------------------------------------------------
    accounts_payable: Mapped[float | None] = _money()
    short_term_debt: Mapped[float | None] = _money()
    deferred_revenue: Mapped[float | None] = _money()
    other_current_liabilities: Mapped[float | None] = _money()
    total_current_liabilities: Mapped[float | None] = _money()

    long_term_debt: Mapped[float | None] = _money()
    deferred_tax_liabilities: Mapped[float | None] = _money()
    other_non_current_liabilities: Mapped[float | None] = _money()
    total_non_current_liabilities: Mapped[float | None] = _money()

    total_liabilities: Mapped[float | None] = _money()

    # ---- Equity -----------------------------------------------------------
    common_stock: Mapped[float | None] = _money()
    retained_earnings: Mapped[float | None] = _money()
    accumulated_other_comprehensive_income: Mapped[float | None] = _money()
    other_stockholder_equity: Mapped[float | None] = _money()
    total_stockholder_equity: Mapped[float | None] = _money()
    total_equity: Mapped[float | None] = _money()

    total_liabilities_and_equity: Mapped[float | None] = _money()
    minority_interest: Mapped[float | None] = _money()
    net_debt: Mapped[float | None] = _money()
    total_debt: Mapped[float | None] = _money()

    # ---- Common-size % of Total Assets ------------------------------------
    cs_cash_pct: Mapped[float | None] = _pct()
    cs_receivables_pct: Mapped[float | None] = _pct()
    cs_inventory_pct: Mapped[float | None] = _pct()
    cs_current_assets_pct: Mapped[float | None] = _pct()
    cs_ppe_pct: Mapped[float | None] = _pct()
    cs_goodwill_pct: Mapped[float | None] = _pct()
    cs_total_current_liabilities_pct: Mapped[float | None] = _pct()
    cs_total_debt_pct: Mapped[float | None] = _pct()
    cs_total_liabilities_pct: Mapped[float | None] = _pct()
    cs_equity_pct: Mapped[float | None] = _pct()

    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    company: Mapped["Company"] = relationship(back_populates="balance_sheets")  # type: ignore[name-defined]

    __table_args__ = (
        UniqueConstraint("company_id", "period", "period_end_date", name="uq_balance_sheet_period"),
    )


class CashFlowStatement(Base):
    __tablename__ = "cash_flow_statements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    period: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    fiscal_year: Mapped[int | None] = mapped_column(nullable=True)
    fiscal_quarter: Mapped[int | None] = mapped_column(nullable=True)
    period_end_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    reported_currency: Mapped[str | None] = mapped_column(String(10))

    # ---- Operating Activities ---------------------------------------------
    net_income: Mapped[float | None] = _money()
    depreciation_amortization: Mapped[float | None] = _money()
    stock_based_compensation: Mapped[float | None] = _money()
    deferred_income_tax: Mapped[float | None] = _money()
    change_in_working_capital: Mapped[float | None] = _money()
    accounts_receivable_changes: Mapped[float | None] = _money()
    inventory_changes: Mapped[float | None] = _money()
    accounts_payable_changes: Mapped[float | None] = _money()
    other_operating_activities: Mapped[float | None] = _money()
    net_cash_from_operating: Mapped[float | None] = _money()

    # ---- Investing Activities ---------------------------------------------
    capex: Mapped[float | None] = _money()
    acquisitions: Mapped[float | None] = _money()
    purchases_of_investments: Mapped[float | None] = _money()
    sales_of_investments: Mapped[float | None] = _money()
    other_investing_activities: Mapped[float | None] = _money()
    net_cash_from_investing: Mapped[float | None] = _money()

    # ---- Financing Activities ---------------------------------------------
    debt_repayment: Mapped[float | None] = _money()
    common_stock_issued: Mapped[float | None] = _money()
    common_stock_repurchased: Mapped[float | None] = _money()
    dividends_paid: Mapped[float | None] = _money()
    other_financing_activities: Mapped[float | None] = _money()
    net_cash_from_financing: Mapped[float | None] = _money()

    # ---- Summary ----------------------------------------------------------
    effect_of_exchange_rate: Mapped[float | None] = _money()
    net_change_in_cash: Mapped[float | None] = _money()
    cash_end_of_period: Mapped[float | None] = _money()
    cash_beginning_of_period: Mapped[float | None] = _money()
    free_cash_flow: Mapped[float | None] = _money()

    # ---- Common-size % of Operating Cash Flow ----------------------------
    cs_net_income_pct: Mapped[float | None] = _pct()
    cs_da_pct: Mapped[float | None] = _pct()
    cs_sbc_pct: Mapped[float | None] = _pct()
    cs_working_capital_pct: Mapped[float | None] = _pct()
    cs_capex_pct: Mapped[float | None] = _pct()
    cs_fcf_pct: Mapped[float | None] = _pct()
    cs_investing_pct: Mapped[float | None] = _pct()
    cs_financing_pct: Mapped[float | None] = _pct()

    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    company: Mapped["Company"] = relationship(back_populates="cash_flow_statements")  # type: ignore[name-defined]

    __table_args__ = (
        UniqueConstraint("company_id", "period", "period_end_date", name="uq_cashflow_period"),
    )
