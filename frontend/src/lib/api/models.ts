import { apiClient } from './client';
import type {
  ModelInfo,
  ModelListResponse,
  ModelMetrics,
  ModelType,
  ModelStatus,
  TrainModelRequest,
  TrainModelResponse,
} from '@/types/api';

// ML Models API
export const modelsApi = {
  list: async (params?: {
    model_type?: ModelType;
    status?: ModelStatus;
    page?: number;
    page_size?: number;
  }): Promise<ModelListResponse> => {
    const response = await apiClient.get('/api/v1/models', { params });
    return response.data;
  },

  get: async (modelId: string): Promise<ModelInfo> => {
    const response = await apiClient.get(`/api/v1/models/${modelId}`);
    return response.data;
  },

  train: async (data: TrainModelRequest): Promise<TrainModelResponse> => {
    const response = await apiClient.post('/api/v1/models/train', data);
    return response.data;
  },

  getMetrics: async (modelId: string): Promise<ModelMetrics> => {
    const response = await apiClient.get(`/api/v1/models/${modelId}/metrics`);
    return response.data;
  },

  deploy: async (modelId: string): Promise<{ message: string; status: string }> => {
    const response = await apiClient.post(`/api/v1/models/${modelId}/deploy`);
    return response.data;
  },

  undeploy: async (modelId: string): Promise<{ message: string }> => {
    const response = await apiClient.post(`/api/v1/models/${modelId}/undeploy`);
    return response.data;
  },

  delete: async (modelId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/models/${modelId}`);
  },
};
