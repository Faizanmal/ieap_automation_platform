import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { decisionsApi } from '@/lib/api/decisions';
import type { DecisionStatus } from '@/types/api';

export function useDecisions(params?: {
    status?: DecisionStatus;
    domain?: string;
    page?: number;
    page_size?: number;
}) {
    return useQuery({
        queryKey: ['decisions', params],
        queryFn: () => decisionsApi.list(params),
    });
}

export function useDecision(decisionId: string) {
    return useQuery({
        queryKey: ['decisions', decisionId],
        queryFn: () => decisionsApi.get(decisionId),
        enabled: Boolean(decisionId),
    });
}

export function useApproveDecision() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ decisionId, comments }: { decisionId: string; comments?: string }) =>
            decisionsApi.approve(decisionId, comments),
        onSuccess: (_, { decisionId }) => {
            queryClient.invalidateQueries({ queryKey: ['decisions'] });
            queryClient.invalidateQueries({ queryKey: ['decisions', decisionId] });
        },
    });
}

export function useRejectDecision() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ decisionId, reason }: { decisionId: string; reason: string }) =>
            decisionsApi.reject(decisionId, reason),
        onSuccess: (_, { decisionId }) => {
            queryClient.invalidateQueries({ queryKey: ['decisions'] });
            queryClient.invalidateQueries({ queryKey: ['decisions', decisionId] });
        },
    });
}

export function useDecisionAnalytics() {
    return useQuery({
        queryKey: ['decisions', 'analytics'],
        queryFn: () => decisionsApi.getAnalytics(),
    });
}
