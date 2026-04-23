import { apiClient } from './client';
import type { HealthResponse } from '@/types/api';

// Health API
export const healthApi = {
  check: async (): Promise<HealthResponse> => {
    const response = await apiClient.get('/api/v1/health');
    return response.data;
  },

  checkDetailed: async (): Promise<HealthResponse> => {
    const response = await apiClient.get('/api/v1/health/detailed');
    return response.data;
  },

  checkReadiness: async (): Promise<{ ready: boolean; reason?: string }> => {
    const response = await apiClient.get('/api/v1/health/ready');
    return response.data;
  },

  checkLiveness: async (): Promise<{ alive: boolean }> => {
    const response = await apiClient.get('/api/v1/health/live');
    return response.data;
  },

  checkComponent: async (componentName: string): Promise<{
    name: string;
    status: string;
    response_time_ms: number;
    details: Record<string, unknown>;
  }> => {
    const response = await apiClient.get(`/api/v1/health/components/${componentName}`);
    return response.data;
  },
};
