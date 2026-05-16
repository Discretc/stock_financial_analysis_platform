'use client';

import { useMemo, useState } from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
} from 'recharts';
import { useHistoricalPrices } from '@/hooks/useStockData';
import { formatPrice } from '@/utils/formatters';
import { cn } from '@/lib/utils';

type Range = '1M' | '3M' | '6M' | '1Y' | '2Y' | '5Y';

const RANGE_DAYS: Record<Range, number> = {
  '1M': 30,
  '3M': 90,
  '6M': 180,
  '1Y': 365,
  '2Y': 730,
  '5Y': 1825,
};

interface StockChartProps {
  ticker: string;
  currency?: string;
}

export function StockChart({ ticker, currency = 'USD' }: StockChartProps) {
  const [range, setRange] = useState<Range>('1Y');

  const toDate = new Date();
  const fromDate = new Date();
  fromDate.setDate(fromDate.getDate() - RANGE_DAYS[range]);

  const { data: prices, isLoading } = useHistoricalPrices(
    ticker,
    fromDate.toISOString().slice(0, 10),
    toDate.toISOString().slice(0, 10),
  );

  const isPositive = useMemo(() => {
    if (!prices || prices.length < 2) return true;
    return (prices[prices.length - 1]?.close ?? 0) >= (prices[0]?.close ?? 0);
  }, [prices]);

  const strokeColor = isPositive ? '#22c55e' : '#ef4444';
  const fillColor = isPositive ? 'rgba(34,197,94,0.08)' : 'rgba(239,68,68,0.08)';

  const firstClose = prices?.[0]?.close ?? null;

  return (
    <div className="rounded-xl border border-border bg-card p-4">
      {/* Range selector */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-foreground">Price History</h2>
        <div className="flex gap-1">
          {(Object.keys(RANGE_DAYS) as Range[]).map((r) => (
            <button
              key={r}
              onClick={() => setRange(r)}
              className={cn(
                'px-2.5 py-1 rounded text-xs font-medium transition-colors',
                range === r
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted',
              )}
            >
              {r}
            </button>
          ))}
        </div>
      </div>

      {/* Chart */}
      <div className="h-64">
        {isLoading ? (
          <div className="h-full flex items-center justify-center">
            <div className="h-8 w-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
          </div>
        ) : !prices || prices.length === 0 ? (
          <div className="h-full flex items-center justify-center text-sm text-muted-foreground">
            No historical data available
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={prices} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={strokeColor} stopOpacity={0.15} />
                  <stop offset="95%" stopColor={strokeColor} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11, fill: '#94a3b8' }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v: string) => {
                  const d = new Date(v);
                  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                }}
                interval="preserveStartEnd"
              />
              <YAxis
                tick={{ fontSize: 11, fill: '#94a3b8' }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v: number) => formatPrice(v, currency).replace('$', '')}
                width={60}
                domain={['auto', 'auto']}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px',
                  fontSize: 12,
                }}
                labelFormatter={(label: string) =>
                  new Date(label).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                  })
                }
                formatter={(value: number) => [formatPrice(value, currency), 'Close']}
              />
              {firstClose != null && (
                <ReferenceLine
                  y={firstClose}
                  stroke="rgba(148,163,184,0.3)"
                  strokeDasharray="4 4"
                />
              )}
              <Area
                type="monotone"
                dataKey="close"
                stroke={strokeColor}
                strokeWidth={2}
                fill="url(#priceGradient)"
                dot={false}
                activeDot={{ r: 4, fill: strokeColor }}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
