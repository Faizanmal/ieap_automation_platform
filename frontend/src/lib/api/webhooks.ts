import { apiClient } from './client';
import type {
  Webhook,
  WebhookListResponse,
  CreateWebhookRequest,
  WebhookDelivery,
  WebhookEvent,
} from '@/types/api';

// Webhooks API
export const webhooksApi = {
  list: async (): Promise<WebhookListResponse> => {
    const response = await apiClient.get('/api/v1/webhooks');
    return response.data;
  },

  get: async (webhookId: string): Promise<Webhook> => {
    const response = await apiClient.get(`/api/v1/webhooks/${webhookId}`);
    return response.data;
  },

  create: async (data: CreateWebhookRequest): Promise<Webhook> => {
    const response = await apiClient.post('/api/v1/webhooks', data);
    return response.data;
  },

  delete: async (webhookId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/webhooks/${webhookId}`);
  },

  test: async (webhookId: string): Promise<{
    message: string;
    webhook_id: string;
    status: string;
    response_code: number;
  }> => {
    const response = await apiClient.post(`/api/v1/webhooks/${webhookId}/test`);
    return response.data;
  },

  getDeliveries: async (webhookId: string, limit?: number): Promise<{
    deliveries: WebhookDelivery[];
    total: number;
  }> => {
    const response = await apiClient.get(`/api/v1/webhooks/${webhookId}/deliveries`, {
      params: { limit },
    });
    return response.data;
  },

  listEvents: async (): Promise<{
    events: Array<{ name: WebhookEvent; description: string }>;
  }> => {
    const response = await apiClient.get('/api/v1/webhooks/events/available');
    return response.data;
  },
};
