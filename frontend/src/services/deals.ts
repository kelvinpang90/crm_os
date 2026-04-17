import api from './api';
import type { ApiResponse, Activity, Deal, DealStatus } from '@/types';

export interface DealCreateParams {
  contact_id: string;
  title?: string;
  status?: DealStatus;
  priority?: string;
  amount?: number;
  assigned_to?: string;
}

export interface DealUpdateParams {
  title?: string;
  status?: DealStatus;
  priority?: string;
  amount?: number;
  assigned_to?: string;
}

export const dealsApi = {
  getDeals: (contactId?: string) =>
    api.get<ApiResponse<Deal[]>>('/deals', { params: contactId ? { contact_id: contactId } : {} }),

  createDeal: (data: DealCreateParams) =>
    api.post<ApiResponse<Deal>>('/deals', data),

  updateDeal: (id: string, data: DealUpdateParams) =>
    api.put<ApiResponse<Deal>>(`/deals/${id}`, data),

  deleteDeal: (id: string) =>
    api.delete<ApiResponse<null>>(`/deals/${id}`),

  getActivities: (dealId: string) =>
    api.get<ApiResponse<Activity[]>>(`/deals/${dealId}/activities`),

  createActivity: (dealId: string, data: { type: string; content?: string; follow_date?: string }) =>
    api.post<ApiResponse<Activity>>(`/deals/${dealId}/activities`, data),
};
