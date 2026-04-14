import api from './api';
import type { ApiResponse, Contact, ContactStatus } from '@/types';

export interface PipelineStageContact {
  id: string;
  name: string;
  company: string | null;
  industry: string | null;
  deal_value: number;
  priority: string;
  status: string;
  updated_at: string | null;
}

export interface PipelineStage {
  status: string;
  count: number;
  total_value: number;
  contacts: PipelineStageContact[];
}

export interface PipelineData {
  stages: PipelineStage[];
}

export const pipelineApi = {
  getPipeline: () =>
    api.get<ApiResponse<PipelineData>>('/pipeline'),

  updateContactStatus: (id: string, status: ContactStatus) =>
    api.put<ApiResponse<Contact>>(`/contacts/${id}`, { status }),
};
