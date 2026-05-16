'use client';

import { format } from 'date-fns';
import { useCashFlowStatements } from '@/hooks/useFinancials';
import { FinancialTable, type FinancialRow } from './FinancialTable';
import type { CashFlowStatement } from '@/types/financials';

function buildRows(statements: CashFlowStatement[]): FinancialRow[] {
  const v = (key: keyof CashFlowStatement) =>
    statements.map((s) => (s[key] as number | null) ?? null);
  const cs = (key: keyof CashFlowStatement) =>
    statements.map((s) => (s[key] as number | null) ?? null);

  return [
    // Operating
    { key: 'ocf_header', label: 'OPERATING ACTIVITIES', level: 0, isHeader: true, childKeys: ['net_income_cf', 'da', 'sbc', 'wc', 'other_op', 'ocf'], values: statements.map(() => null) },
    { key: 'net_income_cf', label: 'Net Income', level: 1, values: v('net_income'), csValues: cs('cs_net_income_pct'), positiveIsGood: true },
    { key: 'da', label: 'D&A', level: 1, values: v('depreciation_and_amortization'), csValues: cs('cs_da_pct'), positiveIsGood: true },
    { key: 'sbc', label: 'Stock-Based Compensation', level: 1, values: v('stock_based_compensation'), csValues: cs('cs_sbc_pct'), positiveIsGood: false },
    { key: 'wc', label: 'Change in Working Capital', level: 1, values: v('change_in_working_capital'), csValues: cs('cs_working_capital_pct'), positiveIsGood: true },
    { key: 'other_op', label: 'Other Operating Activities', level: 1, values: v('other_operating_activities'), positiveIsGood: true },
    { key: 'ocf', label: 'Net Cash from Operations (OCF)', level: 0, values: v('net_cash_from_operating'), positiveIsGood: true },
    // Investing
    { key: 'inv_header', label: 'INVESTING ACTIVITIES', level: 0, isHeader: true, childKeys: ['capex', 'acquisitions', 'other_inv', 'net_inv'], values: statements.map(() => null) },
    { key: 'capex', label: 'Capital Expenditures', level: 1, values: v('capital_expenditures'), csValues: cs('cs_capex_pct'), positiveIsGood: false },
    { key: 'acquisitions', label: 'Acquisitions', level: 1, values: v('acquisitions'), positiveIsGood: false },
    { key: 'other_inv', label: 'Other Investing Activities', level: 1, values: v('other_investing_activities'), positiveIsGood: true },
    { key: 'net_inv', label: 'Net Cash from Investing', level: 0, values: v('net_cash_from_investing'), csValues: cs('cs_investing_pct'), positiveIsGood: false },
    // Financing
    { key: 'fin_header', label: 'FINANCING ACTIVITIES', level: 0, isHeader: true, childKeys: ['dividends', 'buybacks', 'net_borrow', 'other_fin', 'net_fin'], values: statements.map(() => null) },
    { key: 'dividends', label: 'Dividends Paid', level: 1, values: v('dividends_paid'), positiveIsGood: false },
    { key: 'buybacks', label: 'Stock Repurchases', level: 1, values: v('stock_repurchases'), positiveIsGood: true },
    { key: 'net_borrow', label: 'Net Borrowings', level: 1, values: v('net_borrowings'), positiveIsGood: false },
    { key: 'other_fin', label: 'Other Financing Activities', level: 1, values: v('other_financing_activities'), positiveIsGood: true },
    { key: 'net_fin', label: 'Net Cash from Financing', level: 0, values: v('net_cash_from_financing'), csValues: cs('cs_financing_pct'), positiveIsGood: false },
    // FCF
    { key: 'fcf', label: 'Free Cash Flow (FCF)', level: 0, values: v('free_cash_flow'), csValues: cs('cs_fcf_pct'), positiveIsGood: true },
  ];
}

export function CashFlowStatementTable({ ticker, period = 'annual' }: { ticker: string; period?: 'annual' | 'quarterly' }) {
  const { data, isLoading, error } = useCashFlowStatements(ticker, period, 10);

  if (isLoading) {
    return (
      <div className="rounded-xl border border-border bg-card p-8 flex items-center justify-center">
        <div className="h-8 w-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
      </div>
    );
  }
  if (error || !data || data.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-card p-8 text-center text-sm text-muted-foreground">
        No cash flow data available.
      </div>
    );
  }

  const periods = data.map((s) => format(new Date(s.period_end_date), 'yyyy'));

  return (
    <FinancialTable
      title="Cash Flow Statement"
      periods={periods}
      rows={buildRows(data)}
      currency={data[0]?.currency ?? 'USD'}
      showToggle
    />
  );
}
