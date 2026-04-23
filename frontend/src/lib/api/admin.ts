import { apiClient } from './client';
import type { AdminDashboard } from '@/types/api';

// Types for admin
export interface AdminUser {
  id: string;
  email: string;
  username: string;
  role: string;
  is_active: boolean;
  created_at: string;
  last_login: string;
}

export interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  user_id: string;
  created_at: string;
  last_used: string;
  is_revoked: boolean;
  scopes: string[];
}

export interface AuditLog {
  id: string;
  user_id: string;
  event_type: string;
  action: string;
  resource: string;
  timestamp: string;
  details: Record<string, unknown>;
}

export interface Backup {
  backup_id: string;
  type: string;
  size_bytes: number;
  created_at: string;
  location: string;
  status: string;
}

export interface FeatureFlag {
  name: string;
  enabled: boolean;
  description?: string;
}

export interface ServiceStatus {
  name: string;
  status: 'healthy' | 'unhealthy' | 'degraded';
  uptime: number;
  last_check: string;
  details?: Record<string, unknown>;
}

// Admin API
export const adminApi = {
  // Dashboard
  getDashboard: async (): Promise<AdminDashboard> => {
    const response = await apiClient.get('/admin/dashboard');
    return response.data;
  },

  getSystemInfo: async (): Promise<Record<string, unknown>> => {
    const response = await apiClient.get('/admin/system/info');
    return response.data;
  },

  getSystemConfig: async (): Promise<Record<string, unknown>> => {
    const response = await apiClient.get('/admin/system/config');
    return response.data;
  },

  // Analytics
  getUsageAnalytics: async (timeRange?: string): Promise<Record<string, unknown>> => {
    const response = await apiClient.get('/admin/analytics/usage', {
      params: { time_range: timeRange },
    });
    return response.data;
  },

  getPerformanceAnalytics: async (timeRange?: string, metric?: string): Promise<Record<string, unknown>> => {
    const response = await apiClient.get('/admin/analytics/performance', {
      params: { time_range: timeRange, metric },
    });
    return response.data;
  },

  getErrorAnalytics: async (timeRange?: string): Promise<Record<string, unknown>> => {
    const response = await apiClient.get('/admin/analytics/errors', {
      params: { time_range: timeRange },
    });
    return response.data;
  },

  getUserAnalytics: async (timeRange?: string): Promise<Record<string, unknown>> => {
    const response = await apiClient.get('/admin/analytics/users', {
      params: { time_range: timeRange },
    });
    return response.data;
  },

  getModelAnalytics: async (timeRange?: string): Promise<Record<string, unknown>> => {
    const response = await apiClient.get('/admin/analytics/models', {
      params: { time_range: timeRange },
    });
    return response.data;
  },

  getResourceAnalytics: async (timeRange?: string): Promise<Record<string, unknown>> => {
    const response = await apiClient.get('/admin/analytics/resources', {
      params: { time_range: timeRange },
    });
    return response.data;
  },

  generateReport: async (timeRange?: string, sections?: string[]): Promise<Record<string, unknown>> => {
    const response = await apiClient.get('/admin/analytics/report', {
      params: { time_range: timeRange, sections: sections?.join(',') },
    });
    return response.data;
  },

  // User Management
  listUsers: async (params?: {
    page?: number;
    per_page?: number;
    search?: string;
    role?: string;
    active_only?: boolean;
  }): Promise<{ users: AdminUser[]; total: number; page: number; per_page: number }> => {
    const response = await apiClient.get('/admin/users', { params });
    return response.data;
  },

  getUser: async (userId: string): Promise<AdminUser> => {
    const response = await apiClient.get(`/admin/users/${userId}`);
    return response.data;
  },

  updateUser: async (userId: string, updates: Partial<AdminUser>): Promise<AdminUser> => {
    const response = await apiClient.put(`/admin/users/${userId}`, updates);
    return response.data;
  },

  deactivateUser: async (userId: string): Promise<{ success: boolean }> => {
    const response = await apiClient.post(`/admin/users/${userId}/deactivate`);
    return response.data;
  },

  // API Keys
  listApiKeys: async (userId?: string, includeRevoked?: boolean): Promise<ApiKey[]> => {
    const response = await apiClient.get('/admin/api-keys', {
      params: { user_id: userId, include_revoked: includeRevoked },
    });
    return response.data;
  },

  revokeApiKey: async (keyId: string): Promise<{ success: boolean }> => {
    const response = await apiClient.post(`/admin/api-keys/${keyId}/revoke`);
    return response.data;
  },

  // Audit Logs
  getAuditLogs: async (params?: {
    user_id?: string;
    event_type?: string;
    limit?: number;
  }): Promise<AuditLog[]> => {
    const response = await apiClient.get('/admin/audit-logs', { params });
    return response.data;
  },

  // Maintenance Mode
  getMaintenanceStatus: async (): Promise<{
    enabled: boolean;
    mode: string;
    message: string;
    enabled_at?: string;
  }> => {
    const response = await apiClient.get('/admin/maintenance');
    return response.data;
  },

  enableMaintenanceMode: async (data: {
    mode?: string;
    message?: string;
    notify_users?: boolean;
  }): Promise<{ message: string }> => {
    const response = await apiClient.post('/admin/maintenance/enable', data);
    return response.data;
  },

  disableMaintenanceMode: async (): Promise<{ message: string }> => {
    const response = await apiClient.post('/admin/maintenance/disable');
    return response.data;
  },

  // Cache Management
  getCacheStats: async (): Promise<{
    size: number;
    items: number;
    hit_rate: number;
    miss_rate: number;
  }> => {
    const response = await apiClient.get('/admin/cache/stats');
    return response.data;
  },

  clearCache: async (pattern?: string): Promise<{ message: string }> => {
    const response = await apiClient.post('/admin/cache/clear', { pattern, confirm: true });
    return response.data;
  },

  // Database Operations
  getDatabaseStats: async (): Promise<{
    size: string;
    tables: number;
    connections: number;
    slow_queries: number;
  }> => {
    const response = await apiClient.get('/admin/database/stats');
    return response.data;
  },

  runDatabaseVacuum: async (): Promise<{ message: string }> => {
    const response = await apiClient.post('/admin/database/vacuum');
    return response.data;
  },

  runMigrations: async (dryRun?: boolean): Promise<{ migrations: string[]; applied: number }> => {
    const response = await apiClient.post('/admin/database/migrations', null, {
      params: { dry_run: dryRun },
    });
    return response.data;
  },

  // Backup Management
  listBackups: async (limit?: number): Promise<Backup[]> => {
    const response = await apiClient.get('/admin/backups', { params: { limit } });
    return response.data;
  },

  createBackup: async (data: {
    backup_type?: string;
    include_logs?: boolean;
  }): Promise<Backup> => {
    const response = await apiClient.post('/admin/backups', data);
    return response.data;
  },

  restoreBackup: async (backupId: string): Promise<{ message: string; status: string }> => {
    const response = await apiClient.post('/admin/backups/restore', {
      backup_id: backupId,
      confirm: true,
    });
    return response.data;
  },

  // Feature Flags
  getFeatureFlags: async (): Promise<Record<string, boolean>> => {
    const response = await apiClient.get('/admin/feature-flags');
    return response.data;
  },

  updateFeatureFlag: async (flagName: string, enabled: boolean): Promise<{ message: string }> => {
    const response = await apiClient.put('/admin/feature-flags', {
      flag_name: flagName,
      enabled,
    });
    return response.data;
  },

  // Services
  getServicesStatus: async (): Promise<ServiceStatus[]> => {
    const response = await apiClient.get('/admin/services');
    return response.data;
  },

  getServiceStatus: async (serviceName: string): Promise<ServiceStatus> => {
    const response = await apiClient.get(`/admin/services/${serviceName}`);
    return response.data;
  },

  restartService: async (serviceName: string, graceful?: boolean): Promise<{ message: string }> => {
    const response = await apiClient.post(`/admin/services/${serviceName}/restart`, null, {
      params: { graceful },
    });
    return response.data;
  },

  // Operation Log
  getOperationLog: async (limit?: number): Promise<{
    id: string;
    action: string;
    user: string;
    timestamp: string;
    details: string;
  }[]> => {
    const response = await apiClient.get('/admin/operations/log', { params: { limit } });
    return response.data;
  },
};
