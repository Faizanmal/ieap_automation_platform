import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { pipelinesApi } from '@/lib/api/pipelines';
import type { CreatePipelineRequest, PipelineStatus, DataSourceType } from '@/types/api';

export function usePipelines(params?: {
    status?: PipelineStatus;
    source_type?: DataSourceType;
}) {
    return useQuery({
        queryKey: ['pipelines', params],
        queryFn: () => pipelinesApi.list(params),
    });
}

export function usePipeline(pipelineId: string) {
    return useQuery({
        queryKey: ['pipelines', pipelineId],
        queryFn: () => pipelinesApi.get(pipelineId),
        enabled: Boolean(pipelineId),
    });
}

export function useCreatePipeline() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: CreatePipelineRequest) => pipelinesApi.create(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['pipelines'] });
        },
    });
}

export function useRunPipeline() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (pipelineId: string) => pipelinesApi.run(pipelineId),
        onSuccess: (_, pipelineId) => {
            queryClient.invalidateQueries({ queryKey: ['pipelines'] });
            queryClient.invalidateQueries({ queryKey: ['pipelines', pipelineId] });
        },
    });
}

export function useStopPipeline() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (pipelineId: string) => pipelinesApi.stop(pipelineId),
        onSuccess: (_, pipelineId) => {
            queryClient.invalidateQueries({ queryKey: ['pipelines'] });
            queryClient.invalidateQueries({ queryKey: ['pipelines', pipelineId] });
        },
    });
}

export function usePipelineMetrics(pipelineId: string) {
    return useQuery({
        queryKey: ['pipelines', pipelineId, 'metrics'],
        queryFn: () => pipelinesApi.getMetrics(pipelineId),
        enabled: Boolean(pipelineId),
    });
}

export function useDeletePipeline() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (pipelineId: string) => pipelinesApi.delete(pipelineId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['pipelines'] });
        },
    });
}
