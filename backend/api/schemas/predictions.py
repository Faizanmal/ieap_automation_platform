from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PredictionType(str, Enum):
    """Types of predictions"""
    ANOMALY = "anomaly"
    FORECAST = "forecast"
    CLASSIFICATION = "classification"
    REGRESSION = "regression"


class PredictionRequest(BaseModel):
    """Single prediction request"""
    model_id: str
    features: dict[str, Any]
    include_explanation: bool = False


class BatchPredictionRequest(BaseModel):
    """Batch prediction request"""
    model_id: str
    instances: list[dict[str, Any]]
    include_explanations: bool = False


class PredictionResult(BaseModel):
    """Single prediction result"""
    prediction: Any
    probability: float | None = None
    confidence: float | None = None
    label: str | None = None


class PredictionExplanation(BaseModel):
    """Prediction explanation (SHAP-like)"""
    feature_contributions: dict[str, float]
    base_value: float
    prediction_value: float


class PredictionResponse(BaseModel):
    """Prediction response"""
    request_id: str
    model_id: str
    model_version: str
    prediction: PredictionResult
    explanation: PredictionExplanation | None = None
    latency_ms: float
    timestamp: datetime = Field(default_factory=datetime.now)


class BatchPredictionResponse(BaseModel):
    """Batch prediction response"""
    request_id: str
    model_id: str
    model_version: str
    predictions: list[PredictionResult]
    explanations: list[PredictionExplanation] | None = None
    total_instances: int
    successful: int
    failed: int
    latency_ms: float
    timestamp: datetime = Field(default_factory=datetime.now)


class AnomalyDetectionRequest(BaseModel):
    """Anomaly detection request"""
    features: dict[str, float]
    threshold: float = 0.5


class AnomalyDetectionResponse(BaseModel):
    """Anomaly detection response"""
    is_anomaly: bool
    anomaly_score: float
    threshold: float
    feature_contributions: dict[str, float]
    recommendation: str


class ForecastRequest(BaseModel):
    """Forecasting request"""
    target: str
    periods: int = Field(ge=1, le=365, default=30)
    frequency: str = "D"  # D=daily, W=weekly, M=monthly
    include_confidence: bool = True


class ForecastResponse(BaseModel):
    """Forecasting response"""
    target: str
    forecasts: list[dict[str, Any]]
    model_used: str
    confidence_level: float = 0.95


class ChurnPredictionRequest(BaseModel):
    """Churn prediction request"""
    customer_id: str
    tenure_months: int
    monthly_charges: float
    total_charges: float
    contract_type: str
    payment_method: str
    num_support_tickets: int = 0
    additional_features: dict[str, Any] = {}


class ChurnPredictionResponse(BaseModel):
    """Churn prediction response"""
    customer_id: str
    churn_probability: float
    churn_risk: str  # low, medium, high
    top_risk_factors: list[dict[str, Any]]
    recommended_actions: list[str]
    retention_score: float
