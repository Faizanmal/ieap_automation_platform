"""
SDK Data Models

Pydantic models for the IEAP SDK with full type safety.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# ============================================================================
# Enums
# ============================================================================

class ModelStatus(str, Enum):
    READY = "ready"
    DEPLOYED = "deployed"
    TRAINING = "training"
    FAILED = "failed"
    ARCHIVED = "archived"


class PipelineStatus(str, Enum):
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    FAILED = "failed"


class DecisionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    EXECUTED = "executed"
    FAILED = "failed"
    ESCALATED = "escalated"


class PredictionType(str, Enum):
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    ANOMALY = "anomaly"
    FORECAST = "forecast"


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


# ============================================================================
# User Models
# ============================================================================

class User(BaseModel):
    """User model"""
    id: str
    email: str
    username: str
    is_active: bool = True
    is_verified: bool = False
    roles: list[str] = []
    created_at: datetime
    last_login: datetime | None = None


class TokenResponse(BaseModel):
    """Authentication token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class APIKey(BaseModel):
    """API key model"""
    id: str
    name: str
    key: str | None = None  # Only populated on creation
    scopes: list[str] = []
    is_active: bool = True
    created_at: datetime
    expires_at: datetime | None = None


# ============================================================================
# ML Model Models
# ============================================================================

class ModelMetrics(BaseModel):
    """Model performance metrics"""
    accuracy: float | None = None
    precision: float | None = None
    recall: float | None = None
    f1_score: float | None = None
    mse: float | None = None
    mae: float | None = None
    latency_p50_ms: float | None = None
    latency_p99_ms: float | None = None
    predictions_total: int = 0


class MLModel(BaseModel):
    """ML model"""
    id: str
    name: str
    model_type: str
    version: str
    status: ModelStatus
    description: str | None = None
    features: list[str] = []
    metrics: ModelMetrics | None = None
    created_at: datetime
    deployed_at: datetime | None = None
    created_by: str | None = None


class ModelCreateRequest(BaseModel):
    """Request to create a model"""
    name: str = Field(min_length=3, max_length=100)
    model_type: str
    description: str | None = None
    features: list[str] = []


class ModelDeployRequest(BaseModel):
    """Request to deploy a model"""
    replicas: int = Field(default=1, ge=1, le=10)
    resources: dict[str, Any] | None = None
    canary_percentage: int | None = Field(default=None, ge=0, le=100)


# ============================================================================
# Prediction Models
# ============================================================================

class FeatureContribution(BaseModel):
    """Feature contribution to prediction"""
    feature: str
    value: Any
    contribution: float
    importance_rank: int


class PredictionExplanation(BaseModel):
    """Prediction explanation (SHAP-style)"""
    base_value: float
    prediction_value: float
    feature_contributions: list[FeatureContribution]
    top_features: list[str]


class PredictionResult(BaseModel):
    """Prediction result"""
    prediction: Any
    probability: float | None = None
    confidence: float | None = None
    label: str | None = None
    explanation: PredictionExplanation | None = None


class PredictionResponse(BaseModel):
    """Prediction API response"""
    request_id: str
    model_id: str
    model_version: str
    prediction_type: PredictionType
    result: PredictionResult
    latency_ms: float
    timestamp: datetime


class BatchPredictionResponse(BaseModel):
    """Batch prediction response"""
    request_id: str
    model_id: str
    model_version: str
    predictions: list[PredictionResult]
    total_instances: int
    successful: int
    failed: int
    latency_ms: float
    timestamp: datetime


class PredictionRequest(BaseModel):
    """Prediction request"""
    model_id: str
    features: dict[str, Any]
    include_explanation: bool = False


class BatchPredictionRequest(BaseModel):
    """Batch prediction request"""
    model_id: str
    instances: list[dict[str, Any]]
    include_explanations: bool = False


# ============================================================================
# Pipeline Models
# ============================================================================

class PipelineMetrics(BaseModel):
    """Pipeline metrics"""
    records_processed: int = 0
    records_failed: int = 0
    throughput_per_second: float = 0.0
    average_latency_ms: float = 0.0
    uptime_percentage: float = 100.0


class DataPipeline(BaseModel):
    """Data pipeline"""
    id: str
    name: str
    pipeline_type: str
    status: PipelineStatus
    schedule: str | None = None
    metrics: PipelineMetrics | None = None
    created_at: datetime
    last_run: datetime | None = None
    next_run: datetime | None = None


class PipelineRunResult(BaseModel):
    """Pipeline run result"""
    job_id: str
    pipeline_id: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    records_processed: int = 0
    errors: list[str] = []


# ============================================================================
# Decision Models
# ============================================================================

class DecisionOption(BaseModel):
    """Decision option"""
    id: str
    name: str
    description: str
    score: float
    risk_score: float
    cost: float
    expected_outcome: dict[str, Any] = {}


class Decision(BaseModel):
    """Autonomous decision"""
    id: str
    decision_type: str
    status: DecisionStatus
    confidence: float
    impact_level: str
    reasoning: str
    selected_option: DecisionOption | None = None
    options: list[DecisionOption] = []
    created_at: datetime
    executed_at: datetime | None = None


# ============================================================================
# Health Models
# ============================================================================

class ComponentHealth(BaseModel):
    """Component health status"""
    component: str
    status: HealthStatus
    latency_ms: float
    message: str | None = None
    details: dict[str, Any] = {}
    checked_at: datetime


class PlatformHealth(BaseModel):
    """Platform health"""
    status: HealthStatus
    version: str
    uptime_seconds: int
    components: list[ComponentHealth] = []


# ============================================================================
# Analytics Models
# ============================================================================

class DailyMetric(BaseModel):
    """Daily metric"""
    date: str
    value: int | float


class Analytics(BaseModel):
    """Platform analytics"""
    total_predictions: int
    total_decisions: int
    active_models: int
    active_pipelines: int
    active_users: int
    predictions_today: int
    decisions_today: int


# ============================================================================
# Pagination
# ============================================================================

class PaginatedResponse(BaseModel):
    """Paginated response wrapper"""
    items: list[Any]
    total: int
    page: int
    page_size: int
    pages: int
    has_next: bool
    has_prev: bool
