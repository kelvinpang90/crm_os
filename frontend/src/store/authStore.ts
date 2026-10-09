import { create } from 'zustand';
import { authApi, type UserInfo, type LoginParams } from '@/services/auth';

interface AuthState {
  user: UserInfo | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  login: (params: LoginParams) => Promise<void>;
  logout: () => Promise<void>;
  fetchMe: () => Promise<void>;
  clearError: () => void;
  setUser: (user: UserInfo) => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isAuthenticated: !!localStorage.getItem('access_token'),
  isLoading: false,
  error: null,

  login: async (params) => {
    set({ isLoading: true, error: null });
    try {
      const res = await authApi.login(params);
      const { user, access_token, refresh_token } = res.data.data;
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (err: any) {
      const message =
        err.response?.data?.error?.message || '登录失败，请重试';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  logout: async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    try {
      if (refreshToken) {
        await authApi.logout(refreshToken);
      }
    } catch {
      // ignore logout errors
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      set({ user: null, isAuthenticated: false });
    }
  },

  fetchMe: async () => {
    try {
      const res = await authApi.getMe();
      set({ user: res.data.data, isAuthenticated: true });
    } catch {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      set({ user: null, isAuthenticated: false });
    }
  },

  clearError: () => set({ error: null }),

  setUser: (user) => set({ user }),
}));
