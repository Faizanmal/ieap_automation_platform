"""
Worker Pool

Manages a pool of workers for parallel batch processing.
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Worker:
    """Individual worker"""
    id: str
    status: str = "idle"  # idle, busy, stopped
    current_task: str | None = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    started_at: datetime = None
    last_activity: datetime = None


class WorkerPool:
    """
    Worker pool for parallel processing.

    Usage:
        pool = WorkerPool(size=4)
        await pool.start()

        async def process(item):
            return await some_operation(item)

        results = await pool.map(process, items)

        await pool.stop()
    """

    def __init__(
        self,
        size: int = 4,
        name: str = "worker_pool"
    ):
        self.size = size
        self.name = name
        self._workers: list[Worker] = []
        self._queue: asyncio.Queue = asyncio.Queue()
        self._results: dict[str, Any] = {}
        self._running = False
        self._tasks: list[asyncio.Task] = []

    async def start(self):
        """Start the worker pool"""
        self._running = True
        self._workers = [
            Worker(id=f"worker_{i}", started_at=datetime.now(UTC))
            for i in range(self.size)
        ]

        # Start worker tasks
        self._tasks = [
            asyncio.create_task(self._worker_loop(worker))
            for worker in self._workers
        ]

        logger.info(f"WorkerPool '{self.name}' started with {self.size} workers")

    async def stop(self):
        """Stop the worker pool"""
        self._running = False

        # Cancel all worker tasks
        for task in self._tasks:
            task.cancel()

        await asyncio.gather(*self._tasks, return_exceptions=True)

        logger.info(f"WorkerPool '{self.name}' stopped")

    async def _worker_loop(self, worker: Worker):
        """Worker processing loop"""
        while self._running:
            try:
                # Get task from queue with timeout
                try:
                    task_id, func, args, kwargs = await asyncio.wait_for(
                        self._queue.get(),
                        timeout=1.0
                    )
                except TimeoutError:
                    continue

                worker.status = "busy"
                worker.current_task = task_id
                worker.last_activity = datetime.now(UTC)

                try:
                    # Execute task
                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)

                    self._results[task_id] = {"status": "success", "result": result}
                    worker.tasks_completed += 1

                except Exception as e:
                    self._results[task_id] = {"status": "error", "error": str(e)}
                    worker.tasks_failed += 1

                finally:
                    worker.status = "idle"
                    worker.current_task = None
                    self._queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker.id} error: {e}")

    async def submit(
        self,
        func: Callable,
        *args,
        task_id: str | None = None,
        **kwargs
    ) -> str:
        """Submit a task to the pool"""
        if task_id is None:
            task_id = f"task_{id(func)}_{datetime.now(UTC).timestamp()}"

        await self._queue.put((task_id, func, args, kwargs))
        return task_id

    async def get_result(self, task_id: str, timeout: float | None = None) -> Any:
        """Get result of a task"""
        start_time = datetime.now(UTC)

        while task_id not in self._results:
            if timeout and (datetime.now(UTC) - start_time).total_seconds() > timeout:
                raise TimeoutError(f"Task {task_id} timed out")
            await asyncio.sleep(0.1)

        result = self._results.pop(task_id)
        if result["status"] == "error":
            raise Exception(result["error"])
        return result["result"]

    async def map(
        self,
        func: Callable,
        items: list[Any],
        _timeout: float | None = None
    ) -> list[Any]:
        """Apply function to all items in parallel"""
        task_ids = []

        for i, item in enumerate(items):
            task_id = await self.submit(func, item, task_id=f"map_{i}")
            task_ids.append(task_id)

        # Wait for all tasks
        await self._queue.join()

        # Collect results in order
        results = []
        for task_id in task_ids:
            result = self._results.pop(task_id, None)
            if result:
                if result["status"] == "error":
                    results.append(None)
                else:
                    results.append(result["result"])
            else:
                results.append(None)

        return results

    def get_stats(self) -> dict[str, Any]:
        """Get pool statistics"""
        return {
            "name": self.name,
            "size": self.size,
            "running": self._running,
            "queue_size": self._queue.qsize(),
            "workers": [
                {
                    "id": w.id,
                    "status": w.status,
                    "tasks_completed": w.tasks_completed,
                    "tasks_failed": w.tasks_failed
                }
                for w in self._workers
            ]
        }
