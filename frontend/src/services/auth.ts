import api from './api';

export interface LoginParams {
  email: string;
  password: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserInfo {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'manager' | 'sales';
  avatar_url: string | null;
  language: string;
  manager_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface RegisterParams {
  name: string;
  email: string;
  password: string;
  confirm_password: string;
}

export interface LoginResponse {
  user: UserInfo;
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export const authApi = {
  register: (params: RegisterParams) =>
    api.post<{ success: boolean; data: LoginResponse; message: string }>(
      '/auth/register',
      params
    ),

  login: (params: LoginParams) =>
    api.post<{ success: boolean; data: LoginResponse; message: string }>(
      '/auth/login',
      params
    ),

  refresh: (refreshToken: string) =>
    api.post<{ success: boolean; data: AuthTokens }>('/auth/refresh', {
      refresh_token: refreshToken,
    }),

  logout: (refreshToken: string) =>
    api.post('/auth/logout', { refresh_token: refreshToken }),

  getMe: () =>
    api.get<{ success: boolean; data: UserInfo }>('/auth/me'),
};
