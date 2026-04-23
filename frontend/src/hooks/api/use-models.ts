import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { modelsApi } from '@/lib/api/models';
import type { ModelType, ModelStatus, TrainModelRequest } from '@/types/api';

export function useModels(params?: {
    model_type?: ModelType;
    status?: ModelStatus;
    page?: number;
    page_size?: number;
}) {
    return useQuery({
        queryKey: ['models', params],
        queryFn: () => modelsApi.list(params),
    });
}

export function useModel(modelId: string) {
    return useQuery({
        queryKey: ['models', modelId],
        queryFn: () => modelsApi.get(modelId),
        enabled: Boolean(modelId),
    });
}

export function useModelMetrics(modelId: string) {
    return useQuery({
        queryKey: ['models', modelId, 'metrics'],
        queryFn: () => modelsApi.getMetrics(modelId),
        enabled: Boolean(modelId),
    });
}

export function useTrainModel() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: TrainModelRequest) => modelsApi.train(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['models'] });
        },
    });
}

export function useDeployModel() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (modelId: string) => modelsApi.deploy(modelId),
        onSuccess: (_, modelId) => {
            queryClient.invalidateQueries({ queryKey: ['models'] });
            queryClient.invalidateQueries({ queryKey: ['models', modelId] });
        },
    });
}

export function useUndeployModel() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (modelId: string) => modelsApi.undeploy(modelId),
        onSuccess: (_, modelId) => {
            queryClient.invalidateQueries({ queryKey: ['models'] });
            queryClient.invalidateQueries({ queryKey: ['models', modelId] });
        },
    });
}

export function useDeleteModel() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (modelId: string) => modelsApi.delete(modelId),
        onSuccess: () => {
            // Invalidate the list of models
            queryClient.invalidateQueries({ queryKey: ['models'] });
        },
    });
}
