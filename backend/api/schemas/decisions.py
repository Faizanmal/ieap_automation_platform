from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DecisionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"


class DecisionImpact(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Decision(BaseModel):
    id: str
    title: str
    description: str
    domain: str
    status: DecisionStatus
    impact: DecisionImpact
    confidence: float
    reasoning: str
    options: list[dict[str, Any]]
    selected_option: dict[str, Any] | None
    cost_estimate: float
    expected_benefit: float
    created_at: datetime
    decided_at: datetime | None = None
    executed_at: datetime | None = None
    requires_approval: bool


class DecisionListResponse(BaseModel):
    decisions: list[Decision]
    total: int
    pending_count: int


class ApproveDecisionRequest(BaseModel):
    comments: str | None = None


class RejectDecisionRequest(BaseModel):
    reason: str = Field(min_length=10)
