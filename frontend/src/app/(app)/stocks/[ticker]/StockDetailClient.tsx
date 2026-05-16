'use client';

import { useState } from 'react';
import { StockHeader } from '@/components/stock/StockHeader';
import { StockChart } from '@/components/stock/StockChart';
import { IncomeStatementTable } from '@/components/financials/IncomeStatement';
import { BalanceSheetTable } from '@/components/financials/BalanceSheet';
import { CashFlowStatementTable } from '@/components/financials/CashFlowStatement';
import { cn } from '@/lib/utils';

type Tab = 'overview' | 'income' | 'balance' | 'cashflow' | 'ratios';
type Period = 'annual' | 'quarterly';

const TABS: { key: Tab; label: string }[] = [
  { key: 'overview', label: 'Overview' },
  { key: 'income', label: 'Income Statement' },
  { key: 'balance', label: 'Balance Sheet' },
  { key: 'cashflow', label: 'Cash Flow' },
  { key: 'ratios', label: 'Ratios' },
];

interface StockDetailClientProps {
  ticker: string;
}

export function StockDetailClient({ ticker }: StockDetailClientProps) {
  const [tab, setTab] = useState<Tab>('overview');
  const [period, setPeriod] = useState<Period>('annual');

  return (
    <div className="space-y-6">
      {/* Stock header with live price */}
      <StockHeader ticker={ticker} />

      {/* Tab bar */}
      <div className="flex items-center justify-between border-b border-border">
        <div className="flex gap-0">
          {TABS.map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={cn(
                'px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px',
                tab === key
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground',
              )}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Annual / Quarterly toggle (hidden on overview/ratios) */}
        {(tab === 'income' || tab === 'balance' || tab === 'cashflow') && (
          <div className="flex gap-1 pb-1">
            {(['annual', 'quarterly'] as Period[]).map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={cn(
                  'px-3 py-1 rounded text-xs font-medium transition-colors capitalize',
                  period === p
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-muted',
                )}
              >
                {p}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Tab content */}
      <div>
        {tab === 'overview' && (
          <div className="space-y-6">
            <StockChart ticker={ticker} />
          </div>
        )}
        {tab === 'income' && <IncomeStatementTable ticker={ticker} period={period} />}
        {tab === 'balance' && <BalanceSheetTable ticker={ticker} period={period} />}
        {tab === 'cashflow' && <CashFlowStatementTable ticker={ticker} period={period} />}
        {tab === 'ratios' && (
          <div className="rounded-xl border border-border bg-card p-8 text-center text-sm text-muted-foreground">
            Financial ratios coming soon.
          </div>
        )}
      </div>
    </div>
  );
}
