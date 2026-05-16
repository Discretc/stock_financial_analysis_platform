"""
Profitability, valuation, liquidity, and leverage ratio computation engine.

All functions take normalised dicts and return computed ratio dicts.
No DB / HTTP calls — pure computation only.
"""

from typing import Any


def _safe_div(a: float | None, b: float | None) -> float | None:
    if a is None or b is None or b == 0:
        return None
    return a / b


# ---------------------------------------------------------------------------
# Profitability ratios
# ---------------------------------------------------------------------------

def compute_profitability_ratios(
    income: dict[str, Any],
    balance: dict[str, Any],
) -> dict[str, float | None]:
    rev = income.get("revenue")
    ebitda = income.get("ebitda")
    net_income = income.get("net_income")
    gross_profit = income.get("gross_profit")
    operating_income = income.get("operating_income")

    total_assets = balance.get("total_assets")
    total_equity = balance.get("total_equity")

    # ROIC = Operating Income (1 - tax_rate) / (Debt + Equity)
    # Simplified: Operating Income / (Total Assets - Current Liabilities)
    invested_capital = (
        (total_assets or 0) - (balance.get("total_current_liabilities") or 0)
    ) or None

    return {
        "gross_margin":      _safe_div(gross_profit, rev),
        "operating_margin":  _safe_div(operating_income, rev),
        "ebitda_margin":     _safe_div(ebitda, rev),
        "net_margin":        _safe_div(net_income, rev),
        "roa":               _safe_div(net_income, total_assets),
        "roe":               _safe_div(net_income, total_equity),
        "roic":              _safe_div(operating_income, invested_capital),
    }


# ---------------------------------------------------------------------------
# Liquidity ratios
# ---------------------------------------------------------------------------

def compute_liquidity_ratios(balance: dict[str, Any]) -> dict[str, float | None]:
    current_assets = balance.get("total_current_assets")
    current_liabilities = balance.get("total_current_liabilities")
    inventory = balance.get("inventory") or 0
    cash = balance.get("cash_and_short_term_investments")

    return {
        "current_ratio": _safe_div(current_assets, current_liabilities),
        "quick_ratio": _safe_div(
            (current_assets or 0) - inventory, current_liabilities
        ),
        "cash_ratio": _safe_div(cash, current_liabilities),
    }


# ---------------------------------------------------------------------------
# Leverage / solvency ratios
# ---------------------------------------------------------------------------

def compute_leverage_ratios(
    income: dict[str, Any],
    balance: dict[str, Any],
) -> dict[str, float | None]:
    total_debt = balance.get("total_debt")
    total_equity = balance.get("total_equity")
    total_assets = balance.get("total_assets")
    ebitda = income.get("ebitda")
    interest_expense = income.get("interest_expense")
    net_debt = balance.get("net_debt")
    operating_income = income.get("operating_income")

    return {
        "debt_to_equity":    _safe_div(total_debt, total_equity),
        "debt_to_assets":    _safe_div(total_debt, total_assets),
        "interest_coverage": _safe_div(operating_income, abs(interest_expense) if interest_expense else None),
        "net_debt_to_ebitda": _safe_div(net_debt, ebitda),
    }


# ---------------------------------------------------------------------------
# Cash flow quality ratios
# ---------------------------------------------------------------------------

def compute_cash_flow_ratios(
    income: dict[str, Any],
    cash_flow: dict[str, Any],
    market_cap: float | None = None,
    shares_outstanding: float | None = None,
) -> dict[str, float | None]:
    ocf = cash_flow.get("net_cash_from_operating")
    net_income = income.get("net_income")
    capex = cash_flow.get("capex")
    rev = income.get("revenue")
    fcf = cash_flow.get("free_cash_flow")

    fcf_per_share = _safe_div(fcf, shares_outstanding)
    fcf_yield = _safe_div(fcf, market_cap)

    return {
        "ocf_conversion":  _safe_div(ocf, net_income),
        "capex_intensity": _safe_div(abs(capex) if capex else None, rev),
        "fcf_per_share":   fcf_per_share,
        "fcf_yield":       fcf_yield,
    }


# ---------------------------------------------------------------------------
# Valuation ratios (requires live price data)
# ---------------------------------------------------------------------------

def compute_valuation_ratios(
    income: dict[str, Any],
    balance: dict[str, Any],
    cash_flow: dict[str, Any],
    price: float | None,
    shares_outstanding: float | None,
    market_cap: float | None,
) -> dict[str, float | None]:
    eps = income.get("eps_diluted")
    book_value_per_share = _safe_div(balance.get("total_equity"), shares_outstanding)
    rev = income.get("revenue")
    ebitda = income.get("ebitda")
    total_debt = balance.get("total_debt") or 0
    cash = balance.get("cash_and_short_term_investments") or 0
    ev = (market_cap or 0) + total_debt - cash  # Enterprise Value

    pe = _safe_div(price, eps) if eps and eps > 0 else None
    pb = _safe_div(price, book_value_per_share) if book_value_per_share and book_value_per_share > 0 else None
    ps = _safe_div(market_cap, rev)
    ev_ebitda = _safe_div(ev, ebitda) if ebitda and ebitda > 0 else None
    fcf = cash_flow.get("free_cash_flow")

    return {
        "pe_ratio":  pe,
        "pb_ratio":  pb,
        "ps_ratio":  ps,
        "ev_ebitda": ev_ebitda,
        "fcf_yield": _safe_div(fcf, market_cap),
        # PEG requires external EPS growth estimate; set to None here
        "peg_ratio": None,
    }
