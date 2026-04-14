import api from './api';
import type { ApiResponse } from '@/types';

export interface AnalyticsOverview {
  total_contacts: number;
  total_won: number;
  total_lost: number;
  overall_conversion_rate: number;
  total_deal_amount: number;
  avg_deal_value: number;
}

export interface ConversionPoint {
  date: string;
  total: number;
  won: number;
  rate: number;
}

export interface ChannelDistribution {
  channel: string;
  count: number;
  percentage: number;
}

export interface SalesRanking {
  user_id: string;
  user_name: string;
  deal_count: number;
  deal_amount: number;
  conversion_rate: number;
}

export interface AnalyticsDashboard {
  overview: AnalyticsOverview;
  conversion_trend: ConversionPoint[];
  channel_distribution: ChannelDistribution[];
  sales_ranking: SalesRanking[];
}

export interface SalesTargetItem {
  id: string;
  user_id: string;
  user_name: string | null;
  year: number;
  month: number;
  target_amount: number;
  target_count: number;
  created_at: string;
  updated_at: string;
}

export const analyticsApi = {
  getAnalytics: (days = 90) =>
    api.get<ApiResponse<AnalyticsDashboard>>('/analytics', { params: { days } }),
};

export const salesTargetsApi = {
  getTargets: (params?: { year?: number; user_id?: string }) =>
    api.get<ApiResponse<SalesTargetItem[]>>('/sales-targets', { params }),

  createTarget: (data: { user_id: string; year: number; month: number; target_amount: number; target_count: number }) =>
    api.post<ApiResponse<SalesTargetItem>>('/sales-targets', data),

  updateTarget: (id: string, data: { target_amount?: number; target_count?: number }) =>
    api.put<ApiResponse<SalesTargetItem>>(`/sales-targets/${id}`, data),

  deleteTarget: (id: string) =>
    api.delete<ApiResponse<null>>(`/sales-targets/${id}`),
};
