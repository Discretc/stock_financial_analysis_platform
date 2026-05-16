/**
 * Auth hook — wraps the Zustand auth store for components.
 */

'use client';

import { useAuthStore } from '@/store/authStore';

export function useAuth() {
  const user = useAuthStore((s) => s.user);
  const accessToken = useAuthStore((s) => s.accessToken);
  const isLoading = useAuthStore((s) => s.isLoading);
  const login = useAuthStore((s) => s.login);
  const logout = useAuthStore((s) => s.logout);
  const register = useAuthStore((s) => s.register);
  const fetchCurrentUser = useAuthStore((s) => s.fetchCurrentUser);

  return {
    user,
    accessToken,
    isLoading,
    isAuthenticated: !!user && !!accessToken,
    isAdmin: user?.role === 'admin',
    isPremium: user?.role === 'premium' || user?.role === 'admin',
    login,
    logout,
    register,
    fetchCurrentUser,
  };
}
