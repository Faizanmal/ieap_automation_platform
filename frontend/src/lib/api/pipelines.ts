import { apiClient } from './client';
import type {
  PipelineInfo,
  PipelineListResponse,
  PipelineMetrics,
  PipelineStatus,
  DataSourceType,
  CreatePipelineRequest,
  PipelineRunResponse,
} from '@/types/api';

// Data Pipelines API
export const pipelinesApi = {
  list: async (params?: {
    status?: PipelineStatus;
    source_type?: DataSourceType;
  }): Promise<PipelineListResponse> => {
    const response = await apiClient.get('/api/v1/pipelines', { params });
    return response.data;
  },

  get: async (pipelineId: string): Promise<PipelineInfo> => {
    const response = await apiClient.get(`/api/v1/pipelines/${pipelineId}`);
    return response.data;
  },

  create: async (data: CreatePipelineRequest): Promise<PipelineInfo> => {
    const response = await apiClient.post('/api/v1/pipelines', data);
    return response.data;
  },

  run: async (pipelineId: string): Promise<PipelineRunResponse> => {
    const response = await apiClient.post(`/api/v1/pipelines/${pipelineId}/run`);
    return response.data;
  },

  stop: async (pipelineId: string): Promise<{ message: string; status: string }> => {
    const response = await apiClient.post(`/api/v1/pipelines/${pipelineId}/stop`);
    return response.data;
  },

  getMetrics: async (pipelineId: string): Promise<PipelineMetrics> => {
    const response = await apiClient.get(`/api/v1/pipelines/${pipelineId}/metrics`);
    return response.data;
  },

  delete: async (pipelineId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/pipelines/${pipelineId}`);
  },
};
