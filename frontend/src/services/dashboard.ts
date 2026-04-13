import api from './api';
import type { ApiResponse } from '@/types';

export interface KpiItem {
  key: string;
  value: number;
  change?: number | null;
}

export interface FunnelStage {
  stage: string;
  count: number;
  amount: number;
}

export interface PipelineStage {
  stage: string;
  count: number;
  amount: number;
  last_updated: string | null;
}

export interface LeaderboardEntry {
  rank: number;
  user_id: string;
  user_name: string;
  avatar_url: string | null;
  deal_amount: number;
  deal_count: number;
  win_rate: number;
}

export interface GmvTrendPoint {
  label: string;
  gmv: number;
}

export const dashboardApi = {
  getAdmin: () =>
    api.get<ApiResponse<{ kpis: KpiItem[]; funnel: FunnelStage[] }>>('/dashboard/admin'),

  getManager: () =>
    api.get<ApiResponse<{ kpis: KpiItem[]; funnel: FunnelStage[] }>>('/dashboard/manager'),

  getSales: () =>
    api.get<ApiResponse<{ kpis: KpiItem[]; pipeline: PipelineStage[] }>>('/dashboard/sales'),

  getLeaderboard: (month: string) =>
    api.get<ApiResponse<{ month: string; entries: LeaderboardEntry[] }>>('/dashboard/leaderboard', { params: { month } }),

  getTeamLeaderboard: (month: string) =>
    api.get<ApiResponse<{ month: string; entries: LeaderboardEntry[] }>>('/dashboard/team-leaderboard', { params: { month } }),

  getGmvTrend: (period: 'month' | 'year') =>
    api.get<ApiResponse<{ period: string; data: GmvTrendPoint[] }>>('/dashboard/gmv-trend', { params: { period } }),
};
