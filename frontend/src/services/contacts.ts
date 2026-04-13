import api from './api';
import type { ApiResponse, PaginatedResponse, Contact, Activity } from '@/types';

export interface ContactListParams {
  search?: string;
  industry?: string;
  status?: string;
  priority?: string;
  assigned_to?: string;
  page?: number;
  page_size?: number;
  sort_by?: string;
  order?: string;
}

export const contactsApi = {
  getContacts: (params: ContactListParams) =>
    api.get<ApiResponse<PaginatedResponse<Contact>>>('/contacts', { params }),

  getContact: (id: string) =>
    api.get<ApiResponse<Contact>>(`/contacts/${id}`),

  createContact: (data: Partial<Contact>) =>
    api.post<ApiResponse<Contact>>('/contacts', data),

  updateContact: (id: string, data: Partial<Contact>) =>
    api.put<ApiResponse<Contact>>(`/contacts/${id}`, data),

  deleteContact: (id: string) =>
    api.delete<ApiResponse<null>>(`/contacts/${id}`),

  importContacts: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<ApiResponse<{
      total: number; inserted: number; updated: number; skipped: number;
      errors: Array<{ row: number; field: string; message: string }>;
    }>>('/contacts/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  downloadTemplate: () =>
    api.get('/contacts/import/template', { responseType: 'blob' }),

  getActivities: (contactId: string) =>
    api.get<ApiResponse<Activity[]>>(`/contacts/${contactId}/activities`),

  createActivity: (contactId: string, data: { type: string; content?: string; follow_date?: string }) =>
    api.post<ApiResponse<Activity>>(`/contacts/${contactId}/activities`, data),
};
