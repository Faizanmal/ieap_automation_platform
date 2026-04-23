"""
Predictions Endpoint

Provides:
- Single predictions
- Batch predictions
- Streaming predictions
- Prediction explanations
"""

import hashlib
import time
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter

from api.schemas.predictions import (
    AnomalyDetectionRequest,
    AnomalyDetectionResponse,
    BatchPredictionRequest,
    BatchPredictionResponse,
    ChurnPredictionRequest,
    ChurnPredictionResponse,
    ForecastRequest,
    ForecastResponse,
    PredictionExplanation,
    PredictionRequest,
    PredictionResponse,
    PredictionResult,
)

router = APIRouter()

BASE_FORECAST_VALUE = 1000
LOW_TENURE_MONTHS_THRESHOLD = 12
HIGH_MONTHLY_CHARGES_THRESHOLD = 80
HIGH_SUPPORT_TICKETS_THRESHOLD = 3
BASE_CHURN_PROBABILITY = 0.3
MAX_CHURN_PROBABILITY = 0.95
LOW_RISK_THRESHOLD = 0.3
MEDIUM_RISK_THRESHOLD = 0.6


def now_utc() -> datetime:
    """Return the current timezone-aware UTC datetime."""
    return datetime.now(UTC)


def deterministic_unit(seed: str) -> float:
    """Generate a deterministic float in [0, 1] from a seed string."""
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], byteorder="big") / float(2**64 - 1)


def deterministic_range(seed: str, lower: float, upper: float) -> float:
    """Generate a deterministic float in [lower, upper]."""
    return lower + (upper - lower) * deterministic_unit(seed)


def classify_churn_risk(churn_probability: float) -> str:
    """Map churn probability into risk buckets."""
    if churn_probability < LOW_RISK_THRESHOLD:
        return "low"
    if churn_probability < MEDIUM_RISK_THRESHOLD:
        return "medium"
    return "high"


def build_churn_signals(
    request: ChurnPredictionRequest,
) -> tuple[float, list[dict[str, float | str]], list[str]]:
    """Calculate churn adjustments, risk factors, and tailored recommendations."""
    rules = [
        (
            request.tenure_months < LOW_TENURE_MONTHS_THRESHOLD,
            0.2,
            {
                "factor": "Low tenure",
                "impact": 0.2,
                "description": "Customer is relatively new",
            },
            "Offer onboarding support",
        ),
        (
            request.monthly_charges > HIGH_MONTHLY_CHARGES_THRESHOLD,
            0.1,
            {
                "factor": "High monthly charges",
                "impact": 0.15,
                "description": "Above average monthly spend",
            },
            "Offer plan optimization review",
        ),
        (
            request.num_support_tickets > HIGH_SUPPORT_TICKETS_THRESHOLD,
            0.15,
            {
                "factor": "Multiple support tickets",
                "impact": 0.2,
                "description": "Customer has contacted support frequently",
            },
            "Escalate to customer success team",
        ),
        (
            request.contract_type == "month-to-month",
            0.1,
            {
                "factor": "Month-to-month contract",
                "impact": 0.1,
                "description": "Customer has low contractual commitment",
            },
            "Offer annual contract incentive",
        ),
    ]

    base_probability = BASE_CHURN_PROBABILITY
    risk_factors: list[dict[str, float | str]] = []
    recommendations: list[str] = []

    for applies, weight, factor, recommendation in rules:
        if not applies:
            continue
        base_probability += weight
        risk_factors.append(factor)
        recommendations.append(recommendation)

    return base_probability, risk_factors, recommendations


@router.post(
    "",
    response_model=PredictionResponse,
    summary="Make prediction",
    description="Make a single prediction using a deployed model"
)
async def predict(request: PredictionRequest):
    """
    Make a prediction using a deployed model.

    - Supports all model types
    - Optional explanation generation
    - Returns prediction with confidence
    """
    start_time = time.perf_counter()
    request_id = str(uuid.uuid4())

    # In production, this would call the actual model
    # For demo, generate mock prediction
    prediction = PredictionResult(
        prediction=1,
        probability=0.87,
        confidence=0.92,
        label="positive"
    )

    explanation = None
    if request.include_explanation:
        explanation = PredictionExplanation(
            feature_contributions={
                "feature_1": 0.35,
                "feature_2": -0.15,
                "feature_3": 0.22
            },
            base_value=0.5,
            prediction_value=0.87
        )

    latency_ms = (time.perf_counter() - start_time) * 1000

    return PredictionResponse(
        request_id=request_id,
        model_id=request.model_id,
        model_version="1.0.0",
        prediction=prediction,
        explanation=explanation,
        latency_ms=latency_ms
    )


@router.post(
    "/batch",
    response_model=BatchPredictionResponse,
    summary="Batch prediction",
    description="Make predictions for multiple instances"
)
async def batch_predict(request: BatchPredictionRequest):
    """
    Make predictions for multiple instances at once.

    - More efficient than individual predictions
    - Returns summary statistics
    """
    start_time = time.perf_counter()
    request_id = str(uuid.uuid4())

    predictions = []
    for index, instance in enumerate(request.instances):
        probability = deterministic_range(
            f"{request.model_id}:{index}:{instance}",
            0.85,
            0.94,
        )
        predictions.append(PredictionResult(
            prediction=1,
            probability=probability,
            confidence=0.90
        ))

    latency_ms = (time.perf_counter() - start_time) * 1000

    return BatchPredictionResponse(
        request_id=request_id,
        model_id=request.model_id,
        model_version="1.0.0",
        predictions=predictions,
        total_instances=len(request.instances),
        successful=len(predictions),
        failed=0,
        latency_ms=latency_ms
    )


@router.post(
    "/anomaly",
    response_model=AnomalyDetectionResponse,
    summary="Detect anomalies",
    description="Detect anomalies in input data"
)
async def detect_anomaly(request: AnomalyDetectionRequest):
    """
    Detect anomalies using the anomaly detection model.

    Returns:
    - Whether the input is anomalous
    - Anomaly score
    - Feature contributions
    - Recommended action
    """
    # Calculate deterministic mock anomaly score from request content.
    anomaly_seed = f"{request.threshold}:{sorted(request.features.items())}"
    anomaly_score = deterministic_range(anomaly_seed, 0.1, 0.9)
    is_anomaly = anomaly_score > request.threshold

    # Generate feature contributions
    feature_contributions = {}
    for feature, _value in request.features.items():
        feature_contributions[feature] = deterministic_range(
            f"{anomaly_seed}:{feature}",
            -0.3,
            0.3,
        )

    recommendation = (
        "Investigate immediately - anomalous behavior detected"
        if is_anomaly else
        "No action required - behavior within normal parameters"
    )

    return AnomalyDetectionResponse(
        is_anomaly=is_anomaly,
        anomaly_score=anomaly_score,
        threshold=request.threshold,
        feature_contributions=feature_contributions,
        recommendation=recommendation
    )


@router.post(
    "/forecast",
    response_model=ForecastResponse,
    summary="Generate forecast",
    description="Generate time series forecast"
)
async def generate_forecast(request: ForecastRequest):
    """
    Generate time series forecast.

    - Supports daily, weekly, monthly frequencies
    - Returns confidence intervals
    """
    forecasts = []

    for i in range(request.periods):
        date = now_utc() + timedelta(days=i)
        value = (
            BASE_FORECAST_VALUE
            + deterministic_range(f"{request.target}:{request.frequency}:{i}", -100, 100)
            + (i * 5)
        )

        forecast = {
            "date": date.isoformat(),
            "forecast": round(value, 2),
        }

        if request.include_confidence:
            forecast["lower_bound"] = round(value * 0.9, 2)
            forecast["upper_bound"] = round(value * 1.1, 2)

        forecasts.append(forecast)

    return ForecastResponse(
        target=request.target,
        forecasts=forecasts,
        model_used="prophet_xgboost_ensemble"
    )


@router.post(
    "/churn",
    response_model=ChurnPredictionResponse,
    summary="Predict customer churn",
    description="Predict probability of customer churning"
)
async def predict_churn(request: ChurnPredictionRequest):
    """
    Predict customer churn probability.

    Returns:
    - Churn probability
    - Risk level
    - Key risk factors
    - Recommended retention actions
    """
    base_probability, risk_factors, recommendations = build_churn_signals(request)

    churn_jitter = deterministic_range(
        (
            f"{request.customer_id}:{request.tenure_months}:{request.monthly_charges}:"
            f"{request.total_charges}:{request.contract_type}:{request.payment_method}:"
            f"{request.num_support_tickets}"
        ),
        -0.1,
        0.1,
    )
    churn_prob = min(MAX_CHURN_PROBABILITY, max(0.0, base_probability + churn_jitter))
    risk = classify_churn_risk(churn_prob)

    if risk in ["medium", "high"]:
        recommendations.extend([
            "Offer loyalty discount",
            "Schedule proactive outreach call",
        ])

    if not recommendations:
        recommendations = ["Continue standard engagement"]

    recommendations = list(dict.fromkeys(recommendations))

    return ChurnPredictionResponse(
        customer_id=request.customer_id,
        churn_probability=round(churn_prob, 3),
        churn_risk=risk,
        top_risk_factors=risk_factors,
        recommended_actions=recommendations,
        retention_score=round(1 - churn_prob, 3)
    )
