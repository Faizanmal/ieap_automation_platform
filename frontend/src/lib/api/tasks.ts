import { apiClient } from './client';
import type {
  Task,
  TaskListResponse,
  TaskStatus,
  TaskPriority,
  CreateTaskRequest,
  Agent,
  AgentListResponse,
  OrchestratorMetrics,
} from '@/types/api';

// Task Orchestrator API
export const tasksApi = {
  list: async (params?: {
    status_filter?: TaskStatus;
    priority?: TaskPriority;
    limit?: number;
  }): Promise<TaskListResponse> => {
    const response = await apiClient.get('/api/v1/tasks', { params });
    return response.data;
  },

  get: async (taskId: string): Promise<Task> => {
    const response = await apiClient.get(`/api/v1/tasks/${taskId}`);
    return response.data;
  },

  create: async (data: CreateTaskRequest): Promise<Task> => {
    const response = await apiClient.post('/api/v1/tasks', data);
    return response.data;
  },

  cancel: async (taskId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/tasks/${taskId}`);
  },

  // Agents
  listAgents: async (): Promise<AgentListResponse> => {
    const response = await apiClient.get('/api/v1/tasks/agents/list');
    return response.data;
  },

  getAgent: async (agentId: string): Promise<Agent> => {
    const response = await apiClient.get(`/api/v1/tasks/agents/${agentId}`);
    return response.data;
  },

  // Metrics
  getMetrics: async (): Promise<OrchestratorMetrics> => {
    const response = await apiClient.get('/api/v1/tasks/metrics/summary');
    return response.data;
  },
};
