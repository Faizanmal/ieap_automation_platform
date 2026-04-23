import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '@/lib/stores';

// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create axios instance
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - Add auth token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = useAuthStore.getState().accessToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - Handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    
    // Handle 401 Unauthorized
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      const refreshToken = useAuthStore.getState().refreshToken;
      
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken,
          });
          
          const { access_token, refresh_token } = response.data;
          useAuthStore.getState().setTokens(access_token, refresh_token);
          
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return apiClient(originalRequest);
        } catch (refreshError) {
          useAuthStore.getState().logout();
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      } else {
        useAuthStore.getState().logout();
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

// API Error helper
export interface ApiError {
  message: string;
  error_code: string;
  details?: Record<string, unknown>;
  status_code: number;
}

export function getApiError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const response = error.response?.data;
    return {
      message: response?.detail || response?.message || error.message || 'An error occurred',
      error_code: response?.error_code || 'UNKNOWN_ERROR',
      details: response?.details,
      status_code: error.response?.status || 500,
    };
  }
  return {
    message: error instanceof Error ? error.message : 'An unknown error occurred',
    error_code: 'UNKNOWN_ERROR',
    status_code: 500,
  };
}
