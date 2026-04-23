"""
Task Orchestrator Endpoints

Provides:
- Task management
- Agent monitoring
- Workflow execution
"""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status

from api.schemas.tasks import (
    Agent,
    AgentStatus,
    CreateTaskRequest,
    Task,
    TaskPriority,
    TaskStatus,
)

router = APIRouter()


def now_utc() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(UTC)


# Mock data
_tasks: dict[str, Task] = {}
_agents: list[Agent] = [
    Agent(id="agent_001", name="Financial Agent", status=AgentStatus.IDLE,
          capabilities=["forecasting", "risk_analysis"], tasks_completed=156, performance_score=0.95),
    Agent(id="agent_002", name="Operations Agent", status=AgentStatus.BUSY,
          capabilities=["maintenance", "optimization"], current_task="task_001", tasks_completed=243, performance_score=0.92),
    Agent(id="agent_003", name="Customer Agent", status=AgentStatus.IDLE,
          capabilities=["churn_prediction", "sentiment"], tasks_completed=189, performance_score=0.94),
]


@router.get("", summary="List tasks")
async def list_tasks(
    status_filter: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    limit: int = 50
):
    """List all tasks."""
    tasks = list(_tasks.values())
    if status_filter:
        tasks = [t for t in tasks if t.status == status_filter]
    if priority:
        tasks = [t for t in tasks if t.priority == priority]
    return {"tasks": tasks[:limit], "total": len(tasks)}


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create task")
async def create_task(request: CreateTaskRequest):
    """Create a new task."""
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    task = Task(
        id=task_id,
        name=request.name,
        type=request.type,
        status=TaskStatus.QUEUED,
        priority=request.priority,
        created_at=now_utc()
    )
    _tasks[task_id] = task
    return task


@router.get("/{task_id}", summary="Get task")
async def get_task(task_id: str):
    """Get task by ID."""
    if task_id not in _tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return _tasks[task_id]


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Cancel task")
async def cancel_task(task_id: str):
    """Cancel a task."""
    if task_id not in _tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    _tasks[task_id].status = TaskStatus.CANCELLED


@router.get("/agents/list", summary="List agents")
async def list_agents():
    """List all AI agents."""
    return {"agents": _agents, "total": len(_agents)}


@router.get("/agents/{agent_id}", summary="Get agent")
async def get_agent(agent_id: str):
    """Get agent by ID."""
    for agent in _agents:
        if agent.id == agent_id:
            return agent
    raise HTTPException(status_code=404, detail="Agent not found")


@router.get("/metrics/summary", summary="Orchestrator metrics")
async def get_orchestrator_metrics():
    """Get orchestrator performance metrics."""
    return {
        "active_agents": len([a for a in _agents if a.status != AgentStatus.OFFLINE]),
        "busy_agents": len([a for a in _agents if a.status == AgentStatus.BUSY]),
        "pending_tasks": len([t for t in _tasks.values() if t.status in [TaskStatus.PENDING, TaskStatus.QUEUED]]),
        "running_tasks": len([t for t in _tasks.values() if t.status == TaskStatus.RUNNING]),
        "completed_today": len([t for t in _tasks.values() if t.status == TaskStatus.COMPLETED]),
        "average_performance": sum(a.performance_score for a in _agents) / len(_agents)
    }
