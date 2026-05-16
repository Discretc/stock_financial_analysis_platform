"""
Tests for common-size analytics engine.
"""

import pytest

from app.analytics.common_size import (
    compute_balance_sheet_common_size,
    compute_cagr,
    compute_cash_flow_common_size,
    compute_income_statement_common_size,
    compute_income_statement_yoy,
    compute_yoy_growth,
)


def test_income_statement_common_size_basic():
    raw = {"revenue": 100_000, "gross_profit": 40_000, "net_income": 20_000}
    cs = compute_income_statement_common_size(raw)
    assert cs["cs_gross_profit_pct"] == pytest.approx(40.0)
    assert cs["cs_net_income_pct"] == pytest.approx(20.0)


def test_income_statement_common_size_zero_revenue():
    raw = {"revenue": 0, "gross_profit": 10_000}
    cs = compute_income_statement_common_size(raw)
    assert cs["cs_gross_profit_pct"] is None


def test_income_statement_common_size_none_revenue():
    raw = {"revenue": None, "gross_profit": 10_000}
    cs = compute_income_statement_common_size(raw)
    assert cs["cs_gross_profit_pct"] is None


def test_balance_sheet_common_size():
    raw = {"total_assets": 200_000, "cash_and_short_term_investments": 50_000}
    cs = compute_balance_sheet_common_size(raw)
    assert cs["cs_cash_pct"] == pytest.approx(25.0)


def test_cash_flow_common_size():
    raw = {"net_cash_from_operating": 80_000, "capex": -20_000, "free_cash_flow": 60_000}
    cs = compute_cash_flow_common_size(raw)
    assert cs["cs_fcf_pct"] == pytest.approx(75.0)
    assert cs["cs_capex_pct"] == pytest.approx(-25.0)


def test_yoy_growth_positive():
    assert compute_yoy_growth(110, 100) == pytest.approx(10.0)


def test_yoy_growth_from_negative():
    """Moving from loss to profit — uses abs(prior)."""
    result = compute_yoy_growth(50, -100)
    assert result == pytest.approx(150.0)


def test_yoy_growth_zero_denominator():
    assert compute_yoy_growth(100, 0) is None


def test_cagr_basic():
    # 100 → 200 over 5 years ≈ 14.87%
    result = compute_cagr(100, 200, 5)
    assert result == pytest.approx(14.87, abs=0.01)


def test_cagr_negative_beginning():
    assert compute_cagr(-100, 200, 5) is None


def test_cagr_zero_years():
    assert compute_cagr(100, 200, 0) is None
