import type { Metadata } from 'next';
import { StockSearch } from '@/components/stock/StockSearch';

export const metadata: Metadata = {
  title: 'Stock Screener',
  description: 'Search and analyse stocks.',
};

export default function StocksPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Stock Screener</h1>
        <p className="text-muted-foreground mt-1">Search for any stock to view detailed financial analysis.</p>
      </div>

      <div className="max-w-lg">
        <StockSearch placeholder="Search by ticker or company name…" className="max-w-full" />
      </div>

      <div className="rounded-xl border border-border bg-card p-12 flex flex-col items-center justify-center gap-3 text-center">
        <p className="text-muted-foreground text-sm">
          Enter a ticker symbol above to view financials, price history, and analytics.
        </p>
        <p className="text-xs text-muted-foreground">
          Try <strong className="text-primary">AAPL</strong>, <strong className="text-primary">MSFT</strong>, or <strong className="text-primary">NVDA</strong>
        </p>
      </div>
    </div>
  );
}
