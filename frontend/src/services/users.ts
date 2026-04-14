import api from './api';
import type { ApiResponse, User } from '@/types';

export const usersApi = {
  getUsers: () =>
    api.get<ApiResponse<User[]>>('/users'),

  getAllUsers: () =>
    api.get<ApiResponse<User[]>>('/users/all'),

  createUser: (data: { name: string; email: string; password: string; role?: string; manager_id?: string }) =>
    api.post<ApiResponse<User>>('/users', data),

  updateUser: (id: string, data: Record<string, unknown>) =>
    api.put<ApiResponse<User>>(`/users/${id}`, data),

  toggleUser: (id: string) =>
    api.patch<ApiResponse<User>>(`/users/${id}/toggle`),

  updateMyLanguage: (language: string) =>
    api.patch<ApiResponse<User>>('/users/me/language', { language }),
};
