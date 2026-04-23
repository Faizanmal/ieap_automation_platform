import { apiClient } from './client';
import type {
  DashboardData,
  Report,
  ReportData,
  SystemMetrics,
} from '@/types/api';

// Analytics API
export const analyticsApi = {
  getDashboard: async (): Promise<DashboardData> => {
    const response = await apiClient.get('/api/v1/analytics/dashboard');
    return response.data;
  },

  listReports: async (): Promise<{ reports: Report[] }> => {
    const response = await apiClient.get('/api/v1/analytics/reports');
    return response.data;
  },

  getReport: async (reportId: string): Promise<ReportData> => {
    const response = await apiClient.get(`/api/v1/analytics/reports/${reportId}`);
    return response.data;
  },

  getMetrics: async (period?: string): Promise<SystemMetrics> => {
    const response = await apiClient.get('/api/v1/analytics/metrics', {
      params: { period },
    });
    return response.data;
  },
};
