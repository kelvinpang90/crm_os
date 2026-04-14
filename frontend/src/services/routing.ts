import api from './api';
import type { ApiResponse, RoutingRule } from '@/types';

export interface RoutingRuleCreateData {
  name: string;
  strategy: string;
  conditions?: Record<string, unknown> | null;
  target_users: string[];
  priority?: number;
  is_active?: boolean;
}

export const routingApi = {
  getRules: () =>
    api.get<ApiResponse<RoutingRule[]>>('/routing/rules'),

  createRule: (data: RoutingRuleCreateData) =>
    api.post<ApiResponse<RoutingRule>>('/routing/rules', data),

  updateRule: (id: string, data: Partial<RoutingRuleCreateData>) =>
    api.put<ApiResponse<RoutingRule>>(`/routing/rules/${id}`, data),

  deleteRule: (id: string) =>
    api.delete<ApiResponse<null>>(`/routing/rules/${id}`),

  toggleRule: (id: string) =>
    api.patch<ApiResponse<RoutingRule>>(`/routing/rules/${id}/toggle`),

  reorderRules: (rules: { id: string; priority: number }[]) =>
    api.patch<ApiResponse<RoutingRule[]>>('/routing/rules/reorder', { rules }),
};
