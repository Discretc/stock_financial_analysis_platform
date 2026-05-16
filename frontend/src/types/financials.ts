/**
 * Financial statement types.
 * Mirrors backend/app/schemas/financials.py — includes cs_* common-size percentage fields.
 */

export interface IncomeStatement {
  id: string;
  ticker: string;
  period: 'annual' | 'quarterly';
  period_end_date: string;
  fiscal_year: number | null;
  fiscal_quarter: number | null;
  currency: string | null;

  revenue: number | null;
  cost_of_revenue: number | null;
  gross_profit: number | null;
  research_and_development: number | null;
  selling_general_and_admin: number | null;
  total_operating_expenses: number | null;
  operating_income: number | null;
  ebitda: number | null;
  interest_expense: number | null;
  income_before_tax: number | null;
  income_tax_expense: number | null;
  net_income: number | null;
  eps_basic: number | null;
  eps_diluted: number | null;
  shares_outstanding_basic: number | null;
  shares_outstanding_diluted: number | null;

  // Common-size percentages (% of revenue)
  cs_cost_of_revenue_pct: number | null;
  cs_gross_profit_pct: number | null;
  cs_rd_pct: number | null;
  cs_sga_pct: number | null;
  cs_total_opex_pct: number | null;
  cs_operating_income_pct: number | null;
  cs_ebitda_pct: number | null;
  cs_net_income_pct: number | null;

  // YoY growth
  yoy_revenue_growth: number | null;
  yoy_gross_profit_growth: number | null;
  yoy_operating_income_growth: number | null;
  yoy_net_income_growth: number | null;
  yoy_eps_diluted_growth: number | null;
}

export interface BalanceSheet {
  id: string;
  ticker: string;
  period: 'annual' | 'quarterly';
  period_end_date: string;
  fiscal_year: number | null;
  currency: string | null;

  cash_and_short_term_investments: number | null;
  net_receivables: number | null;
  inventory: number | null;
  other_current_assets: number | null;
  total_current_assets: number | null;
  property_plant_equipment_net: number | null;
  goodwill: number | null;
  intangible_assets: number | null;
  other_non_current_assets: number | null;
  total_assets: number | null;

  accounts_payable: number | null;
  short_term_debt: number | null;
  total_current_liabilities: number | null;
  long_term_debt: number | null;
  total_non_current_liabilities: number | null;
  total_liabilities: number | null;
  total_stockholders_equity: number | null;
  total_liabilities_and_equity: number | null;

  // Common-size (% of total assets)
  cs_cash_pct: number | null;
  cs_receivables_pct: number | null;
  cs_inventory_pct: number | null;
  cs_current_assets_pct: number | null;
  cs_ppe_pct: number | null;
  cs_goodwill_pct: number | null;
  cs_total_current_liabilities_pct: number | null;
  cs_total_debt_pct: number | null;
  cs_total_liabilities_pct: number | null;
  cs_equity_pct: number | null;
}

export interface CashFlowStatement {
  id: string;
  ticker: string;
  period: 'annual' | 'quarterly';
  period_end_date: string;
  fiscal_year: number | null;
  currency: string | null;

  net_income: number | null;
  depreciation_and_amortization: number | null;
  stock_based_compensation: number | null;
  change_in_working_capital: number | null;
  other_operating_activities: number | null;
  net_cash_from_operating: number | null;
  capital_expenditures: number | null;
  acquisitions: number | null;
  other_investing_activities: number | null;
  net_cash_from_investing: number | null;
  dividends_paid: number | null;
  stock_repurchases: number | null;
  net_borrowings: number | null;
  other_financing_activities: number | null;
  net_cash_from_financing: number | null;
  free_cash_flow: number | null;

  // Common-size (% of OCF)
  cs_net_income_pct: number | null;
  cs_da_pct: number | null;
  cs_sbc_pct: number | null;
  cs_working_capital_pct: number | null;
  cs_capex_pct: number | null;
  cs_fcf_pct: number | null;
  cs_investing_pct: number | null;
  cs_financing_pct: number | null;
}

export interface FinancialRatios {
  period_end_date: string;
  period: string;

  gross_margin: number | null;
  operating_margin: number | null;
  ebitda_margin: number | null;
  net_margin: number | null;
  return_on_assets: number | null;
  return_on_equity: number | null;
  return_on_invested_capital: number | null;

  current_ratio: number | null;
  quick_ratio: number | null;
  cash_ratio: number | null;

  debt_to_equity: number | null;
  debt_to_assets: number | null;
  interest_coverage: number | null;
  net_debt_to_ebitda: number | null;

  pe_ratio: number | null;
  pb_ratio: number | null;
  ps_ratio: number | null;
  ev_to_ebitda: number | null;
  fcf_yield: number | null;

  ocf_conversion: number | null;
  capex_intensity: number | null;
  fcf_per_share: number | null;
}
