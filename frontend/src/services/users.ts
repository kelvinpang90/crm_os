import api from './api';
import type { ApiResponse, User } from '@/types';

export const usersApi = {
  getUsers: () =>
    api.get<ApiResponse<User[]>>('/users'),

  updateMyLanguage: (language: string) =>
    api.patch<ApiResponse<User>>('/users/me/language', { language }),
};
