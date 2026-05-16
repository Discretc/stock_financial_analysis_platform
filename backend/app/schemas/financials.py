"""
Pydantic v2 schemas — Financial Statements with common-size percentages.
"""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Base for all statement line items
# ---------------------------------------------------------------------------

class BaseFinancialPeriod(BaseModel):
    id: UUID
    ticker: str
    period: str       # "annual" | "quarterly" | "ttm"
    fiscal_year: int | None
    fiscal_quarter: int | None
    period_end_date: date
    currency: str | None = Field(None, validation_alias="reported_currency")

    model_config = {"from_attributes": True, "populate_by_name": True}


# ---------------------------------------------------------------------------
# Income Statement
# ---------------------------------------------------------------------------

class IncomeStatementSchema(BaseFinancialPeriod):
    # Raw values
    revenue: float | None
    cost_of_revenue: float | None
    gross_profit: float | None
    research_and_development: float | None
    selling_general_and_admin: float | None = Field(None, validation_alias="selling_general_administrative")
    other_operating_expenses: float | None
    total_operating_expenses: float | None
    operating_income: float | None
    interest_income: float | None
    interest_expense: float | None
    total_other_income_expense: float | None
    ebitda: float | None
    depreciation_amortization: float | None
    income_before_tax: float | None
    income_tax_expense: float | None
    net_income: float | None
    net_income_attributable: float | None
    eps_basic: float | None = Field(None, validation_alias="eps")
    eps_diluted: float | None
    shares_outstanding_basic: float | None = Field(None, validation_alias="shares_outstanding")
    shares_outstanding_diluted: float | None = Field(None, validation_alias="shares_diluted")

    # Common-size % of Revenue
    cs_cost_of_revenue_pct: float | None
    cs_gross_profit_pct: float | None
    cs_rd_pct: float | None
    cs_sga_pct: float | None
    cs_total_opex_pct: float | None
    cs_operating_income_pct: float | None
    cs_ebitda_pct: float | None
    cs_net_income_pct: float | None

    # YoY Growth
    yoy_revenue_growth: float | None
    yoy_gross_profit_growth: float | None
    yoy_operating_income_growth: float | None
    yoy_net_income_growth: float | None
    yoy_eps_diluted_growth: float | None = Field(None, validation_alias="yoy_eps_growth")


class IncomeStatementResponse(BaseModel):
    ticker: str
    period: str
    statements: list[IncomeStatementSchema]


# ---------------------------------------------------------------------------
# Balance Sheet
# ---------------------------------------------------------------------------

class BalanceSheetSchema(BaseFinancialPeriod):
    # Assets
    cash_and_equivalents: float | None
    short_term_investments: float | None
    cash_and_short_term_investments: float | None
    net_receivables: float | None
    inventory: float | None
    other_current_assets: float | None
    total_current_assets: float | None
    property_plant_equipment_net: float | None
    goodwill: float | None
    intangible_assets: float | None
    long_term_investments: float | None
    other_non_current_assets: float | None
    total_non_current_assets: float | None
    total_assets: float | None

    # Liabilities
    accounts_payable: float | None
    short_term_debt: float | None
    deferred_revenue: float | None
    other_current_liabilities: float | None
    total_current_liabilities: float | None
    long_term_debt: float | None
    deferred_tax_liabilities: float | None
    other_non_current_liabilities: float | None
    total_non_current_liabilities: float | None
    total_liabilities: float | None

    # Equity
    common_stock: float | None
    retained_earnings: float | None
    total_stockholders_equity: float | None = Field(None, validation_alias="total_stockholder_equity")
    total_equity: float | None
    total_liabilities_and_equity: float | None
    net_debt: float | None
    total_debt: float | None

    # Common-size % of Total Assets
    cs_cash_pct: float | None
    cs_receivables_pct: float | None
    cs_inventory_pct: float | None
    cs_current_assets_pct: float | None
    cs_ppe_pct: float | None
    cs_goodwill_pct: float | None
    cs_total_current_liabilities_pct: float | None
    cs_total_debt_pct: float | None
    cs_total_liabilities_pct: float | None
    cs_equity_pct: float | None


class BalanceSheetResponse(BaseModel):
    ticker: str
    period: str
    statements: list[BalanceSheetSchema]


# ---------------------------------------------------------------------------
# Cash Flow Statement
# ---------------------------------------------------------------------------

class CashFlowStatementSchema(BaseFinancialPeriod):
    # Operating
    net_income: float | None
    depreciation_and_amortization: float | None = Field(None, validation_alias="depreciation_amortization")
    stock_based_compensation: float | None
    deferred_income_tax: float | None
    change_in_working_capital: float | None
    accounts_receivable_changes: float | None
    inventory_changes: float | None
    accounts_payable_changes: float | None
    other_operating_activities: float | None
    net_cash_from_operating: float | None

    # Investing
    capital_expenditures: float | None = Field(None, validation_alias="capex")
    acquisitions: float | None
    purchases_of_investments: float | None
    sales_of_investments: float | None
    other_investing_activities: float | None
    net_cash_from_investing: float | None

    # Financing
    net_borrowings: float | None = Field(None, validation_alias="debt_repayment")
    common_stock_issued: float | None
    stock_repurchases: float | None = Field(None, validation_alias="common_stock_repurchased")
    dividends_paid: float | None
    other_financing_activities: float | None
    net_cash_from_financing: float | None

    # Summary
    free_cash_flow: float | None
    net_change_in_cash: float | None

    # Common-size % of OCF
    cs_net_income_pct: float | None
    cs_da_pct: float | None
    cs_sbc_pct: float | None
    cs_working_capital_pct: float | None
    cs_capex_pct: float | None
    cs_fcf_pct: float | None
    cs_investing_pct: float | None
    cs_financing_pct: float | None


class CashFlowStatementResponse(BaseModel):
    ticker: str
    period: str
    statements: list[CashFlowStatementSchema]


# ---------------------------------------------------------------------------
# Financial Ratios
# ---------------------------------------------------------------------------

class FinancialRatiosSchema(BaseModel):
    ticker: str
    period: str
    period_end_date: date

    # Profitability
    gross_margin: float | None
    operating_margin: float | None
    ebitda_margin: float | None
    net_margin: float | None
    roa: float | None
    roe: float | None
    roic: float | None

    # Valuation
    pe_ratio: float | None
    pb_ratio: float | None
    ps_ratio: float | None
    peg_ratio: float | None
    ev_ebitda: float | None
    fcf_yield: float | None

    # Liquidity
    current_ratio: float | None
    quick_ratio: float | None
    cash_ratio: float | None

    # Leverage
    debt_to_equity: float | None
    debt_to_assets: float | None
    interest_coverage: float | None
    net_debt_to_ebitda: float | None

    # Cash Flow
    fcf_per_share: float | None
    ocf_conversion: float | None
    capex_intensity: float | None

    model_config = {"from_attributes": True}
