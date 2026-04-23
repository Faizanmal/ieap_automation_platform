import { apiClient } from './client';
import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  User,
  APIKey,
} from '@/types/api';

// Authentication API
export const authApi = {
  register: async (data: RegisterRequest): Promise<User> => {
    const response = await apiClient.post('/api/v1/auth/register', data);
    return response.data;
  },

  login: async (data: LoginRequest): Promise<TokenResponse> => {
    const response = await apiClient.post('/api/v1/auth/login', data);
    return response.data;
  },

  refresh: async (refreshToken: string): Promise<TokenResponse> => {
    const response = await apiClient.post('/api/v1/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  logout: async (): Promise<void> => {
    await apiClient.post('/api/v1/auth/logout');
  },

  me: async (): Promise<User> => {
    const response = await apiClient.get('/api/v1/auth/me');
    return response.data;
  },

  requestPasswordReset: async (email: string): Promise<{ message: string }> => {
    const response = await apiClient.post('/api/v1/auth/password/reset', { email });
    return response.data;
  },

  confirmPasswordReset: async (token: string, newPassword: string): Promise<{ message: string }> => {
    const response = await apiClient.post('/api/v1/auth/password/reset/confirm', {
      token,
      new_password: newPassword,
    });
    return response.data;
  },

  // API Keys
  listApiKeys: async (): Promise<APIKey[]> => {
    const response = await apiClient.get('/api/v1/auth/api-keys');
    return response.data.api_keys;
  },

  createApiKey: async (data: {
    name: string;
    scopes?: string[];
    expires_in_days?: number;
  }): Promise<APIKey> => {
    const response = await apiClient.post('/api/v1/auth/api-keys', data);
    return response.data;
  },

  deleteApiKey: async (keyId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/auth/api-keys/${keyId}`);
  },
};
