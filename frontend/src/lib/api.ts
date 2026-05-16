/**
 * Centralized API client using axios.
 * All requests route through Next.js rewrites → backend.
 * Access tokens are stored in Zustand (memory only — not localStorage).
 * Refresh token is stored in an HttpOnly cookie (set by the server).
 */

import axios, { type AxiosInstance, type AxiosResponse } from 'axios';

const BASE_URL = '/api/v1';

// ---------------------------------------------------------------------------
// Axios instance
// ---------------------------------------------------------------------------

export const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Send cookies (refresh token) on every request
  timeout: 30_000,
});

// ---------------------------------------------------------------------------
// Request interceptor — attach access token
// ---------------------------------------------------------------------------

apiClient.interceptors.request.use((config) => {
  // Access token is stored in Zustand memory store (not localStorage/sessionStorage)
  // Importing here avoids circular dependency
  const { useAuthStore } = require('@/store/authStore');
  const accessToken = useAuthStore.getState().accessToken;
  if (accessToken && config.headers) {
    config.headers['Authorization'] = `Bearer ${accessToken}`;
  }
  return config;
});

// ---------------------------------------------------------------------------
// Response interceptor — handle 401 and token refresh
// ---------------------------------------------------------------------------

let isRefreshing = false;
let failedQueue: Array<{ resolve: (v: unknown) => void; reject: (r: unknown) => void }> = [];

function processQueue(error: unknown, token: string | null = null) {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else {
      resolve(token);
    }
  });
  failedQueue = [];
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Don't try to refresh tokens for auth endpoints — it causes a deadlock
    const isAuthEndpoint = originalRequest?.url?.includes('/auth/');

    if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers['Authorization'] = `Bearer ${token}`;
            return apiClient(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const { useAuthStore } = require('@/store/authStore');
        const newAccessToken = await useAuthStore.getState().refreshAccessToken();
        processQueue(null, newAccessToken);
        originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        const { useAuthStore } = require('@/store/authStore');
        useAuthStore.getState().logout();
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  },
);

// ---------------------------------------------------------------------------
// Typed API functions
// ---------------------------------------------------------------------------

export const stocksApi = {
  search: (q: string, limit = 20) =>
    apiClient.get('/stocks/search', { params: { q, limit } }),

  getProfile: (ticker: string) =>
    apiClient.get(`/stocks/${ticker}/profile`),

  getQuote: (ticker: string) =>
    apiClient.get(`/stocks/${ticker}/quote`),

  getHistorical: (ticker: string, from?: string, to?: string) =>
    apiClient.get(`/stocks/${ticker}/historical`, { params: { from_date: from, to_date: to } }),

  getDetail: (ticker: string) =>
    apiClient.get(`/stocks/${ticker}`),
};

export const financialsApi = {
  getIncomeStatement: (ticker: string, period = 'annual', limit = 10) =>
    apiClient.get(`/financials/${ticker}/income-statement`, { params: { period, limit } }),

  getBalanceSheet: (ticker: string, period = 'annual', limit = 10) =>
    apiClient.get(`/financials/${ticker}/balance-sheet`, { params: { period, limit } }),

  getCashFlow: (ticker: string, period = 'annual', limit = 10) =>
    apiClient.get(`/financials/${ticker}/cash-flow`, { params: { period, limit } }),

  getRatios: (ticker: string, period = 'annual') =>
    apiClient.get(`/financials/${ticker}/ratios`, { params: { period } }),
};

export const authApi = {
  login: (email: string, password: string) =>
    apiClient.post('/auth/login', { email, password }),

  register: (email: string, password: string, full_name?: string) =>
    apiClient.post('/auth/register', { email, password, full_name }),

  refresh: (refresh_token: string) =>
    apiClient.post('/auth/refresh', { refresh_token }),

  logout: (refresh_token: string) =>
    apiClient.post('/auth/logout', { refresh_token }),

  me: () =>
    apiClient.get('/auth/me'),
};

export const watchlistsApi = {
  list: () => apiClient.get('/watchlists'),
  create: (name: string, description?: string) =>
    apiClient.post('/watchlists', { name, description }),
  addItem: (watchlistId: string, ticker: string) =>
    apiClient.post(`/watchlists/${watchlistId}/items`, { ticker }),
  delete: (watchlistId: string) =>
    apiClient.delete(`/watchlists/${watchlistId}`),
};
