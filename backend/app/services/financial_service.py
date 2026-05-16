"""
Financial data service — orchestrates FMP fetching, normalisation,
common-size computation, YoY growth, and persistence.
"""

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.common_size import (
    compute_balance_sheet_common_size,
    compute_cash_flow_common_size,
    compute_income_statement_common_size,
    compute_income_statement_yoy,
)
from app.core.logging import get_logger
from app.models.company import Company
from app.models.financials import BalanceSheet, CashFlowStatement, IncomeStatement
from app.services.fmp_service import fmp_client

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# FMP → ORM field name mapping helpers
# ---------------------------------------------------------------------------

def _normalize_income_statement(raw: dict) -> dict:
    """Map FMP income statement keys to our ORM field names."""
    return {
        "revenue":                      raw.get("revenue"),
        "cost_of_revenue":              raw.get("costOfRevenue"),
        "gross_profit":                 raw.get("grossProfit"),
        "research_and_development":     raw.get("researchAndDevelopmentExpenses"),
        "selling_general_administrative": raw.get("sellingGeneralAndAdministrativeExpenses"),
        "other_operating_expenses":     raw.get("otherExpenses"),
        "total_operating_expenses":     raw.get("operatingExpenses"),
        "operating_income":             raw.get("operatingIncome"),
        "interest_income":              raw.get("interestIncome"),
        "interest_expense":             raw.get("interestExpense"),
        "total_other_income_expense":   raw.get("totalOtherIncomeExpensesNet"),
        "ebitda":                       raw.get("ebitda"),
        "depreciation_amortization":    raw.get("depreciationAndAmortization"),
        "income_before_tax":            raw.get("incomeBeforeTax"),
        "income_tax_expense":           raw.get("incomeTaxExpense"),
        "net_income":                   raw.get("netIncome"),
        "net_income_attributable":      raw.get("netIncomeDeductingPortionAttributableToNoncontrollingInterest"),
        "eps":                          raw.get("eps"),
        "eps_diluted":                  raw.get("epsdiluted"),
        "shares_outstanding":           raw.get("weightedAverageShsOut"),
        "shares_diluted":               raw.get("weightedAverageShsOutDil"),
        "period_end_date":              _parse_date(raw.get("date")),
        "fiscal_year":                  raw.get("calendarYear"),
        "fiscal_quarter":               _parse_quarter(raw.get("period")),
        "reported_currency":            raw.get("reportedCurrency"),
        "cik":                          raw.get("cik"),
        "filing_date":                  _parse_date(raw.get("fillingDate")),
    }


def _normalize_balance_sheet(raw: dict) -> dict:
    return {
        "cash_and_equivalents":             raw.get("cashAndCashEquivalents"),
        "short_term_investments":           raw.get("shortTermInvestments"),
        "cash_and_short_term_investments":  raw.get("cashAndShortTermInvestments"),
        "net_receivables":                  raw.get("netReceivables"),
        "inventory":                        raw.get("inventory"),
        "other_current_assets":             raw.get("otherCurrentAssets"),
        "total_current_assets":             raw.get("totalCurrentAssets"),
        "property_plant_equipment_net":     raw.get("propertyPlantEquipmentNet"),
        "goodwill":                         raw.get("goodwill"),
        "intangible_assets":                raw.get("intangibleAssets"),
        "long_term_investments":            raw.get("longTermInvestments"),
        "other_non_current_assets":         raw.get("otherNonCurrentAssets"),
        "total_non_current_assets":         raw.get("totalNonCurrentAssets"),
        "total_assets":                     raw.get("totalAssets"),
        "accounts_payable":                 raw.get("accountPayables"),
        "short_term_debt":                  raw.get("shortTermDebt"),
        "deferred_revenue":                 raw.get("deferredRevenue"),
        "other_current_liabilities":        raw.get("otherCurrentLiabilities"),
        "total_current_liabilities":        raw.get("totalCurrentLiabilities"),
        "long_term_debt":                   raw.get("longTermDebt"),
        "deferred_tax_liabilities":         raw.get("deferredTaxLiabilitiesNonCurrent"),
        "other_non_current_liabilities":    raw.get("otherNonCurrentLiabilities"),
        "total_non_current_liabilities":    raw.get("totalNonCurrentLiabilities"),
        "total_liabilities":                raw.get("totalLiabilities"),
        "common_stock":                     raw.get("commonStock"),
        "retained_earnings":                raw.get("retainedEarnings"),
        "accumulated_other_comprehensive_income": raw.get("accumulatedOtherComprehensiveIncomeLoss"),
        "other_stockholder_equity":         raw.get("othertotalStockholdersEquity"),
        "total_stockholder_equity":         raw.get("totalStockholdersEquity"),
        "total_equity":                     raw.get("totalEquity"),
        "total_liabilities_and_equity":     raw.get("totalLiabilitiesAndStockholdersEquity"),
        "minority_interest":                raw.get("minorityInterest"),
        "net_debt":                         raw.get("netDebt"),
        "total_debt":                       raw.get("totalDebt"),
        "period_end_date":                  _parse_date(raw.get("date")),
        "fiscal_year":                      raw.get("calendarYear"),
        "fiscal_quarter":                   _parse_quarter(raw.get("period")),
        "reported_currency":                raw.get("reportedCurrency"),
    }


def _normalize_cash_flow(raw: dict) -> dict:
    return {
        "net_income":                   raw.get("netIncome"),
        "depreciation_amortization":    raw.get("depreciationAndAmortization"),
        "stock_based_compensation":     raw.get("stockBasedCompensation"),
        "deferred_income_tax":          raw.get("deferredIncomeTax"),
        "change_in_working_capital":    raw.get("changeInWorkingCapital"),
        "accounts_receivable_changes":  raw.get("accountsReceivables"),
        "inventory_changes":            raw.get("inventory"),
        "accounts_payable_changes":     raw.get("accountsPayables"),
        "other_operating_activities":   raw.get("otherWorkingCapital"),
        "net_cash_from_operating":      raw.get("netCashProvidedByOperatingActivities"),
        "capex":                        raw.get("capitalExpenditure"),
        "acquisitions":                 raw.get("acquisitionsNet"),
        "purchases_of_investments":     raw.get("purchasesOfInvestments"),
        "sales_of_investments":         raw.get("salesMaturitiesOfInvestments"),
        "other_investing_activities":   raw.get("otherInvestingActivites"),
        "net_cash_from_investing":      raw.get("netCashUsedForInvestingActivites"),
        "debt_repayment":               raw.get("debtRepayment"),
        "common_stock_issued":          raw.get("commonStockIssued"),
        "common_stock_repurchased":     raw.get("commonStockRepurchased"),
        "dividends_paid":               raw.get("dividendsPaid"),
        "other_financing_activities":   raw.get("otherFinancingActivites"),
        "net_cash_from_financing":      raw.get("netCashUsedProvidedByFinancingActivities"),
        "effect_of_exchange_rate":      raw.get("effectOfForexChangesOnCash"),
        "net_change_in_cash":           raw.get("netChangeInCash"),
        "cash_end_of_period":           raw.get("cashAtEndOfPeriod"),
        "cash_beginning_of_period":     raw.get("cashAtBeginningOfPeriod"),
        "free_cash_flow":               raw.get("freeCashFlow"),
        "period_end_date":              _parse_date(raw.get("date")),
        "fiscal_year":                  raw.get("calendarYear"),
        "fiscal_quarter":               _parse_quarter(raw.get("period")),
        "reported_currency":            raw.get("reportedCurrency"),
    }


def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def _parse_quarter(period_str: str | None) -> int | None:
    """Convert 'Q1'/'Q2'/'Q3'/'Q4' → 1/2/3/4. Returns None for annual."""
    if period_str and period_str.startswith("Q"):
        try:
            return int(period_str[1])
        except ValueError:
            pass
    return None


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------

class FinancialService:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def _get_or_create_company(self, ticker: str) -> Company:
        result = await self._db.execute(select(Company).where(Company.ticker == ticker.upper()))
        company = result.scalar_one_or_none()
        if company is None:
            company = Company(ticker=ticker.upper(), company_name=ticker.upper())
            self._db.add(company)
            await self._db.flush()  # Generates the UUID without committing
        return company

    async def fetch_and_store_income_statements(
        self, ticker: str, period: str = "annual", limit: int = 10
    ) -> list[IncomeStatement]:
        raw_list = await fmp_client.get_income_statement(ticker, period=period, limit=limit)
        if not raw_list:
            return []

        company = await self._get_or_create_company(ticker)
        results: list[IncomeStatement] = []

        for i, raw in enumerate(raw_list):
            normalized = _normalize_income_statement(raw)

            # Common-size percentages
            cs = compute_income_statement_common_size(normalized)
            normalized.update(cs)

            # YoY growth (compare to prior year, index i+1)
            if i + 1 < len(raw_list):
                prior_normalized = _normalize_income_statement(raw_list[i + 1])
                yoy = compute_income_statement_yoy(normalized, prior_normalized)
                normalized.update(yoy)

            # Upsert pattern: find existing record or create new
            period_end = normalized.get("period_end_date")
            stmt_q = select(IncomeStatement).where(
                IncomeStatement.company_id == company.id,
                IncomeStatement.period == period,
                IncomeStatement.period_end_date == period_end,
            )
            existing = (await self._db.execute(stmt_q)).scalar_one_or_none()

            if existing:
                for k, v in normalized.items():
                    if hasattr(existing, k):
                        setattr(existing, k, v)
                results.append(existing)
            else:
                record = IncomeStatement(
                    company_id=company.id,
                    ticker=ticker.upper(),
                    period=period,
                    **{k: v for k, v in normalized.items() if hasattr(IncomeStatement, k)},
                )
                self._db.add(record)
                results.append(record)

        return results

    async def fetch_and_store_balance_sheets(
        self, ticker: str, period: str = "annual", limit: int = 10
    ) -> list[BalanceSheet]:
        raw_list = await fmp_client.get_balance_sheet(ticker, period=period, limit=limit)
        if not raw_list:
            return []
        company = await self._get_or_create_company(ticker)
        results: list[BalanceSheet] = []
        for raw in raw_list:
            normalized = _normalize_balance_sheet(raw)
            cs = compute_balance_sheet_common_size(normalized)
            normalized.update(cs)
            period_end = normalized.get("period_end_date")
            stmt_q = select(BalanceSheet).where(
                BalanceSheet.company_id == company.id,
                BalanceSheet.period == period,
                BalanceSheet.period_end_date == period_end,
            )
            existing = (await self._db.execute(stmt_q)).scalar_one_or_none()
            if existing:
                for k, v in normalized.items():
                    if hasattr(existing, k):
                        setattr(existing, k, v)
                results.append(existing)
            else:
                record = BalanceSheet(
                    company_id=company.id,
                    ticker=ticker.upper(),
                    period=period,
                    **{k: v for k, v in normalized.items() if hasattr(BalanceSheet, k)},
                )
                self._db.add(record)
                results.append(record)
        return results

    async def fetch_and_store_cash_flows(
        self, ticker: str, period: str = "annual", limit: int = 10
    ) -> list[CashFlowStatement]:
        raw_list = await fmp_client.get_cash_flow_statement(ticker, period=period, limit=limit)
        if not raw_list:
            return []
        company = await self._get_or_create_company(ticker)
        results: list[CashFlowStatement] = []
        for raw in raw_list:
            normalized = _normalize_cash_flow(raw)
            cs = compute_cash_flow_common_size(normalized)
            normalized.update(cs)
            period_end = normalized.get("period_end_date")
            stmt_q = select(CashFlowStatement).where(
                CashFlowStatement.company_id == company.id,
                CashFlowStatement.period == period,
                CashFlowStatement.period_end_date == period_end,
            )
            existing = (await self._db.execute(stmt_q)).scalar_one_or_none()
            if existing:
                for k, v in normalized.items():
                    if hasattr(existing, k):
                        setattr(existing, k, v)
                results.append(existing)
            else:
                record = CashFlowStatement(
                    company_id=company.id,
                    ticker=ticker.upper(),
                    period=period,
                    **{k: v for k, v in normalized.items() if hasattr(CashFlowStatement, k)},
                )
                self._db.add(record)
                results.append(record)
        return results

    async def get_income_statements(
        self, ticker: str, period: str = "annual", limit: int = 10
    ) -> list[IncomeStatement]:
        result = await self._db.execute(
            select(IncomeStatement)
            .where(IncomeStatement.ticker == ticker.upper(), IncomeStatement.period == period)
            .order_by(IncomeStatement.period_end_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_balance_sheets(
        self, ticker: str, period: str = "annual", limit: int = 10
    ) -> list[BalanceSheet]:
        result = await self._db.execute(
            select(BalanceSheet)
            .where(BalanceSheet.ticker == ticker.upper(), BalanceSheet.period == period)
            .order_by(BalanceSheet.period_end_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_cash_flow_statements(
        self, ticker: str, period: str = "annual", limit: int = 10
    ) -> list[CashFlowStatement]:
        result = await self._db.execute(
            select(CashFlowStatement)
            .where(CashFlowStatement.ticker == ticker.upper(), CashFlowStatement.period == period)
            .order_by(CashFlowStatement.period_end_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
