'use client';

import { format } from 'date-fns';
import { useIncomeStatements } from '@/hooks/useFinancials';
import { FinancialTable, type FinancialRow } from './FinancialTable';
import type { IncomeStatement } from '@/types/financials';

interface IncomeStatementProps {
  ticker: string;
  period?: 'annual' | 'quarterly';
}

function buildRows(statements: IncomeStatement[]): FinancialRow[] {
  const v = (key: keyof IncomeStatement) =>
    statements.map((s) => (s[key] as number | null) ?? null);

  const cs = (key: keyof IncomeStatement) =>
    statements.map((s) => (s[key] as number | null) ?? null);

  return [
    {
      key: 'revenue',
      label: 'Revenue',
      level: 0,
      isHeader: false,
      values: v('revenue'),
      csValues: statements.map(() => 100),
      positiveIsGood: true,
    },
    {
      key: 'cost_of_revenue',
      label: 'Cost of Revenue',
      level: 1,
      values: v('cost_of_revenue'),
      csValues: cs('cs_cost_of_revenue_pct'),
      positiveIsGood: false,
    },
    {
      key: 'gross_profit',
      label: 'Gross Profit',
      level: 0,
      isHeader: true,
      childKeys: ['rd', 'sga'],
      values: v('gross_profit'),
      csValues: cs('cs_gross_profit_pct'),
      positiveIsGood: true,
    },
    {
      key: 'rd',
      label: 'R&D Expenses',
      level: 1,
      values: v('research_and_development'),
      csValues: cs('cs_rd_pct'),
      positiveIsGood: false,
    },
    {
      key: 'sga',
      label: 'SG&A Expenses',
      level: 1,
      values: v('selling_general_and_admin'),
      csValues: cs('cs_sga_pct'),
      positiveIsGood: false,
    },
    {
      key: 'total_opex',
      label: 'Total Operating Expenses',
      level: 0,
      values: v('total_operating_expenses'),
      csValues: cs('cs_total_opex_pct'),
      positiveIsGood: false,
    },
    {
      key: 'operating_income',
      label: 'Operating Income (EBIT)',
      level: 0,
      isHeader: true,
      childKeys: ['ebitda', 'interest_expense'],
      values: v('operating_income'),
      csValues: cs('cs_operating_income_pct'),
      positiveIsGood: true,
    },
    {
      key: 'ebitda',
      label: 'EBITDA',
      level: 1,
      values: v('ebitda'),
      csValues: cs('cs_ebitda_pct'),
      positiveIsGood: true,
    },
    {
      key: 'interest_expense',
      label: 'Interest Expense',
      level: 1,
      values: v('interest_expense'),
      positiveIsGood: false,
    },
    {
      key: 'income_before_tax',
      label: 'Income Before Tax',
      level: 0,
      values: v('income_before_tax'),
      positiveIsGood: true,
    },
    {
      key: 'income_tax',
      label: 'Income Tax',
      level: 1,
      values: v('income_tax_expense'),
      positiveIsGood: false,
    },
    {
      key: 'net_income',
      label: 'Net Income',
      level: 0,
      isHeader: true,
      childKeys: ['eps_basic', 'eps_diluted'],
      values: v('net_income'),
      csValues: cs('cs_net_income_pct'),
      positiveIsGood: true,
    },
    {
      key: 'eps_basic',
      label: 'EPS Basic',
      level: 1,
      values: v('eps_basic'),
      positiveIsGood: true,
    },
    {
      key: 'eps_diluted',
      label: 'EPS Diluted',
      level: 1,
      values: v('eps_diluted'),
      positiveIsGood: true,
    },
    // YoY growth rows
    {
      key: 'yoy_revenue_growth',
      label: 'Revenue Growth YoY',
      level: 0,
      values: v('yoy_revenue_growth'),
      positiveIsGood: true,
    },
    {
      key: 'yoy_ni_growth',
      label: 'Net Income Growth YoY',
      level: 0,
      values: v('yoy_net_income_growth'),
      positiveIsGood: true,
    },
  ];
}

export function IncomeStatementTable({ ticker, period = 'annual' }: IncomeStatementProps) {
  const { data: statements, isLoading, error } = useIncomeStatements(ticker, period, 10);

  if (isLoading) {
    return (
      <div className="rounded-xl border border-border bg-card p-8 flex items-center justify-center">
        <div className="h-8 w-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
      </div>
    );
  }

  if (error || !statements || statements.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-card p-8 text-center text-sm text-muted-foreground">
        No income statement data available.
      </div>
    );
  }

  const periods = statements.map((s) =>
    format(new Date(s.period_end_date), s.period === 'annual' ? 'yyyy' : "yyyy 'Q'Q"),
  );

  return (
    <FinancialTable
      title="Income Statement"
      periods={periods}
      rows={buildRows(statements)}
      currency={statements[0]?.currency ?? 'USD'}
      showToggle
    />
  );
}
