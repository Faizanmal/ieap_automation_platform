from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ModelType(str, Enum):
    """Available model types"""
    ANOMALY_DETECTION = "anomaly_detection"
    DEMAND_FORECASTING = "demand_forecasting"
    CHURN_PREDICTION = "churn_prediction"
    FRAUD_DETECTION = "fraud_detection"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    PRICE_OPTIMIZATION = "price_optimization"


class ModelStatus(str, Enum):
    """Model deployment status"""
    TRAINING = "training"
    READY = "ready"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    FAILED = "failed"
    DEPRECATED = "deprecated"


class ModelInfo(BaseModel):
    """Model information"""
    id: str
    name: str
    type: ModelType
    version: str
    status: ModelStatus
    description: str | None = None
    created_at: datetime
    updated_at: datetime
    metrics: dict[str, float] = {}
    config: dict[str, Any] = {}


class ModelListResponse(BaseModel):
    """Model list response"""
    models: list[ModelInfo]
    total: int


class TrainModelRequest(BaseModel):
    """Model training request"""
    model_type: ModelType
    name: str = Field(min_length=3, max_length=100)
    config: dict[str, Any] = {}
    data_source: str | None = None


class TrainModelResponse(BaseModel):
    """Model training response"""
    model_id: str
    status: ModelStatus
    message: str
    estimated_time_minutes: int | None = None


class ModelMetrics(BaseModel):
    """Model performance metrics"""
    model_id: str
    accuracy: float | None = None
    precision: float | None = None
    recall: float | None = None
    f1_score: float | None = None
    auc_roc: float | None = None
    mse: float | None = None
    mae: float | None = None
    r2_score: float | None = None
    confusion_matrix: list[list[int]] | None = None
    feature_importance: dict[str, float] = {}
    training_time_seconds: float | None = None
    last_evaluated: datetime
