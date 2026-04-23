import { apiClient } from './client';
import type {
  Decision,
  DecisionListResponse,
  DecisionStatus,
  DecisionAnalytics,
} from '@/types/api';

// Decision Engine API
export const decisionsApi = {
  list: async (params?: {
    status_filter?: DecisionStatus;
    domain?: string;
    page?: number;
    page_size?: number;
  }): Promise<DecisionListResponse> => {
    const response = await apiClient.get('/api/v1/decisions', { params });
    return response.data;
  },

  get: async (decisionId: string): Promise<Decision> => {
    const response = await apiClient.get(`/api/v1/decisions/${decisionId}`);
    return response.data;
  },

  approve: async (decisionId: string, comments?: string): Promise<{ message: string; decision: Decision }> => {
    const response = await apiClient.post(`/api/v1/decisions/${decisionId}/approve`, {
      comments,
    });
    return response.data;
  },

  reject: async (decisionId: string, reason: string): Promise<{ message: string; reason: string; decision: Decision }> => {
    const response = await apiClient.post(`/api/v1/decisions/${decisionId}/reject`, {
      reason,
    });
    return response.data;
  },

  getAnalytics: async (): Promise<DecisionAnalytics> => {
    const response = await apiClient.get('/api/v1/decisions/analytics/summary');
    return response.data;
  },
};
