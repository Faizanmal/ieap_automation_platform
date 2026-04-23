import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { webhooksApi } from '@/lib/api/webhooks';
import type { CreateWebhookRequest } from '@/types/api';

export function useWebhooks() {
    return useQuery({
        queryKey: ['webhooks'],
        queryFn: () => webhooksApi.list(),
    });
}

export function useWebhook(webhookId: string) {
    return useQuery({
        queryKey: ['webhooks', webhookId],
        queryFn: () => webhooksApi.get(webhookId),
        enabled: Boolean(webhookId),
    });
}

export function useCreateWebhook() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: CreateWebhookRequest) => webhooksApi.create(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['webhooks'] });
        },
    });
}

export function useDeleteWebhook() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (webhookId: string) => webhooksApi.delete(webhookId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['webhooks'] });
        },
    });
}

export function useTestWebhook() {
    return useMutation({
        mutationFn: (webhookId: string) => webhooksApi.test(webhookId),
    });
}

export function useWebhookDeliveries(webhookId: string, limit: number = 20) {
    return useQuery({
        queryKey: ['webhooks', webhookId, 'deliveries'],
        queryFn: () => webhooksApi.getDeliveries(webhookId, limit),
        enabled: Boolean(webhookId),
    });
}

export function useAvailableEvents() {
    return useQuery({
        queryKey: ['webhooks', 'events'],
        queryFn: () => webhooksApi.listEvents(),
    });
}
