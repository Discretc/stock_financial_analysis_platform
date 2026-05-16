/**
 * TypeScript types matching backend Pydantic schemas.
 * Keep in sync with backend/app/schemas/auth.py
 */

export interface UserResponse {
  id: string;
  email: string;
  full_name: string | null;
  role: 'user' | 'premium' | 'admin';
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  last_login_at: string | null;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  expires_in: number;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string;
}
