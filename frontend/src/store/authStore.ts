/**
 * Zustand auth store.
 * Access tokens live in memory only — never written to localStorage or cookies.
 * Refresh token is in an HttpOnly cookie managed by the browser/server.
 */

'use client';

import { create } from 'zustand';
import type { UserResponse } from '@/types/auth';
import { authApi } from '@/lib/api';

interface AuthState {
  user: UserResponse | null;
  accessToken: string | null;
  isLoading: boolean;

  // Actions
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshAccessToken: () => Promise<string>;
  fetchCurrentUser: () => Promise<void>;
  setUser: (user: UserResponse | null) => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  isLoading: false,

  login: async (email, password) => {
    set({ isLoading: true });
    try {
      const { data } = await authApi.login(email, password);
      set({ accessToken: data.access_token, isLoading: false });
      // Fetch user profile after login
      await get().fetchCurrentUser();
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  register: async (email, password, fullName) => {
    set({ isLoading: true });
    try {
      await authApi.register(email, password, fullName);
      set({ isLoading: false });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  logout: async () => {
    const { accessToken } = get();
    set({ user: null, accessToken: null });
    try {
      if (accessToken) {
        // Tell the server to revoke the refresh token (cookie-based)
        await authApi.logout(''); // Server reads refresh token from cookie
      }
    } catch {
      // Ignore errors on logout
    }
  },

  refreshAccessToken: async () => {
    // Refresh token is in an HttpOnly cookie — no need to send it manually
    const { data } = await authApi.refresh('');
    set({ accessToken: data.access_token });
    return data.access_token as string;
  },

  fetchCurrentUser: async () => {
    try {
      const { data } = await authApi.me();
      set({ user: data });
    } catch {
      set({ user: null, accessToken: null });
    }
  },

  setUser: (user) => set({ user }),
}));
