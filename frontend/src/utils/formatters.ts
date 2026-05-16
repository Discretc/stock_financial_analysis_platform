/**
 * Number formatting utilities for financial data display.
 */

/**
 * Format a large number in compact form: 1.2B, 450M, 3.5T
 */
export function formatMarketCap(value: number | null | undefined): string {
  if (value == null) return '—';
  const abs = Math.abs(value);
  if (abs >= 1e12) return `${(value / 1e12).toFixed(2)}T`;
  if (abs >= 1e9) return `${(value / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `${(value / 1e6).toFixed(2)}M`;
  if (abs >= 1e3) return `${(value / 1e3).toFixed(1)}K`;
  return value.toFixed(0);
}

/**
 * Format a financial statement line item in millions (standard for financial models).
 */
export function formatFinancialValue(
  value: number | null | undefined,
  currency = 'USD',
  decimals = 0,
): string {
  if (value == null) return '—';
  const millions = value / 1_000_000;
  const formatted = new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(millions);
  return formatted;
}

/**
 * Format a percentage value with a sign (+12.3% or -5.1%).
 */
export function formatPercent(
  value: number | null | undefined,
  decimals = 1,
  showSign = false,
): string {
  if (value == null) return '—';
  const formatted = `${Math.abs(value).toFixed(decimals)}%`;
  if (showSign) {
    return value >= 0 ? `+${formatted}` : `-${formatted}`;
  }
  return value < 0 ? `-${formatted}` : formatted;
}

/**
 * Format a common-size percentage (e.g., 34.5%).
 */
export function formatCommonSize(value: number | null | undefined): string {
  if (value == null) return '—';
  return `${value.toFixed(1)}%`;
}

/**
 * Format a stock price.
 */
export function formatPrice(value: number | null | undefined, currency = 'USD'): string {
  if (value == null) return '—';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

/**
 * Format price change: +1.23 (+0.45%)
 */
export function formatPriceChange(
  change: number | null | undefined,
  changePercent: number | null | undefined,
): string {
  if (change == null || changePercent == null) return '—';
  const sign = change >= 0 ? '+' : '';
  return `${sign}${change.toFixed(2)} (${sign}${changePercent.toFixed(2)}%)`;
}

/**
 * Format a ratio like PE, PB etc. (plain number with 1-2 decimals)
 */
export function formatRatio(value: number | null | undefined, decimals = 2): string {
  if (value == null) return '—';
  return value.toFixed(decimals) + 'x';
}

/**
 * Format volume.
 */
export function formatVolume(value: number | null | undefined): string {
  if (value == null) return '—';
  if (value >= 1e9) return `${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `${(value / 1e6).toFixed(2)}M`;
  if (value >= 1e3) return `${(value / 1e3).toFixed(1)}K`;
  return value.toFixed(0);
}

/**
 * Return CSS class for a signed number (red/green).
 */
export function signColorClass(value: number | null | undefined): string {
  if (value == null) return 'text-muted-foreground';
  return value >= 0 ? 'text-up' : 'text-down';
}
