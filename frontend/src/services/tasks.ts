import api from './api';
import type { ApiResponse, PaginatedResponse, Task } from '@/types';

export interface TaskListParams {
  status?: string;
  priority?: string;
  assigned_to?: string;
  due_before?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export const tasksApi = {
  getTasks: (params: TaskListParams) =>
    api.get<ApiResponse<PaginatedResponse<Task>>>('/tasks', { params }),

  getTask: (id: string) =>
    api.get<ApiResponse<Task>>(`/tasks/${id}`),

  createTask: (data: Partial<Task>) =>
    api.post<ApiResponse<Task>>('/tasks', data),

  updateTask: (id: string, data: Partial<Task>) =>
    api.put<ApiResponse<Task>>(`/tasks/${id}`, data),

  toggleTask: (id: string) =>
    api.patch<ApiResponse<Task>>(`/tasks/${id}/toggle`),

  deleteTask: (id: string) =>
    api.delete<ApiResponse<null>>(`/tasks/${id}`),
};
