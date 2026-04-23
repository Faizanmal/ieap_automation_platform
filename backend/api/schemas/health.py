from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class HealthStatus(str, Enum):
    """Health status values"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth(BaseModel):
    """Health status of a single component"""
    name: str
    status: HealthStatus
    response_time_ms: float | None = None
    message: str | None = None
    details: dict | None = None


class HealthResponse(BaseModel):
    """Complete health check response"""
    status: HealthStatus
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str = "2.0.0"
    uptime_seconds: float = 0
    components: list[ComponentHealth] = []

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ReadinessResponse(BaseModel):
    """Kubernetes readiness probe response"""
    ready: bool
    reason: str | None = None


class LivenessResponse(BaseModel):
    """Kubernetes liveness probe response"""
    alive: bool
