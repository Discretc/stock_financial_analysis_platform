"""
Common-size financial statement calculation engine.

This module implements the structural percentage analysis used by institutional
financial terminals (Bloomberg, FactSet, etc.).

Design:
  - All calculations are pure functions — no I/O, no side effects.
  - Division is always guarded against zero/None denominators.
  - Percentages are stored as floats (e.g. 45.32 means 45.32%).
  - Negative values are handled correctly (negative margins are valid).
"""

from typing import Any


def _pct(numerator: float | None, denominator: float | None) -> float | None:
    """
    Safe percentage: numerator / denominator × 100.
    Returns None if either value is None or denominator is zero.
    """
    if numerator is None or denominator is None or denominator == 0:
        return None
    return round(numerator / denominator * 100, 4)


# ---------------------------------------------------------------------------
# Income Statement Common-Size (% of Revenue)
# ---------------------------------------------------------------------------

def compute_income_statement_common_size(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Given a normalised income statement dict (keys match ORM field names),
    compute all common-size percentages as % of revenue.

    Returns a new dict with the cs_* keys populated.
    """
    revenue = raw.get("revenue")

    return {
        "cs_cost_of_revenue_pct":   _pct(raw.get("cost_of_revenue"), revenue),
        "cs_gross_profit_pct":      _pct(raw.get("gross_profit"), revenue),
        "cs_rd_pct":                _pct(raw.get("research_and_development"), revenue),
        "cs_sga_pct":               _pct(raw.get("selling_general_administrative"), revenue),
        "cs_total_opex_pct":        _pct(raw.get("total_operating_expenses"), revenue),
        "cs_operating_income_pct":  _pct(raw.get("operating_income"), revenue),
        "cs_ebitda_pct":            _pct(raw.get("ebitda"), revenue),
        "cs_net_income_pct":        _pct(raw.get("net_income"), revenue),
    }


# ---------------------------------------------------------------------------
# Balance Sheet Common-Size (% of Total Assets)
# ---------------------------------------------------------------------------

def compute_balance_sheet_common_size(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Compute common-size percentages as % of total_assets.
    """
    total_assets = raw.get("total_assets")

    return {
        "cs_cash_pct":                       _pct(raw.get("cash_and_short_term_investments"), total_assets),
        "cs_receivables_pct":                _pct(raw.get("net_receivables"), total_assets),
        "cs_inventory_pct":                  _pct(raw.get("inventory"), total_assets),
        "cs_current_assets_pct":             _pct(raw.get("total_current_assets"), total_assets),
        "cs_ppe_pct":                        _pct(raw.get("property_plant_equipment_net"), total_assets),
        "cs_goodwill_pct":                   _pct(raw.get("goodwill"), total_assets),
        "cs_total_current_liabilities_pct":  _pct(raw.get("total_current_liabilities"), total_assets),
        "cs_total_debt_pct":                 _pct(raw.get("total_debt"), total_assets),
        "cs_total_liabilities_pct":          _pct(raw.get("total_liabilities"), total_assets),
        "cs_equity_pct":                     _pct(raw.get("total_equity"), total_assets),
    }


# ---------------------------------------------------------------------------
# Cash Flow Common-Size (% of Operating Cash Flow)
# ---------------------------------------------------------------------------

def compute_cash_flow_common_size(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Compute common-size percentages as % of net_cash_from_operating (OCF).
    Note: OCF can be negative; percentages are still meaningful.
    """
    ocf = raw.get("net_cash_from_operating")

    return {
        "cs_net_income_pct":       _pct(raw.get("net_income"), ocf),
        "cs_da_pct":               _pct(raw.get("depreciation_amortization"), ocf),
        "cs_sbc_pct":              _pct(raw.get("stock_based_compensation"), ocf),
        "cs_working_capital_pct":  _pct(raw.get("change_in_working_capital"), ocf),
        "cs_capex_pct":            _pct(raw.get("capex"), ocf),
        "cs_fcf_pct":              _pct(raw.get("free_cash_flow"), ocf),
        "cs_investing_pct":        _pct(raw.get("net_cash_from_investing"), ocf),
        "cs_financing_pct":        _pct(raw.get("net_cash_from_financing"), ocf),
    }


# ---------------------------------------------------------------------------
# Year-over-Year Growth
# ---------------------------------------------------------------------------

def compute_yoy_growth(
    current: float | None, prior: float | None
) -> float | None:
    """
    YoY growth rate: (current - prior) / |prior| × 100.
    Uses absolute value of prior to handle sign changes correctly
    (e.g. moving from a loss to a profit).
    Returns None if either value is missing or prior is zero.
    """
    if current is None or prior is None or prior == 0:
        return None
    return round((current - prior) / abs(prior) * 100, 4)


def compute_income_statement_yoy(
    current: dict[str, Any],
    prior: dict[str, Any],
) -> dict[str, Any]:
    """
    Compute YoY growth fields given two consecutive period dicts.
    *current* is the more recent period; *prior* is the earlier period.
    """
    return {
        "yoy_revenue_growth":           compute_yoy_growth(current.get("revenue"), prior.get("revenue")),
        "yoy_gross_profit_growth":      compute_yoy_growth(current.get("gross_profit"), prior.get("gross_profit")),
        "yoy_operating_income_growth":  compute_yoy_growth(current.get("operating_income"), prior.get("operating_income")),
        "yoy_net_income_growth":        compute_yoy_growth(current.get("net_income"), prior.get("net_income")),
        "yoy_eps_growth":               compute_yoy_growth(current.get("eps_diluted"), prior.get("eps_diluted")),
    }


# ---------------------------------------------------------------------------
# CAGR (Compound Annual Growth Rate)
# ---------------------------------------------------------------------------

def compute_cagr(
    beginning_value: float | None,
    ending_value: float | None,
    years: float,
) -> float | None:
    """
    CAGR = (ending_value / beginning_value) ^ (1 / years) - 1

    Returns None if inputs are invalid.
    Handles negative beginning values by returning None (CAGR undefined for negatives).
    """
    if (
        beginning_value is None
        or ending_value is None
        or beginning_value <= 0
        or years <= 0
    ):
        return None
    try:
        return round(((ending_value / beginning_value) ** (1 / years) - 1) * 100, 4)
    except (ValueError, ZeroDivisionError):
        return None


# ---------------------------------------------------------------------------
# TTM (Trailing Twelve Months) aggregation
# ---------------------------------------------------------------------------

def compute_ttm_income_statement(quarters: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Sum the last 4 quarterly income statement periods to produce a TTM view.
    Non-additive fields (EPS, margins) are excluded and will be recomputed.
    """
    _ADDITIVE_FIELDS = [
        "revenue", "cost_of_revenue", "gross_profit",
        "research_and_development", "selling_general_administrative",
        "other_operating_expenses", "total_operating_expenses",
        "operating_income", "interest_income", "interest_expense",
        "total_other_income_expense", "ebitda", "depreciation_amortization",
        "income_before_tax", "income_tax_expense",
        "net_income", "net_income_attributable",
    ]
    last_4 = quarters[:4]
    ttm: dict[str, Any] = {"period": "ttm"}
    for field in _ADDITIVE_FIELDS:
        values = [q.get(field) for q in last_4]
        if all(v is None for v in values):
            ttm[field] = None
        else:
            ttm[field] = sum(v for v in values if v is not None)

    # Recompute derived common-size percentages on the summed TTM data
    ttm.update(compute_income_statement_common_size(ttm))
    return ttm


def compute_ttm_cash_flow(quarters: list[dict[str, Any]]) -> dict[str, Any]:
    """Sum last 4 quarters for cash flow TTM view."""
    _ADDITIVE_FIELDS = [
        "net_income", "depreciation_amortization", "stock_based_compensation",
        "deferred_income_tax", "change_in_working_capital",
        "accounts_receivable_changes", "inventory_changes", "accounts_payable_changes",
        "other_operating_activities", "net_cash_from_operating",
        "capex", "acquisitions", "purchases_of_investments", "sales_of_investments",
        "other_investing_activities", "net_cash_from_investing",
        "debt_repayment", "common_stock_issued", "common_stock_repurchased",
        "dividends_paid", "other_financing_activities", "net_cash_from_financing",
        "free_cash_flow", "net_change_in_cash",
    ]
    last_4 = quarters[:4]
    ttm: dict[str, Any] = {"period": "ttm"}
    for field in _ADDITIVE_FIELDS:
        values = [q.get(field) for q in last_4]
        ttm[field] = None if all(v is None for v in values) else sum(v for v in values if v is not None)
    ttm.update(compute_cash_flow_common_size(ttm))
    return ttm


# ---------------------------------------------------------------------------
# Multi-period CAGR batch
# ---------------------------------------------------------------------------

def compute_revenue_cagr_series(
    statements: list[dict[str, Any]],
    years_list: list[int] = [3, 5, 10],
) -> dict[str, float | None]:
    """
    Given a list of annual income statements (newest first), compute revenue
    CAGR for each requested year span.
    Returns a dict: {"cagr_3y": ..., "cagr_5y": ..., "cagr_10y": ...}
    """
    result: dict[str, float | None] = {}
    for years in years_list:
        if len(statements) > years:
            current_rev = statements[0].get("revenue")
            prior_rev = statements[years].get("revenue")
            result[f"cagr_{years}y"] = compute_cagr(prior_rev, current_rev, years)
        else:
            result[f"cagr_{years}y"] = None
    return result
