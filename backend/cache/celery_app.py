"""
Celery Application

Enterprise task queue configuration with:
- Multiple queues
- Priority support
- Result backend
- Monitoring
"""

import os

from celery import Celery
from kombu import Exchange, Queue


def create_celery_app(
    broker_url: str | None = None,
    result_backend: str | None = None
) -> Celery:
    """
    Create and configure Celery application.
    
    Args:
        broker_url: Message broker URL (default: Redis)
        result_backend: Result backend URL (default: Redis)
    
    Returns:
        Configured Celery app
    """
    # Get URLs from environment or settings
    if not broker_url:
        broker_url = os.environ.get(
            "CELERY_BROKER_URL",
            "redis://localhost:6379/1"
        )

    if not result_backend:
        result_backend = os.environ.get(
            "CELERY_RESULT_BACKEND",
            "redis://localhost:6379/2"
        )

    # Create app
    app = Celery(
        "ieap_tasks",
        broker=broker_url,
        backend=result_backend,
        include=[
            "cache.tasks"
        ]
    )

    # Define exchanges
    default_exchange = Exchange("default", type="direct")
    priority_exchange = Exchange("priority", type="direct")

    # Configure queues
    app.conf.task_queues = [
        # Default queue for general tasks
        Queue("default", default_exchange, routing_key="default"),

        # High priority queue
        Queue("high_priority", priority_exchange, routing_key="high"),

        # ML tasks queue
        Queue("ml_tasks", default_exchange, routing_key="ml"),

        # Pipeline tasks queue
        Queue("pipeline_tasks", default_exchange, routing_key="pipeline"),

        # Webhook delivery queue
        Queue("webhooks", default_exchange, routing_key="webhook"),

        # Scheduled tasks queue
        Queue("scheduled", default_exchange, routing_key="scheduled"),
    ]

    # Route tasks to queues
    app.conf.task_routes = {
        "cache.tasks.process_prediction": {"queue": "ml_tasks"},
        "cache.tasks.train_model_task": {"queue": "ml_tasks"},
        "cache.tasks.run_pipeline_task": {"queue": "pipeline_tasks"},
        "cache.tasks.send_webhook_task": {"queue": "webhooks"},
        "cache.tasks.cleanup_old_data_task": {"queue": "scheduled"},
    }

    # Task configuration
    app.conf.update(
        # Task settings
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,

        # Result settings
        result_expires=3600,  # Results expire after 1 hour
        result_extended=True,

        # Worker settings
        worker_prefetch_multiplier=4,
        worker_max_tasks_per_child=1000,
        worker_hijack_root_logger=False,

        # Task execution settings
        task_time_limit=3600,  # 1 hour hard limit
        task_soft_time_limit=3000,  # 50 min soft limit
        task_acks_late=True,
        task_reject_on_worker_lost=True,

        # Retry settings
        task_default_retry_delay=60,  # 1 minute
        task_max_retries=3,

        # Rate limiting
        task_annotations={
            "cache.tasks.send_webhook_task": {
                "rate_limit": "100/m"  # 100 webhooks per minute
            }
        },

        # Monitoring
        worker_send_task_events=True,
        task_send_sent_event=True,

        # Broker settings
        broker_connection_retry_on_startup=True,
        broker_pool_limit=10,
    )

    # Beat schedule for periodic tasks
    app.conf.beat_schedule = {
        "cleanup-old-predictions": {
            "task": "cache.tasks.cleanup_old_data_task",
            "schedule": 3600.0,  # Every hour
            "args": ("predictions", 30),  # Delete predictions older than 30 days
            "options": {"queue": "scheduled"}
        },
        "cleanup-old-audit-logs": {
            "task": "cache.tasks.cleanup_old_data_task",
            "schedule": 86400.0,  # Every day
            "args": ("audit_logs", 90),  # Delete audit logs older than 90 days
            "options": {"queue": "scheduled"}
        },
    }

    return app


# Global Celery app instance
celery_app = create_celery_app()


# Task decorators for convenience
def task(*args, **kwargs):
    """Decorator to register a Celery task."""
    return celery_app.task(*args, **kwargs)


def shared_task(*args, **kwargs):
    """Decorator for shared tasks."""
    from celery import shared_task as celery_shared_task
    return celery_shared_task(*args, **kwargs)
