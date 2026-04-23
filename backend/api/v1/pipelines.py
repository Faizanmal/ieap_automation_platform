"""
Data Pipelines Endpoint

Provides:
- Pipeline management
- Pipeline execution
- Pipeline monitoring
- Data source configuration
"""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status

from api.schemas.pipelines import (
    CreatePipelineRequest,
    DataSourceType,
    PipelineInfo,
    PipelineMetrics,
    PipelineRunResponse,
    PipelineStatus,
)

router = APIRouter()


def utc_datetime(year: int, month: int, day: int) -> datetime:
    """Build a timezone-aware UTC datetime for seed data."""
    return datetime(year, month, day, tzinfo=UTC)


def now_utc() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(UTC)


# Mock data
_pipelines: dict[str, PipelineInfo] = {
    "pipeline_001": PipelineInfo(
        id="pipeline_001",
        name="Customer Data Sync",
        description="Real-time customer data synchronization from CRM",
        status=PipelineStatus.RUNNING,
        source_type=DataSourceType.API,
        schedule="*/5 * * * *",
        last_run=now_utc(),
        created_at=utc_datetime(2024, 1, 1),
        updated_at=now_utc()
    ),
    "pipeline_002": PipelineInfo(
        id="pipeline_002",
        name="Transaction ETL",
        description="Daily transaction data extraction and transformation",
        status=PipelineStatus.IDLE,
        source_type=DataSourceType.DATABASE,
        schedule="0 2 * * *",
        last_run=utc_datetime(2024, 1, 1),
        created_at=utc_datetime(2024, 1, 15),
        updated_at=now_utc()
    )
}


@router.get("", summary="List pipelines")
async def list_pipelines(
    status: PipelineStatus | None = None,
    source_type: DataSourceType | None = None
):
    """List all data pipelines."""
    pipelines = list(_pipelines.values())

    if status:
        pipelines = [p for p in pipelines if p.status == status]
    if source_type:
        pipelines = [p for p in pipelines if p.source_type == source_type]

    return {"pipelines": pipelines, "total": len(pipelines)}


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create pipeline")
async def create_pipeline(request: CreatePipelineRequest):
    """Create a new data pipeline."""
    pipeline_id = f"pipeline_{uuid.uuid4().hex[:8]}"

    pipeline = PipelineInfo(
        id=pipeline_id,
        name=request.name,
        description=request.description,
        status=PipelineStatus.IDLE,
        source_type=request.source_type,
        schedule=request.schedule,
        created_at=now_utc(),
        updated_at=now_utc(),
        config={
            "source": request.source_config,
            "destination": request.destination_config,
            "transformations": request.transformations
        }
    )

    _pipelines[pipeline_id] = pipeline
    return pipeline


@router.get("/{pipeline_id}", summary="Get pipeline details")
async def get_pipeline(pipeline_id: str):
    """Get pipeline by ID."""
    if pipeline_id not in _pipelines:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return _pipelines[pipeline_id]


@router.post("/{pipeline_id}/run", summary="Run pipeline")
async def run_pipeline(pipeline_id: str):
    """Trigger a pipeline run."""
    if pipeline_id not in _pipelines:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    pipeline = _pipelines[pipeline_id]
    if pipeline.status == PipelineStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Pipeline is already running")

    pipeline.status = PipelineStatus.RUNNING
    pipeline.last_run = now_utc()

    return PipelineRunResponse(
        pipeline_id=pipeline_id,
        run_id=str(uuid.uuid4()),
        status=PipelineStatus.RUNNING,
        message="Pipeline started successfully"
    )


@router.post("/{pipeline_id}/stop", summary="Stop pipeline")
async def stop_pipeline(pipeline_id: str):
    """Stop a running pipeline."""
    if pipeline_id not in _pipelines:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    pipeline = _pipelines[pipeline_id]
    pipeline.status = PipelineStatus.PAUSED

    return {"message": "Pipeline stopped", "status": pipeline.status}


@router.get("/{pipeline_id}/metrics", response_model=PipelineMetrics, summary="Get metrics")
async def get_pipeline_metrics(pipeline_id: str):
    """Get pipeline performance metrics."""
    if pipeline_id not in _pipelines:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    return PipelineMetrics(
        pipeline_id=pipeline_id,
        records_processed=125000,
        records_failed=42,
        throughput_per_second=1250.5,
        avg_latency_ms=12.3,
        error_rate=0.0003,
        uptime_percentage=99.95,
        last_updated=now_utc()
    )


@router.delete("/{pipeline_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete pipeline")
async def delete_pipeline(pipeline_id: str):
    """Delete a pipeline."""
    if pipeline_id not in _pipelines:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    del _pipelines[pipeline_id]
