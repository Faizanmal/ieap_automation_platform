// API Types - Complete type definitions for all backend APIs

// ============ Authentication Types ============
export interface User {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
  is_verified: boolean;
  full_name?: string;
  roles: string[];
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
  remember?: boolean;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface APIKey {
  id: string;
  key?: string;
  name: string;
  scopes: string[];
  created_at: string;
  expires_at: string | null;
  last_used: string | null;
}

// ============ ML Models Types ============
export type ModelType =
  | 'anomaly_detection'
  | 'demand_forecasting'
  | 'churn_prediction'
  | 'fraud_detection'
  | 'sentiment_analysis'
  | 'price_optimization';

export type ModelStatus =
  | 'training'
  | 'ready'
  | 'deploying'
  | 'deployed'
  | 'failed'
  | 'deprecated'
  | 'active';

export interface ModelInfo {
  id: string;
  name: string;
  type: ModelType;
  version: string;
  status: ModelStatus;
  description: string | null;
  created_at: string;
  updated_at: string;
  metrics: Record<string, number>;
  config: Record<string, unknown>;
  accuracy?: number;
}

export interface ModelListResponse {
  models: ModelInfo[];
  total: number;
}

export interface TrainModelRequest {
  model_type: ModelType;
  name: string;
  config?: Record<string, unknown>;
  data_source?: string;
}

export interface TrainModelResponse {
  model_id: string;
  status: ModelStatus;
  message: string;
  estimated_time_minutes: number | null;
}

export interface ModelMetrics {
  model_id: string;
  accuracy: number | null;
  precision: number | null;
  recall: number | null;
  f1_score: number | null;
  auc_roc: number | null;
  mse: number | null;
  mae: number | null;
  r2_score: number | null;
  confusion_matrix: number[][] | null;
  feature_importance: Record<string, number>;
  training_time_seconds: number | null;
  last_evaluated: string;
}

// ============ Predictions Types ============
export interface PredictionRequest {
  model_id: string;
  features: Record<string, unknown>;
  include_explanation?: boolean;
}

export interface BatchPredictionRequest {
  model_id: string;
  instances: Record<string, unknown>[];
  include_explanations?: boolean;
}

export interface PredictionResult {
  prediction: unknown;
  probability: number | null;
  confidence: number | null;
  label: string | null;
}

export interface PredictionExplanation {
  feature_contributions: Record<string, number>;
  base_value: number;
  prediction_value: number;
}

export interface PredictionResponse {
  request_id: string;
  model_id: string;
  model_version: string;
  prediction: PredictionResult;
  explanation: PredictionExplanation | null;
  latency_ms: number;
  timestamp: string;
}

export interface BatchPredictionResponse {
  request_id: string;
  model_id: string;
  model_version: string;
  predictions: PredictionResult[];
  explanations: PredictionExplanation[] | null;
  total_instances: number;
  successful: number;
  failed: number;
  latency_ms: number;
  timestamp: string;
}

export interface AnomalyDetectionRequest {
  features: Record<string, unknown>;
  threshold?: number;
}

export interface AnomalyDetectionResponse {
  is_anomaly: boolean;
  anomaly_score: number;
  threshold: number;
  feature_contributions: Record<string, number>;
  recommendation: string;
}

export interface ForecastRequest {
  target?: string;
  periods?: number;
  frequency?: string;
  include_confidence?: boolean;
}

export interface ForecastResponse {
  target: string;
  forecasts: Array<{
    date: string;
    forecast: number;
    lower_bound?: number;
    upper_bound?: number;
  }>;
  model_used: string;
  confidence_level: number;
}

export interface ChurnPredictionRequest {
  customer_id: string;
  tenure_months?: number;
  monthly_charges?: number;
  total_charges?: number;
  contract_type?: string;
  payment_method?: string;
  num_support_tickets?: number;
  additional_features?: Record<string, unknown>;
}

export interface ChurnPredictionResponse {
  customer_id: string;
  churn_probability: number;
  churn_risk: 'low' | 'medium' | 'high';
  will_churn?: boolean;
  top_risk_factors: Array<{ factor: string; impact: number }>;
  risk_factors?: Record<string, unknown>;
  recommended_actions: string[];
  retention_score: number;
}

// ============ Data Pipelines Types ============
export type PipelineStatus = 'idle' | 'running' | 'paused' | 'failed' | 'completed';
export type DataSourceType = 'api' | 'database' | 'file' | 'stream' | 's3' | 'kafka';

export interface PipelineInfo {
  id: string;
  name: string;
  description: string | null;
  status: PipelineStatus;
  source_type: DataSourceType;
  schedule: string | null;
  last_run: string | null;
  next_run: string | null;
  created_at: string;
  updated_at: string;
  config: Record<string, unknown>;
  records_processed?: number;
}

export interface PipelineListResponse {
  pipelines: PipelineInfo[];
  total: number;
}

export interface CreatePipelineRequest {
  name: string;
  description?: string;
  source_type: DataSourceType;
  source_config: Record<string, unknown>;
  destination_config: Record<string, unknown>;
  transformations?: Array<Record<string, unknown>>;
  schedule?: string;
}

export interface PipelineMetrics {
  pipeline_id: string;
  records_processed: number;
  records_failed: number;
  throughput_per_second: number;
  avg_latency_ms: number;
  error_rate: number;
  uptime_percentage: number;
  last_updated: string;
}

export interface PipelineRunResponse {
  pipeline_id: string;
  run_id: string;
  status: PipelineStatus;
  message: string;
}

// ============ Decision Engine Types ============
export type DecisionStatus = 'pending' | 'approved' | 'rejected' | 'executed' | 'failed';
export type DecisionImpact = 'low' | 'medium' | 'high' | 'critical';

export interface Decision {
  id: string;
  title: string;
  description: string;
  domain: string;
  status: DecisionStatus;
  impact: DecisionImpact;
  confidence: number;
  reasoning: string;
  options: Array<{ name: string; cost: number; benefit: number }>;
  selected_option: { name: string; cost: number; benefit: number } | null;
  cost_estimate: number;
  expected_benefit: number;
  created_at: string;
  decided_at: string | null;
  executed_at: string | null;
  requires_approval: boolean;
  type?: string;
  priority?: string;
  context?: Record<string, unknown>;
  rejection_reason?: string;
}

export interface DecisionListResponse {
  decisions: Decision[];
  total: number;
  pending_count: number;
}

export interface DecisionAnalytics {
  total_decisions: number;
  by_status: Record<string, number>;
  by_domain: Record<string, number>;
  average_confidence: number;
  total_cost_savings: number;
}

// ============ Task Orchestrator Types ============
export type TaskStatus = 'pending' | 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
export type TaskPriority = 'low' | 'medium' | 'high' | 'critical';
export type AgentStatus = 'idle' | 'busy' | 'offline' | 'active';

export interface Task {
  id: string;
  name: string;
  type: string;
  status: TaskStatus;
  priority: TaskPriority;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  assigned_agent: string | null;
  result: Record<string, unknown> | null;
  error: string | null;
  task_type?: string;
  progress?: number;
  description?: string;
}

export interface TaskListResponse {
  tasks: Task[];
  total: number;
}

export interface CreateTaskRequest {
  name: string;
  type: string;
  priority?: TaskPriority;
  payload?: Record<string, unknown>;
}

export interface Agent {
  id: string;
  name: string;
  type?: string;
  status: AgentStatus;
  capabilities: string[];
  current_task: string | null;
  tasks_completed: number;
  performance_score: number;
  success_rate?: number;
}

export interface AgentListResponse {
  agents: Agent[];
  total: number;
}

export interface OrchestratorMetrics {
  active_agents: number;
  busy_agents: number;
  pending_tasks: number;
  running_tasks: number;
  completed_today: number;
  average_performance: number;
}

// ============ Analytics Types ============
export interface KPI {
  name: string;
  value: number;
  unit: string;
  change: number;
  trend: 'up' | 'down' | 'stable';
}

export interface DashboardData {
  kpis: KPI[];
  charts: {
    revenue_trend: { labels: string[]; values: number[] };
    predictions_by_model: Record<string, number>;
    agent_utilization: Record<string, number>;
  };
  last_updated: string;
}

export interface Report {
  id: string;
  name: string;
  type: string;
  frequency: string;
}

export interface ReportData {
  id: string;
  name: string;
  generated_at: string;
  data: {
    summary: string;
    metrics: Record<string, number>;
  };
}

export interface SystemMetrics {
  period?: string;
  api_requests: { total: number; success_rate: number };
  predictions: { total: number; avg_latency_ms: number };
  pipelines: { active: number; records_processed: number };
  decisions: { total: number; autonomous: number; manual: number };
}

// ============ Health Types ============
export type HealthStatus = 'healthy' | 'degraded' | 'unhealthy';

export interface ComponentHealth {
  name: string;
  status: HealthStatus;
  response_time_ms: number | null;
  message: string | null;
  details: Record<string, unknown> | null;
}

export interface HealthResponse {
  status: HealthStatus;
  timestamp: string;
  version: string;
  uptime_seconds: number;
  components: ComponentHealth[];
}

// ============ Webhooks Types ============
export type WebhookEvent =
  | 'model.trained'
  | 'model.deployed'
  | 'prediction.made'
  | 'anomaly.detected'
  | 'decision.made'
  | 'pipeline.completed'
  | 'pipeline.failed'
  | 'task.completed';

export type WebhookStatus = 'active' | 'inactive' | 'failed';

export interface Webhook {
  id: string;
  name: string;
  url: string;
  events: WebhookEvent[];
  status: WebhookStatus;
  secret: string | null;
  created_at: string;
  last_triggered: string | null;
  last_delivery?: string;
  last_delivery_success?: boolean;
  success_count: number;
  failure_count: number;
}

export interface WebhookListResponse {
  webhooks: Webhook[];
  total: number;
}

export interface CreateWebhookRequest {
  name: string;
  url: string;
  events: WebhookEvent[];
}

export interface WebhookDelivery {
  id: string;
  webhook_id: string;
  event: WebhookEvent;
  payload: Record<string, unknown>;
  response_code: number;
  delivered_at: string;
  success: boolean;
}

// ============ Admin Types ============
export interface AdminDashboard {
  status: string;
  components: ComponentHealth[];
  metrics: {
    total_requests: number;
    requests_per_minute: number;
    error_rate: number;
    avg_latency_ms: number;
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
    uptime_seconds: number;
  };
  alerts: Array<Record<string, unknown>>;
  recent_events: Array<Record<string, unknown>>;
  quick_stats: Record<string, unknown>;
}

export interface SystemInfo {
  version: string;
  environment: string;
  uptime: number;
  python_version: string;
  dependencies: Record<string, string>;
}

// ============ WebSocket Types ============
export type WSMessageType =
  | 'connected'
  | 'disconnected'
  | 'error'
  | 'ping'
  | 'pong'
  | 'subscribe'
  | 'unsubscribe'
  | 'subscribed'
  | 'unsubscribed'
  | 'prediction'
  | 'decision'
  | 'alert'
  | 'metric'
  | 'notification'
  | 'pipeline_update'
  | 'model_update'
  | 'health_update';

export type WSChannel =
  | 'predictions'
  | 'decisions'
  | 'alerts'
  | 'metrics'
  | 'notifications'
  | 'pipelines'
  | 'models'
  | 'health'
  | 'all';

export interface WSMessage {
  type: WSMessageType;
  channel: WSChannel | null;
  data: Record<string, unknown>;
  timestamp: string;
  message_id: string;
}
