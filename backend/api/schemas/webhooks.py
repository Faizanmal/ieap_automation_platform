from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class WebhookEvent(str, Enum):
    MODEL_TRAINED = "model.trained"
    MODEL_DEPLOYED = "model.deployed"
    PREDICTION_MADE = "prediction.made"
    ANOMALY_DETECTED = "anomaly.detected"
    DECISION_MADE = "decision.made"
    PIPELINE_COMPLETED = "pipeline.completed"
    PIPELINE_FAILED = "pipeline.failed"
    TASK_COMPLETED = "task.completed"


class WebhookStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"


class Webhook(BaseModel):
    id: str
    name: str
    url: str
    events: list[WebhookEvent]
    status: WebhookStatus
    secret: str | None = None
    created_at: datetime
    last_triggered: datetime | None
    success_count: int = 0
    failure_count: int = 0


class CreateWebhookRequest(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    url: str
    events: list[WebhookEvent]


class WebhookDelivery(BaseModel):
    id: str
    webhook_id: str
    event: WebhookEvent
    payload: dict[str, Any]
    response_code: int
    delivered_at: datetime
    success: bool
