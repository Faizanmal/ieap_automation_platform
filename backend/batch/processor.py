"""
Batch Processor

Enterprise-grade batch processing with:
- Progress tracking
- Checkpointing and resumability
- Error handling and retries
- Parallel execution
- Real-time status updates
"""

import asyncio
import contextlib
import json
import logging
import uuid
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")
R = TypeVar("R")


class JobStatus(Enum):
    """Batch job status"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BatchItem:
    """Single item in a batch"""
    id: str
    data: Any
    status: str = "pending"  # pending, processing, completed, failed
    result: Any = None
    error: str | None = None
    attempt: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class BatchProgress:
    """Batch job progress"""
    job_id: str
    total_items: int
    processed_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    skipped_items: int = 0
    current_item: str | None = None
    started_at: datetime | None = None
    updated_at: datetime | None = None
    estimated_remaining_seconds: float | None = None

    @property
    def percentage(self) -> float:
        if self.total_items == 0:
            return 100.0
        return (self.processed_items / self.total_items) * 100

    @property
    def items_per_second(self) -> float:
        if not self.started_at:
            return 0.0
        elapsed = (datetime.now(UTC) - self.started_at).total_seconds()
        if elapsed == 0:
            return 0.0
        return self.processed_items / elapsed

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "total_items": self.total_items,
            "processed_items": self.processed_items,
            "successful_items": self.successful_items,
            "failed_items": self.failed_items,
            "skipped_items": self.skipped_items,
            "percentage": round(self.percentage, 2),
            "items_per_second": round(self.items_per_second, 2),
            "estimated_remaining_seconds": self.estimated_remaining_seconds,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class BatchJob:
    """Batch processing job"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    status: JobStatus = JobStatus.PENDING
    items: list[BatchItem] = field(default_factory=list)
    progress: BatchProgress | None = None
    config: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    checkpoint_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "progress": self.progress.to_dict() if self.progress else None,
            "total_items": len(self.items),
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
        }


class BatchProcessor:
    """
    High-performance batch processor.

    Usage:
        processor = BatchProcessor(
            name="predictions",
            batch_size=100,
            max_workers=4,
            checkpoint_interval=50
        )

        # Define processing function
        async def process_item(item: Dict) -> Dict:
            return await make_prediction(item)

        # Create and run job
        job = await processor.create_job(items, process_item)

        # Stream progress updates
        async for progress in processor.stream_progress(job.id):
            print(f"Progress: {progress.percentage}%")

        # Get results
        results = await processor.get_results(job.id)
    """

    def __init__(
        self,
        name: str = "batch_processor",
        batch_size: int = 100,
        max_workers: int = 4,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        checkpoint_interval: int = 100,
        checkpoint_dir: str = "/tmp/batch_checkpoints",  # noqa: S108
        on_item_complete: Callable | None = None,
        on_job_complete: Callable | None = None,
        on_error: Callable | None = None
    ):
        self.name = name
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.checkpoint_interval = checkpoint_interval
        self.checkpoint_dir = Path(checkpoint_dir)

        # Callbacks
        self.on_item_complete = on_item_complete
        self.on_job_complete = on_job_complete
        self.on_error = on_error

        # Job storage
        self._jobs: dict[str, BatchJob] = {}
        self._running: dict[str, asyncio.Task] = {}

        # Create checkpoint directory
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"BatchProcessor '{name}' initialized")

    async def create_job(
        self,
        items: list[Any],
        processor_func: Callable,
        name: str = "",
        description: str = "",
        config: dict[str, Any] | None = None,
        auto_start: bool = True
    ) -> BatchJob:
        """Create a new batch job"""
        job = BatchJob(
            name=name or f"{self.name}_job_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}",
            description=description,
            items=[
                BatchItem(id=str(i), data=item)
                for i, item in enumerate(items)
            ],
            config=config or {},
            progress=BatchProgress(
                job_id="",
                total_items=len(items)
            )
        )
        job.progress.job_id = job.id
        job.checkpoint_path = str(self.checkpoint_dir / f"{job.id}.checkpoint.json")

        self._jobs[job.id] = job

        logger.info(f"Created batch job '{job.name}' with {len(items)} items")

        if auto_start:
            await self.start_job(job.id, processor_func)

        return job

    async def start_job(self, job_id: str, processor_func: Callable):
        """Start processing a job"""
        job = self._jobs.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        if job.status == JobStatus.RUNNING:
            raise ValueError(f"Job {job_id} is already running")

        # Start processing task
        task = asyncio.create_task(self._process_job(job, processor_func))
        self._running[job_id] = task

        logger.info(f"Started batch job '{job.name}'")

    async def _process_job(self, job: BatchJob, processor_func: Callable):  # noqa: PLR0912
        """Process all items in a job"""
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(UTC)
        job.progress.started_at = datetime.now(UTC)

        try:
            # Get pending items
            pending_items = [
                item for item in job.items
                if item.status in ("pending", "failed") and item.attempt < self.max_retries
            ]

            # Process in batches
            for i in range(0, len(pending_items), self.batch_size):
                if job.status == JobStatus.CANCELLED:
                    break

                if job.status == JobStatus.PAUSED:
                    # Wait for resume
                    while job.status == JobStatus.PAUSED:
                        await asyncio.sleep(1)
                    if job.status == JobStatus.CANCELLED:
                        break

                batch = pending_items[i:i + self.batch_size]

                # Process batch in parallel
                tasks = [
                    self._process_item(job, item, processor_func)
                    for item in batch
                ]
                await asyncio.gather(*tasks, return_exceptions=True)

                # Checkpoint
                if job.progress.processed_items % self.checkpoint_interval == 0:
                    await self._save_checkpoint(job)

            # Final status
            if job.status != JobStatus.CANCELLED:
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now(UTC)

                if self.on_job_complete:
                    try:
                        await self._call_callback(self.on_job_complete, job)
                    except Exception as e:
                        logger.error(f"Error in on_job_complete callback: {e}")

            logger.info(
                f"Batch job '{job.name}' completed: "
                f"{job.progress.successful_items} successful, "
                f"{job.progress.failed_items} failed"
            )

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.completed_at = datetime.now(UTC)
            logger.error(f"Batch job '{job.name}' failed: {e}")

            if self.on_error:
                with contextlib.suppress(Exception):
                    await self._call_callback(self.on_error, job, e)

        finally:
            # Save final checkpoint
            await self._save_checkpoint(job)

            # Clean up
            if job.id in self._running:
                del self._running[job.id]

    async def _process_item(
        self,
        job: BatchJob,
        item: BatchItem,
        processor_func: Callable
    ):
        """Process a single item"""
        item.status = "processing"
        item.started_at = datetime.now(UTC)
        item.attempt += 1
        job.progress.current_item = item.id

        try:
            # Call processor function
            if asyncio.iscoroutinefunction(processor_func):
                result = await processor_func(item.data)
            else:
                result = processor_func(item.data)

            item.status = "completed"
            item.result = result
            item.completed_at = datetime.now(UTC)

            job.progress.processed_items += 1
            job.progress.successful_items += 1
            job.progress.updated_at = datetime.now(UTC)

            # Update estimated time
            if job.progress.items_per_second > 0:
                remaining = job.progress.total_items - job.progress.processed_items
                job.progress.estimated_remaining_seconds = remaining / job.progress.items_per_second

            if self.on_item_complete:
                try:
                    await self._call_callback(self.on_item_complete, item, result)
                except Exception as e:
                    logger.warning(f"Error in on_item_complete callback: {e}")

        except Exception as e:
            item.status = "failed"
            item.error = str(e)
            item.completed_at = datetime.now(UTC)

            job.progress.processed_items += 1
            job.progress.failed_items += 1
            job.progress.updated_at = datetime.now(UTC)

            logger.warning(f"Item {item.id} failed (attempt {item.attempt}): {e}")

    async def _call_callback(self, callback: Callable, *args, **kwargs):
        """Call a callback function"""
        if asyncio.iscoroutinefunction(callback):
            await callback(*args, **kwargs)
        else:
            callback(*args, **kwargs)

    async def _save_checkpoint(self, job: BatchJob):
        """Save job checkpoint to disk"""
        if not job.checkpoint_path:
            return

        checkpoint = {
            "job_id": job.id,
            "name": job.name,
            "status": job.status.value,
            "items": [
                {
                    "id": item.id,
                    "status": item.status,
                    "result": item.result,
                    "error": item.error,
                    "attempt": item.attempt
                }
                for item in job.items
            ],
            "progress": job.progress.to_dict(),
            "saved_at": datetime.now(UTC).isoformat()
        }

        try:
            with open(job.checkpoint_path, "w") as f:
                json.dump(checkpoint, f)
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")

    async def resume_job(self, job_id: str, processor_func: Callable) -> BatchJob:
        """Resume a paused or failed job"""
        job = self._jobs.get(job_id)
        if not job:
            # Try to load from checkpoint
            job = await self._load_checkpoint(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")
            self._jobs[job_id] = job

        if job.status == JobStatus.RUNNING:
            raise ValueError(f"Job {job_id} is already running")

        job.status = JobStatus.RUNNING
        await self.start_job(job_id, processor_func)

        return job

    async def _load_checkpoint(self, job_id: str) -> BatchJob | None:
        """Load job from checkpoint"""
        checkpoint_path = self.checkpoint_dir / f"{job_id}.checkpoint.json"

        if not checkpoint_path.exists():
            return None

        try:
            with open(checkpoint_path) as f:
                data = json.load(f)

            job = BatchJob(
                id=data["job_id"],
                name=data["name"],
                status=JobStatus(data["status"]),
                checkpoint_path=str(checkpoint_path)
            )

            # Restore progress
            job.progress = BatchProgress(
                job_id=job.id,
                total_items=data["progress"]["total_items"],
                processed_items=data["progress"]["processed_items"],
                successful_items=data["progress"]["successful_items"],
                failed_items=data["progress"]["failed_items"]
            )

            return job

        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None

    async def pause_job(self, job_id: str):
        """Pause a running job"""
        job = self._jobs.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        if job.status == JobStatus.RUNNING:
            job.status = JobStatus.PAUSED
            logger.info(f"Paused batch job '{job.name}'")

    async def cancel_job(self, job_id: str):
        """Cancel a job"""
        job = self._jobs.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.now(UTC)

        # Cancel running task
        if job_id in self._running:
            self._running[job_id].cancel()

        logger.info(f"Cancelled batch job '{job.name}'")

    def get_job(self, job_id: str) -> BatchJob | None:
        """Get a job by ID"""
        return self._jobs.get(job_id)

    def get_progress(self, job_id: str) -> BatchProgress | None:
        """Get job progress"""
        job = self._jobs.get(job_id)
        return job.progress if job else None

    async def stream_progress(self, job_id: str, interval: float = 1.0) -> AsyncIterator[BatchProgress]:
        """Stream job progress updates"""
        job = self._jobs.get(job_id)
        if not job:
            return

        while job.status in (JobStatus.PENDING, JobStatus.RUNNING, JobStatus.PAUSED):
            yield job.progress
            await asyncio.sleep(interval)

        # Final update
        yield job.progress

    async def get_results(self, job_id: str) -> list[Any]:
        """Get job results"""
        job = self._jobs.get(job_id)
        if not job:
            return []

        return [
            item.result
            for item in job.items
            if item.status == "completed"
        ]

    async def get_failures(self, job_id: str) -> list[dict[str, Any]]:
        """Get failed items"""
        job = self._jobs.get(job_id)
        if not job:
            return []

        return [
            {"id": item.id, "data": item.data, "error": item.error, "attempts": item.attempt}
            for item in job.items
            if item.status == "failed"
        ]

    def list_jobs(self, status: JobStatus | None = None) -> list[BatchJob]:
        """List all jobs"""
        jobs = list(self._jobs.values())
        if status:
            jobs = [j for j in jobs if j.status == status]
        return jobs
