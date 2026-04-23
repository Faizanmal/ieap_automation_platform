import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { tasksApi } from '@/lib/api/tasks';
import type { CreateTaskRequest, TaskPriority, TaskStatus } from '@/types/api';

export function useTasks(params?: {
    status?: TaskStatus;
    priority?: TaskPriority;
    limit?: number;
}) {
    return useQuery({
        queryKey: ['tasks', params],
        queryFn: () => tasksApi.list(params),
    });
}

export function useTask(taskId: string) {
    return useQuery({
        queryKey: ['tasks', taskId],
        queryFn: () => tasksApi.get(taskId),
        enabled: Boolean(taskId),
    });
}

export function useCreateTask() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: CreateTaskRequest) => tasksApi.create(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['tasks'] });
        },
    });
}

export function useCancelTask() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (taskId: string) => tasksApi.cancel(taskId),
        onSuccess: (_, taskId) => {
            queryClient.invalidateQueries({ queryKey: ['tasks'] });
            queryClient.invalidateQueries({ queryKey: ['tasks', taskId] });
        },
    });
}

export function useAgents() {
    return useQuery({
        queryKey: ['agents'],
        queryFn: () => tasksApi.listAgents(),
    });
}

export function useAgent(agentId: string) {
    return useQuery({
        queryKey: ['agents', agentId],
        queryFn: () => tasksApi.getAgent(agentId),
        enabled: Boolean(agentId),
    });
}

export function useOrchestratorMetrics() {
    return useQuery({
        queryKey: ['orchestrator', 'metrics'],
        queryFn: () => tasksApi.getMetrics(),
    });
}
