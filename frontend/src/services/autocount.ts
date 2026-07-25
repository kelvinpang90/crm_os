import api from './api';
import type { ApiResponse, AutocountDocument, AutocountSyncResult } from '@/types';

export const autocountApi = {
  syncNow: () =>
    api.post<ApiResponse<AutocountSyncResult>>('/autocount/sync'),

  getContactDocuments: (contactId: string) =>
    api.get<ApiResponse<AutocountDocument[]>>(`/contacts/${contactId}/autocount-documents`),
};
