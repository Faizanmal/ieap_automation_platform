"""
Enterprise Caching & Message Queue

Provides:
- Redis caching with TTL
- Celery task queue
- Async background processing
"""

from .cache_decorator import CacheKey, cache, cached_property, invalidate_cache
from .celery_app import celery_app, create_celery_app
from .redis_client import RedisClient, close_redis, get_redis, init_redis
from .tasks import (
    cleanup_old_data_task,
    process_prediction,
    run_pipeline_task,
    send_webhook_task,
    train_model_task,
)

__all__ = [
    # Redis
    "RedisClient",
    "get_redis",
    "init_redis",
    "close_redis",

    # Cache
    "cache",
    "cached_property",
    "invalidate_cache",
    "CacheKey",

    # Celery
    "celery_app",
    "create_celery_app",

    # Tasks
    "process_prediction",
    "train_model_task",
    "run_pipeline_task",
    "send_webhook_task",
    "cleanup_old_data_task"
]
