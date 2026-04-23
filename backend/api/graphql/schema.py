"""
GraphQL Schema Definition

Comprehensive GraphQL schema for the IEAP platform using Strawberry.
"""

import asyncio
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import strawberry
from strawberry.types import Info

# ============================================================================
# Enums
# ============================================================================

@strawberry.enum
class ModelStatus(Enum):
    READY = "ready"
    DEPLOYED = "deployed"
    TRAINING = "training"
    FAILED = "failed"
    ARCHIVED = "archived"


@strawberry.enum
class PipelineStatus(Enum):
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    FAILED = "failed"


@strawberry.enum
class DecisionStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    EXECUTED = "executed"
    FAILED = "failed"
    ESCALATED = "escalated"


@strawberry.enum
class PredictionType(Enum):
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    ANOMALY = "anomaly"
    FORECAST = "forecast"


# ============================================================================
# Types
# ============================================================================

@strawberry.type
class User:
    """Platform user"""
    id: str
    email: str
    username: str
    is_active: bool
    is_verified: bool
    roles: list[str]
    created_at: datetime
    last_login: datetime | None

    @strawberry.field
    async def api_keys(self) -> list["APIKey"]:
        """User's API keys"""
        return [
            APIKey(
                id=str(uuid.uuid4()),
                name="Production Key",
                scopes=["read", "write"],
                is_active=True,
                created_at=datetime.now()
            )
        ]

    @strawberry.field
    async def predictions_count(self) -> int:
        """Total predictions made by user"""
        return 1547


@strawberry.type
class APIKey:
    """API access key"""
    id: str
    name: str
    scopes: list[str]
    is_active: bool
    created_at: datetime
    expires_at: datetime | None = None
    last_used: datetime | None = None


@strawberry.type
class MLModel:
    """Machine learning model"""
    id: str
    name: str
    model_type: str
    version: str
    status: ModelStatus
    description: str | None
    created_at: datetime
    deployed_at: datetime | None

    @strawberry.field
    async def metrics(self) -> "ModelMetrics":
        """Model performance metrics"""
        return ModelMetrics(
            accuracy=0.94,
            precision=0.92,
            recall=0.95,
            f1_score=0.93,
            latency_p50_ms=23.5,
            latency_p99_ms=87.2,
            predictions_total=125847
        )

    @strawberry.field
    async def features(self) -> list[str]:
        """Model input features"""
        return ["feature_1", "feature_2", "feature_3"]


@strawberry.type
class ModelMetrics:
    """Model performance metrics"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    latency_p50_ms: float
    latency_p99_ms: float
    predictions_total: int


@strawberry.type
class Prediction:
    """Prediction result"""
    id: str
    model_id: str
    model_name: str
    prediction_type: PredictionType
    input_data: strawberry.Private[dict[str, Any]]
    result: float
    confidence: float
    label: str | None
    created_at: datetime
    latency_ms: float

    @strawberry.field
    async def explanation(self) -> Optional["PredictionExplanation"]:
        """Get prediction explanation"""
        return PredictionExplanation(
            base_value=0.5,
            prediction_value=0.85,
            feature_contributions=[
                FeatureContribution(feature="monthly_charges", contribution=0.25),
                FeatureContribution(feature="tenure", contribution=-0.15),
            ]
        )


@strawberry.type
class FeatureContribution:
    """Feature contribution to prediction"""
    feature: str
    contribution: float


@strawberry.type
class PredictionExplanation:
    """SHAP-style prediction explanation"""
    base_value: float
    prediction_value: float
    feature_contributions: list[FeatureContribution]


@strawberry.type
class DataPipeline:
    """Data processing pipeline"""
    id: str
    name: str
    pipeline_type: str
    status: PipelineStatus
    created_at: datetime
    last_run: datetime | None
    next_run: datetime | None

    @strawberry.field
    async def metrics(self) -> "PipelineMetrics":
        """Pipeline performance metrics"""
        return PipelineMetrics(
            records_processed=1250000,
            records_failed=127,
            throughput_per_second=1200.5,
            average_latency_ms=45.2,
            uptime_percentage=99.95
        )


@strawberry.type
class PipelineMetrics:
    """Pipeline performance metrics"""
    records_processed: int
    records_failed: int
    throughput_per_second: float
    average_latency_ms: float
    uptime_percentage: float


@strawberry.type
class Decision:
    """Autonomous decision"""
    id: str
    decision_type: str
    status: DecisionStatus
    confidence: float
    impact_level: str
    reasoning: str
    created_at: datetime
    executed_at: datetime | None

    @strawberry.field
    async def options(self) -> list["DecisionOption"]:
        """Available decision options"""
        return [
            DecisionOption(
                id="opt_1",
                name="Option A",
                score=0.85,
                risk_score=0.15,
                cost=1500.0
            )
        ]


@strawberry.type
class DecisionOption:
    """Decision option"""
    id: str
    name: str
    score: float
    risk_score: float
    cost: float


@strawberry.type
class HealthCheck:
    """Component health status"""
    component: str
    status: str
    latency_ms: float
    message: str | None
    checked_at: datetime


@strawberry.type
class PlatformHealth:
    """Overall platform health"""
    status: str
    version: str
    uptime_seconds: int
    components: list[HealthCheck]


@strawberry.type
class Analytics:
    """Platform analytics"""
    total_predictions: int
    total_decisions: int
    active_models: int
    active_pipelines: int
    active_users: int

    @strawberry.field
    async def predictions_by_day(self, days: int = 7) -> list["DailyMetric"]:
        """Predictions over time"""
        return [
            DailyMetric(date=datetime.now().date().isoformat(), value=1500 + i * 100)
            for i in range(days)
        ]


@strawberry.type
class DailyMetric:
    """Daily metric value"""
    date: str
    value: int


# ============================================================================
# Input Types
# ============================================================================

@strawberry.input
class PredictionInput:
    """Input for making predictions"""
    model_id: str
    features: strawberry.scalars.JSON
    include_explanation: bool = False


@strawberry.input
class CreateModelInput:
    """Input for creating a model"""
    name: str
    model_type: str
    description: str | None = None


@strawberry.input
class PipelineRunInput:
    """Input for running a pipeline"""
    pipeline_id: str
    parameters: strawberry.scalars.JSON | None = None


# ============================================================================
# Queries
# ============================================================================

@strawberry.type
class Query:
    """Root query type"""

    @strawberry.field
    async def me(self, info: Info) -> User | None:
        """Get current authenticated user"""
        return User(
            id="user_123",
            email="user@example.com",
            username="demo_user",
            is_active=True,
            is_verified=True,
            roles=["admin", "data_scientist"],
            created_at=datetime.now(),
            last_login=datetime.now()
        )

    @strawberry.field
    async def models(
        self,
        status: ModelStatus | None = None,
        limit: int = 20,
        offset: int = 0
    ) -> list[MLModel]:
        """List ML models with optional filtering"""
        models = [
            MLModel(
                id=f"model_{i}",
                name=f"model-{name}",
                model_type=model_type,
                version="1.0.0",
                status=ModelStatus.DEPLOYED,
                description=f"{name} model",
                created_at=datetime.now(),
                deployed_at=datetime.now()
            )
            for i, (name, model_type) in enumerate([
                ("anomaly-detector", "IsolationForest"),
                ("churn-predictor", "XGBoost"),
                ("demand-forecaster", "Prophet"),
                ("sentiment-analyzer", "Transformer"),
            ])
        ]

        if status:
            models = [m for m in models if m.status == status]

        return models[offset:offset + limit]

    @strawberry.field
    async def model(self, id: str) -> MLModel | None:
        """Get a specific model by ID"""
        return MLModel(
            id=id,
            name="anomaly-detector",
            model_type="IsolationForest",
            version="2.1.0",
            status=ModelStatus.DEPLOYED,
            description="Multivariate anomaly detection model",
            created_at=datetime.now(),
            deployed_at=datetime.now()
        )

    @strawberry.field
    async def pipelines(self, status: PipelineStatus | None = None) -> list[DataPipeline]:
        """List data pipelines"""
        return [
            DataPipeline(
                id="pipeline_1",
                name="real-time-events",
                pipeline_type="streaming",
                status=PipelineStatus.RUNNING,
                created_at=datetime.now(),
                last_run=datetime.now(),
                next_run=None
            ),
            DataPipeline(
                id="pipeline_2",
                name="daily-etl",
                pipeline_type="batch",
                status=PipelineStatus.RUNNING,
                created_at=datetime.now(),
                last_run=datetime.now(),
                next_run=datetime.now()
            )
        ]

    @strawberry.field
    async def decisions(
        self,
        status: DecisionStatus | None = None,
        limit: int = 20
    ) -> list[Decision]:
        """List autonomous decisions"""
        return [
            Decision(
                id=f"dec_{i}",
                decision_type=dtype,
                status=DecisionStatus.EXECUTED,
                confidence=0.85 + i * 0.03,
                impact_level="medium",
                reasoning="Automated decision based on ML analysis",
                created_at=datetime.now(),
                executed_at=datetime.now()
            )
            for i, dtype in enumerate(["budget_optimization", "resource_scaling", "anomaly_response"])
        ][:limit]

    @strawberry.field
    async def health(self) -> PlatformHealth:
        """Get platform health status"""
        return PlatformHealth(
            status="healthy",
            version="2.0.0",
            uptime_seconds=864000,
            components=[
                HealthCheck(component="api", status="healthy", latency_ms=12.5, message=None, checked_at=datetime.now()),
                HealthCheck(component="database", status="healthy", latency_ms=3.2, message=None, checked_at=datetime.now()),
                HealthCheck(component="redis", status="healthy", latency_ms=1.1, message=None, checked_at=datetime.now()),
                HealthCheck(component="ml_engine", status="healthy", latency_ms=45.0, message=None, checked_at=datetime.now()),
            ]
        )

    @strawberry.field
    async def analytics(self) -> Analytics:
        """Get platform analytics"""
        return Analytics(
            total_predictions=1250847,
            total_decisions=45623,
            active_models=8,
            active_pipelines=5,
            active_users=127
        )


# ============================================================================
# Mutations
# ============================================================================

@strawberry.type
class PredictionResult:
    """Mutation result for predictions"""
    success: bool
    prediction: Prediction | None
    error: str | None


@strawberry.type
class ModelResult:
    """Mutation result for model operations"""
    success: bool
    model: MLModel | None
    error: str | None


@strawberry.type
class PipelineResult:
    """Mutation result for pipeline operations"""
    success: bool
    job_id: str | None
    error: str | None


@strawberry.type
class Mutation:
    """Root mutation type"""

    @strawberry.mutation
    async def predict(self, input: PredictionInput) -> PredictionResult:
        """Make a prediction using a model"""
        prediction = Prediction(
            id=str(uuid.uuid4()),
            model_id=input.model_id,
            model_name="anomaly-detector",
            prediction_type=PredictionType.CLASSIFICATION,
            input_data=input.features,
            result=0.85,
            confidence=0.92,
            label="anomaly",
            created_at=datetime.now(),
            latency_ms=23.5
        )
        return PredictionResult(success=True, prediction=prediction, error=None)

    @strawberry.mutation
    async def create_model(self, input: CreateModelInput) -> ModelResult:
        """Create a new ML model"""
        model = MLModel(
            id=str(uuid.uuid4()),
            name=input.name,
            model_type=input.model_type,
            version="1.0.0",
            status=ModelStatus.READY,
            description=input.description,
            created_at=datetime.now(),
            deployed_at=None
        )
        return ModelResult(success=True, model=model, error=None)

    @strawberry.mutation
    async def deploy_model(self, model_id: str, replicas: int = 1) -> ModelResult:
        """Deploy a model to production"""
        model = MLModel(
            id=model_id,
            name="deployed-model",
            model_type="XGBoost",
            version="1.0.0",
            status=ModelStatus.DEPLOYED,
            description="Deployed model",
            created_at=datetime.now(),
            deployed_at=datetime.now()
        )
        return ModelResult(success=True, model=model, error=None)

    @strawberry.mutation
    async def run_pipeline(self, input: PipelineRunInput) -> PipelineResult:
        """Trigger a pipeline run"""
        return PipelineResult(
            success=True,
            job_id=str(uuid.uuid4()),
            error=None
        )


# ============================================================================
# Subscriptions
# ============================================================================

@strawberry.type
class Subscription:
    """Root subscription type for real-time updates"""

    @strawberry.subscription
    async def prediction_stream(
        self,
        model_id: str
    ) -> AsyncGenerator[Prediction, None]:
        """Stream predictions from a model in real-time"""
        while True:
            await asyncio.sleep(1)
            yield Prediction(
                id=str(uuid.uuid4()),
                model_id=model_id,
                model_name="streaming-model",
                prediction_type=PredictionType.ANOMALY,
                input_data={},
                result=0.1 + (0.8 * (hash(str(uuid.uuid4())) % 100) / 100),
                confidence=0.9,
                label="normal",
                created_at=datetime.now(),
                latency_ms=5.2
            )

    @strawberry.subscription
    async def health_updates(self) -> AsyncGenerator[PlatformHealth, None]:
        """Stream platform health updates"""
        while True:
            await asyncio.sleep(5)
            yield PlatformHealth(
                status="healthy",
                version="2.0.0",
                uptime_seconds=864000,
                components=[
                    HealthCheck(
                        component="api",
                        status="healthy",
                        latency_ms=12.5,
                        message=None,
                        checked_at=datetime.now()
                    )
                ]
            )

    @strawberry.subscription
    async def decision_updates(self) -> AsyncGenerator[Decision, None]:
        """Stream decision updates"""
        while True:
            await asyncio.sleep(3)
            yield Decision(
                id=str(uuid.uuid4()),
                decision_type="automated_response",
                status=DecisionStatus.EXECUTED,
                confidence=0.88,
                impact_level="medium",
                reasoning="Real-time decision",
                created_at=datetime.now(),
                executed_at=datetime.now()
            )


# ============================================================================
# Schema
# ============================================================================

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription
)


def get_context(request):
    """Create GraphQL context"""
    return {
        "request": request,
        "user": None  # Will be populated by auth middleware
    }
