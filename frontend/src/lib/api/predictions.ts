import { apiClient } from './client';
import type {
  PredictionRequest,
  PredictionResponse,
  BatchPredictionRequest,
  BatchPredictionResponse,
  AnomalyDetectionRequest,
  AnomalyDetectionResponse,
  ForecastRequest,
  ForecastResponse,
  ChurnPredictionRequest,
  ChurnPredictionResponse,
} from '@/types/api';

// Predictions API
export const predictionsApi = {
  predict: async (data: PredictionRequest): Promise<PredictionResponse> => {
    const response = await apiClient.post('/api/v1/predictions', data);
    return response.data;
  },

  batchPredict: async (data: BatchPredictionRequest): Promise<BatchPredictionResponse> => {
    const response = await apiClient.post('/api/v1/predictions/batch', data);
    return response.data;
  },

  detectAnomaly: async (data: AnomalyDetectionRequest): Promise<AnomalyDetectionResponse> => {
    const response = await apiClient.post('/api/v1/predictions/anomaly', data);
    return response.data;
  },

  generateForecast: async (data: ForecastRequest): Promise<ForecastResponse> => {
    const response = await apiClient.post('/api/v1/predictions/forecast', data);
    return response.data;
  },

  predictChurn: async (data: ChurnPredictionRequest): Promise<ChurnPredictionResponse> => {
    const response = await apiClient.post('/api/v1/predictions/churn', data);
    return response.data;
  },
};
