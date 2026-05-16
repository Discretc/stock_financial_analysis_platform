/**
 * TanStack Query hooks for stock data.
 */

import { useQuery } from '@tanstack/react-query';
import { stocksApi } from '@/lib/api';
import type { CompanyProfile, HistoricalPrice, SearchResult, StockDetail, StockQuote } from '@/types/stock';

export const stockKeys = {
  all: ['stocks'] as const,
  search: (q: string) => [...stockKeys.all, 'search', q] as const,
  detail: (ticker: string) => [...stockKeys.all, 'detail', ticker] as const,
  quote: (ticker: string) => [...stockKeys.all, 'quote', ticker] as const,
  historical: (ticker: string, from?: string, to?: string) =>
    [...stockKeys.all, 'historical', ticker, from, to] as const,
};

export function useStockSearch(q: string, enabled = true) {
  return useQuery<SearchResult[]>({
    queryKey: stockKeys.search(q),
    queryFn: async () => {
      const { data } = await stocksApi.search(q);
      return (data as { results: SearchResult[] }).results;
    },
    enabled: enabled && q.trim().length >= 1,
    staleTime: 60_000,
  });
}

export function useStockDetail(ticker: string) {
  return useQuery<StockDetail>({
    queryKey: stockKeys.detail(ticker),
    queryFn: async () => {
      const { data } = await stocksApi.getDetail(ticker);
      return data;
    },
    enabled: !!ticker,
    staleTime: 15_000,
  });
}

export function useStockQuote(ticker: string, enabled = true) {
  return useQuery<StockQuote>({
    queryKey: stockKeys.quote(ticker),
    queryFn: async () => {
      const { data } = await stocksApi.getQuote(ticker);
      return data;
    },
    enabled: enabled && !!ticker,
    staleTime: 15_000,
    refetchInterval: 30_000, // Poll every 30s as a fallback to WebSocket
  });
}

export function useHistoricalPrices(ticker: string, from?: string, to?: string) {
  return useQuery<HistoricalPrice[]>({
    queryKey: stockKeys.historical(ticker, from, to),
    queryFn: async () => {
      const { data } = await stocksApi.getHistorical(ticker, from, to);
      // Backend returns newest-first; reverse to oldest→newest for left-to-right chart
      const arr = (data as { data: HistoricalPrice[] }).data ?? [];
      return [...arr].reverse();
    },
    enabled: !!ticker,
    staleTime: 5 * 60_000, // 5 minutes
  });
}
