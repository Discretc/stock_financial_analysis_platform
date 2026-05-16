/**
 * Stock & market data types.
 * Matches backend/app/schemas/stock.py (to be kept in sync).
 */

export interface CompanyProfile {
  id: string;
  ticker: string;
  name: string;
  exchange: string | null;
  sector: string | null;
  industry: string | null;
  description: string | null;
  website: string | null;
  logo_url: string | null;
  ceo: string | null;
  employees: number | null;
  country: string | null;
  currency: string | null;
  market_cap: number | null;
  ipo_date: string | null;
}

export interface StockQuote {
  ticker: string;
  price: number | null;
  change: number | null;
  change_percent: number | null;
  volume: number | null;
  avg_volume: number | null;
  market_cap: number | null;
  pe_ratio: number | null;
  eps: number | null;
  high_52w: number | null;
  low_52w: number | null;
  open: number | null;
  previous_close: number | null;
  timestamp: string | null;
}

export interface HistoricalPrice {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  adj_close: number | null;
  volume: number;
  vwap: number | null;
}

export interface StockDetail {
  profile: CompanyProfile;
  quote: StockQuote;
}

export interface SearchResult {
  ticker: string;
  name: string;
  exchange: string | null;
  sector: string | null;
}
