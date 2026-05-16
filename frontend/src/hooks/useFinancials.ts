/**
 * TanStack Query hooks for financial statements.
 */

import { useQuery } from '@tanstack/react-query';
import { financialsApi } from '@/lib/api';
import type {
  BalanceSheet,
  CashFlowStatement,
  FinancialRatios,
  IncomeStatement,
} from '@/types/financials';

export const financialKeys = {
  all: ['financials'] as const,
  income: (ticker: string, period: string, limit: number) =>
    [...financialKeys.all, 'income', ticker, period, limit] as const,
  balance: (ticker: string, period: string, limit: number) =>
    [...financialKeys.all, 'balance', ticker, period, limit] as const,
  cashflow: (ticker: string, period: string, limit: number) =>
    [...financialKeys.all, 'cashflow', ticker, period, limit] as const,
  ratios: (ticker: string, period: string) =>
    [...financialKeys.all, 'ratios', ticker, period] as const,
};

export function useIncomeStatements(
  ticker: string,
  period: 'annual' | 'quarterly' = 'annual',
  limit = 10,
) {
  return useQuery<IncomeStatement[]>({
    queryKey: financialKeys.income(ticker, period, limit),
    queryFn: async () => {
      const { data } = await financialsApi.getIncomeStatement(ticker, period, limit);
      return (data as { statements: IncomeStatement[] }).statements ?? [];
    },
    enabled: !!ticker,
    staleTime: 4 * 60 * 60_000, // 4 hours
  });
}

export function useBalanceSheets(
  ticker: string,
  period: 'annual' | 'quarterly' = 'annual',
  limit = 10,
) {
  return useQuery<BalanceSheet[]>({
    queryKey: financialKeys.balance(ticker, period, limit),
    queryFn: async () => {
      const { data } = await financialsApi.getBalanceSheet(ticker, period, limit);
      return (data as { statements: BalanceSheet[] }).statements ?? [];
    },
    enabled: !!ticker,
    staleTime: 4 * 60 * 60_000,
  });
}

export function useCashFlowStatements(
  ticker: string,
  period: 'annual' | 'quarterly' = 'annual',
  limit = 10,
) {
  return useQuery<CashFlowStatement[]>({
    queryKey: financialKeys.cashflow(ticker, period, limit),
    queryFn: async () => {
      const { data } = await financialsApi.getCashFlow(ticker, period, limit);
      return (data as { statements: CashFlowStatement[] }).statements ?? [];
    },
    enabled: !!ticker,
    staleTime: 4 * 60 * 60_000,
  });
}

export function useFinancialRatios(
  ticker: string,
  period: 'annual' | 'quarterly' = 'annual',
) {
  return useQuery<FinancialRatios[]>({
    queryKey: financialKeys.ratios(ticker, period),
    queryFn: async () => {
      const { data } = await financialsApi.getRatios(ticker, period);
      return data;
    },
    enabled: !!ticker,
    staleTime: 4 * 60 * 60_000,
  });
}
