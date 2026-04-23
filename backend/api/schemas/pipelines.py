from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PipelineStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    FAILED = "failed"
    COMPLETED = "completed"


class DataSourceType(str, Enum):
    API = "api"
    DATABASE = "database"
    FILE = "file"
    STREAM = "stream"
    S3 = "s3"
    KAFKA = "kafka"


class PipelineInfo(BaseModel):
    id: str
    name: str
    description: str | None
    status: PipelineStatus
    source_type: DataSourceType
    schedule: str | None
    last_run: datetime | None = None
    next_run: datetime | None = None
    created_at: datetime
    updated_at: datetime
    config: dict[str, Any] = {}


class PipelineMetrics(BaseModel):
    pipeline_id: str
    records_processed: int
    records_failed: int
    throughput_per_second: float
    avg_latency_ms: float
    error_rate: float
    uptime_percentage: float
    last_updated: datetime


class CreatePipelineRequest(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    description: str | None = None
    source_type: DataSourceType
    source_config: dict[str, Any]
    destination_config: dict[str, Any]
    transformations: list[dict[str, Any]] = []
    schedule: str | None = None


class PipelineRunResponse(BaseModel):
    pipeline_id: str
    run_id: str
    status: PipelineStatus
    message: str
