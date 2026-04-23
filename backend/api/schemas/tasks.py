from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel


class TaskStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentStatus(str, Enum):
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"


class Task(BaseModel):
    id: str
    name: str
    type: str
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    assigned_agent: str | None
    result: dict[str, Any] | None
    error: str | None


class Agent(BaseModel):
    id: str
    name: str
    status: AgentStatus
    capabilities: list[str]
    current_task: str | None = None
    tasks_completed: int
    performance_score: float


class CreateTaskRequest(BaseModel):
    name: str
    type: str
    priority: TaskPriority = TaskPriority.MEDIUM
    payload: dict[str, Any] = {}
