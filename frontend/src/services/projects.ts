// Data layer for the (self-contained) project tracking module.
// Talks to the backend project API (/api/projects). Response envelope is
// { success, data, message }; we return `res.data.data` so components get the
// domain object directly.
import api from './api';
import type { ApiResponse, Project, ProjectInput } from '@/types';

export const projectsApi = {
  getProjects: async (): Promise<Project[]> => {
    const res = await api.get<ApiResponse<Project[]>>('/projects');
    return res.data.data;
  },

  getProject: async (id: string): Promise<Project | undefined> => {
    const res = await api.get<ApiResponse<Project>>(`/projects/${id}`);
    return res.data.data;
  },

  createProject: async (data: ProjectInput): Promise<Project> => {
    const res = await api.post<ApiResponse<Project>>('/projects', data);
    return res.data.data;
  },

  updateProject: async (id: string, data: Partial<ProjectInput>): Promise<Project> => {
    const res = await api.put<ApiResponse<Project>>(`/projects/${id}`, data);
    return res.data.data;
  },

  deleteProject: async (id: string): Promise<void> => {
    await api.delete<ApiResponse<null>>(`/projects/${id}`);
  },

  // `confirmation` is only required by the backend when this advance lands on
  // step 12 (warranty_active) — see WarrantyConfirmModal.
  advanceStep: async (
    id: string,
    note: string | null = null,
    confirmation?: { satisfaction_score: number; customer_feedback?: string; signature_data: string }
  ): Promise<Project> => {
    const res = await api.post<ApiResponse<Project>>(`/projects/${id}/advance`, { note, ...confirmation });
    return res.data.data;
  },

  // Reset + reseed the demo data relative to now (handy before a demo).
  resetDemo: async (): Promise<void> => {
    await api.post<ApiResponse<{ seeded: number }>>('/projects/seed-demo');
  },
};
