'use client';

import Image from 'next/image';
import { ExternalLink, Users, Building2 } from 'lucide-react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useStockDetail } from '@/hooks/useStockData';
import {
  formatMarketCap,
  formatPercent,
  formatPrice,
  formatPriceChange,
  formatVolume,
  signColorClass,
} from '@/utils/formatters';
import { cn } from '@/lib/utils';
import type { StockQuote } from '@/types/stock';

interface StockHeaderProps {
  ticker: string;
}

export function StockHeader({ ticker }: StockHeaderProps) {
  const { data: detail, isLoading } = useStockDetail(ticker);

  // Real-time price via WebSocket; fall back to REST quote
  const { quote: wsQuote, connectionState } = useWebSocket(ticker, { enabled: true });
  const quote: StockQuote | null = wsQuote ?? detail?.quote ?? null;

  if (isLoading) {
    return (
      <div className="animate-pulse flex gap-6 p-6 rounded-xl border border-border bg-card">
        <div className="h-12 w-12 rounded-lg bg-muted" />
        <div className="flex-1 space-y-3">
          <div className="h-6 w-48 rounded bg-muted" />
          <div className="h-4 w-32 rounded bg-muted" />
        </div>
      </div>
    );
  }

  const profile = detail?.profile;

  return (
    <div className="flex flex-col gap-4 p-6 rounded-xl border border-border bg-card">
      {/* Top row: logo + name + price */}
      <div className="flex flex-wrap items-start gap-4">
        {/* Logo */}
        {profile?.logo_url ? (
          <Image
            src={profile.logo_url}
            alt={profile.name ?? ticker}
            width={48}
            height={48}
            className="rounded-lg border border-border object-contain"
          />
        ) : (
          <div className="h-12 w-12 rounded-lg border border-border bg-muted flex items-center justify-center text-lg font-bold text-muted-foreground">
            {ticker[0]}
          </div>
        )}

        {/* Name & identifiers */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h1 className="text-xl font-bold text-foreground">{profile?.name ?? ticker}</h1>
            <span className="font-mono text-primary text-sm border border-primary/30 rounded px-1.5 py-0.5">
              {ticker}
            </span>
            {profile?.exchange && (
              <span className="text-xs text-muted-foreground">{profile.exchange}</span>
            )}
            {/* WebSocket status indicator */}
            <span
              className={cn(
                'h-2 w-2 rounded-full',
                connectionState === 'connected' ? 'bg-up' : 'bg-muted',
              )}
              title={connectionState}
            />
          </div>
          <div className="flex items-center gap-4 mt-1 flex-wrap">
            {profile?.sector && (
              <span className="text-xs text-muted-foreground">{profile.sector}</span>
            )}
            {profile?.industry && (
              <span className="text-xs text-muted-foreground">· {profile.industry}</span>
            )}
          </div>
        </div>

        {/* Price block */}
        {quote && (
          <div className="text-right">
            <p className="text-3xl font-bold font-mono text-foreground">
              {formatPrice(quote.price, profile?.currency ?? 'USD')}
            </p>
            <p className={cn('text-sm font-mono font-medium', signColorClass(quote.change))}>
              {formatPriceChange(quote.change, quote.change_percent)}
            </p>
          </div>
        )}
      </div>

      {/* Metrics row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4 border-t border-border">
        {[
          { label: 'Market Cap', value: formatMarketCap(quote?.market_cap) },
          { label: 'Volume', value: formatVolume(quote?.volume) },
          { label: 'Avg Volume', value: formatVolume(quote?.avg_volume) },
          { label: 'PE Ratio', value: quote?.pe_ratio != null ? quote.pe_ratio.toFixed(2) + 'x' : '—' },
          { label: 'EPS', value: quote?.eps != null ? formatPrice(quote.eps, profile?.currency ?? 'USD') : '—' },
          { label: '52W High', value: formatPrice(quote?.high_52w, profile?.currency ?? 'USD') },
          { label: '52W Low', value: formatPrice(quote?.low_52w, profile?.currency ?? 'USD') },
          { label: 'Employees', value: profile?.employees != null ? profile.employees.toLocaleString() : '—' },
        ].map(({ label, value }) => (
          <div key={label}>
            <p className="text-xs text-muted-foreground">{label}</p>
            <p className="text-sm font-mono font-medium text-foreground">{value}</p>
          </div>
        ))}
      </div>

      {/* Description */}
      {profile?.description && (
        <p className="text-sm text-muted-foreground line-clamp-3 pt-2 border-t border-border">
          {profile.description}
        </p>
      )}

      {/* Footer links */}
      <div className="flex items-center gap-4 text-xs text-muted-foreground">
        {profile?.ceo && (
          <span className="flex items-center gap-1">
            <Users className="h-3 w-3" /> CEO: {profile.ceo}
          </span>
        )}
        {profile?.country && (
          <span className="flex items-center gap-1">
            <Building2 className="h-3 w-3" /> {profile.country}
          </span>
        )}
        {profile?.website && (
          <a
            href={profile.website}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 hover:text-primary transition-colors"
          >
            <ExternalLink className="h-3 w-3" /> Website
          </a>
        )}
      </div>
    </div>
  );
}
