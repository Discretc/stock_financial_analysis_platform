'use client';

import { format } from 'date-fns';
import { useBalanceSheets } from '@/hooks/useFinancials';
import { FinancialTable, type FinancialRow } from './FinancialTable';
import type { BalanceSheet } from '@/types/financials';

function buildRows(statements: BalanceSheet[]): FinancialRow[] {
  const v = (key: keyof BalanceSheet) =>
    statements.map((s) => (s[key] as number | null) ?? null);
  const cs = (key: keyof BalanceSheet) =>
    statements.map((s) => (s[key] as number | null) ?? null);

  return [
    // ASSETS
    { key: 'assets_header', label: 'ASSETS', level: 0, isHeader: true, childKeys: ['cash', 'receivables', 'inventory', 'other_ca', 'total_ca', 'ppe', 'goodwill', 'intangibles', 'other_nca', 'total_assets'], values: statements.map(() => null) },
    { key: 'cash', label: 'Cash & Short-term Investments', level: 1, values: v('cash_and_short_term_investments'), csValues: cs('cs_cash_pct'), positiveIsGood: true },
    { key: 'receivables', label: 'Net Receivables', level: 1, values: v('net_receivables'), csValues: cs('cs_receivables_pct'), positiveIsGood: true },
    { key: 'inventory', label: 'Inventory', level: 1, values: v('inventory'), csValues: cs('cs_inventory_pct'), positiveIsGood: true },
    { key: 'other_ca', label: 'Other Current Assets', level: 1, values: v('other_current_assets'), positiveIsGood: true },
    { key: 'total_ca', label: 'Total Current Assets', level: 0, values: v('total_current_assets'), csValues: cs('cs_current_assets_pct'), positiveIsGood: true },
    { key: 'ppe', label: 'PP&E (Net)', level: 1, values: v('property_plant_equipment_net'), csValues: cs('cs_ppe_pct'), positiveIsGood: true },
    { key: 'goodwill', label: 'Goodwill', level: 1, values: v('goodwill'), csValues: cs('cs_goodwill_pct'), positiveIsGood: true },
    { key: 'intangibles', label: 'Intangible Assets', level: 1, values: v('intangible_assets'), positiveIsGood: true },
    { key: 'other_nca', label: 'Other Non-Current Assets', level: 1, values: v('other_non_current_assets'), positiveIsGood: true },
    { key: 'total_assets', label: 'Total Assets', level: 0, isHeader: false, values: v('total_assets'), csValues: statements.map(() => 100), positiveIsGood: true },
    // LIABILITIES
    { key: 'liab_header', label: 'LIABILITIES', level: 0, isHeader: true, childKeys: ['ap', 'std', 'total_cl', 'ltd', 'total_ncl', 'total_liab'], values: statements.map(() => null) },
    { key: 'ap', label: 'Accounts Payable', level: 1, values: v('accounts_payable'), positiveIsGood: false },
    { key: 'std', label: 'Short-term Debt', level: 1, values: v('short_term_debt'), positiveIsGood: false },
    { key: 'total_cl', label: 'Total Current Liabilities', level: 0, values: v('total_current_liabilities'), csValues: cs('cs_total_current_liabilities_pct'), positiveIsGood: false },
    { key: 'ltd', label: 'Long-term Debt', level: 1, values: v('long_term_debt'), positiveIsGood: false },
    { key: 'total_ncl', label: 'Total Non-Current Liabilities', level: 1, values: v('total_non_current_liabilities'), positiveIsGood: false },
    { key: 'total_liab', label: 'Total Liabilities', level: 0, values: v('total_liabilities'), csValues: cs('cs_total_liabilities_pct'), positiveIsGood: false },
    // EQUITY
    { key: 'equity_header', label: 'EQUITY', level: 0, isHeader: true, childKeys: ['equity'], values: statements.map(() => null) },
    { key: 'equity', label: "Stockholders' Equity", level: 1, values: v('total_stockholders_equity'), csValues: cs('cs_equity_pct'), positiveIsGood: true },
    { key: 'total_le', label: 'Total Liabilities & Equity', level: 0, values: v('total_liabilities_and_equity'), positiveIsGood: true },
  ];
}

export function BalanceSheetTable({ ticker, period = 'annual' }: { ticker: string; period?: 'annual' | 'quarterly' }) {
  const { data, isLoading, error } = useBalanceSheets(ticker, period, 10);

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
        No balance sheet data available.
      </div>
    );
  }

  const periods = data.map((s) => format(new Date(s.period_end_date), 'yyyy'));

  return (
    <FinancialTable
      title="Balance Sheet"
      periods={periods}
      rows={buildRows(data)}
      currency={data[0]?.currency ?? 'USD'}
      showToggle
    />
  );
}
