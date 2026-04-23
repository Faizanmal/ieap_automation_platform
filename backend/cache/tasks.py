"""
Celery Tasks

Background tasks for the enterprise platform.
"""

import logging
from datetime import datetime
from typing import Any

from celery import current_task
from celery.exceptions import MaxRetriesExceededError

from .celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="cache.tasks.process_prediction",
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(Exception,),
    retry_backoff=True
)
def process_prediction(
    self,
    model_id: str,
    input_data: dict[str, Any],
    request_id: str,
    user_id: str | None = None
) -> dict[str, Any]:
    """
    Process a prediction request asynchronously.
    
    Args:
        model_id: ID of the ML model to use
        input_data: Input data for prediction
        request_id: Unique request identifier
        user_id: Optional user ID
    
    Returns:
        Prediction result with metadata
    """
    logger.info(f"Processing prediction request {request_id} for model {model_id}")

    try:
        # Update task state
        self.update_state(
            state="PROCESSING",
            meta={
                "model_id": model_id,
                "request_id": request_id,
                "started_at": datetime.utcnow().isoformat()
            }
        )

        # Import here to avoid circular imports
        from ml_models import get_model_manager

        # Get model and make prediction
        manager = get_model_manager()
        start_time = datetime.utcnow()

        result = manager.predict(model_id, input_data)

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        # Build response
        response = {
            "request_id": request_id,
            "model_id": model_id,
            "prediction": result.get("prediction"),
            "probability": result.get("probability"),
            "confidence": result.get("confidence"),
            "latency_ms": latency_ms,
            "processed_at": datetime.utcnow().isoformat(),
            "status": "completed"
        }

        logger.info(f"Prediction {request_id} completed in {latency_ms:.2f}ms")

        return response

    except Exception as e:
        logger.error(f"Prediction {request_id} failed: {e}")

        try:
            self.retry(exc=e)
        except MaxRetriesExceededError:
            return {
                "request_id": request_id,
                "model_id": model_id,
                "status": "failed",
                "error": str(e)
            }


@celery_app.task(
    bind=True,
    name="cache.tasks.train_model_task",
    time_limit=7200,  # 2 hour hard limit
    soft_time_limit=6000  # 100 min soft limit
)
def train_model_task(
    self,
    model_type: str,
    training_config: dict[str, Any],
    model_name: str,
    model_version: str,
    user_id: str | None = None
) -> dict[str, Any]:
    """
    Train an ML model asynchronously.
    
    Args:
        model_type: Type of model to train
        training_config: Training configuration
        model_name: Name for the trained model
        model_version: Version string
        user_id: User who initiated training
    
    Returns:
        Training result with metrics
    """
    task_id = current_task.request.id
    logger.info(f"Starting model training task {task_id}: {model_name} v{model_version}")

    try:
        self.update_state(
            state="TRAINING",
            meta={
                "model_name": model_name,
                "model_version": model_version,
                "started_at": datetime.utcnow().isoformat(),
                "progress": 0
            }
        )

        # Import training module
        from ml_models import get_model_manager

        manager = get_model_manager()

        # Training callback to update progress
        def progress_callback(progress: float, message: str = ""):
            self.update_state(
                state="TRAINING",
                meta={
                    "model_name": model_name,
                    "progress": progress,
                    "message": message
                }
            )

        # Train model
        result = manager.train(
            model_type=model_type,
            config=training_config,
            progress_callback=progress_callback
        )

        response = {
            "task_id": task_id,
            "model_name": model_name,
            "model_version": model_version,
            "model_id": result.get("model_id"),
            "metrics": result.get("metrics", {}),
            "artifact_path": result.get("artifact_path"),
            "completed_at": datetime.utcnow().isoformat(),
            "status": "completed"
        }

        logger.info(f"Model training {task_id} completed")

        return response

    except Exception as e:
        logger.error(f"Model training {task_id} failed: {e}")
        return {
            "task_id": task_id,
            "model_name": model_name,
            "model_version": model_version,
            "status": "failed",
            "error": str(e)
        }


@celery_app.task(
    bind=True,
    name="cache.tasks.run_pipeline_task",
    max_retries=2
)
def run_pipeline_task(
    self,
    pipeline_id: str,
    run_config: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Execute a data pipeline.
    
    Args:
        pipeline_id: ID of the pipeline to run
        run_config: Optional runtime configuration overrides
    
    Returns:
        Pipeline execution result
    """
    task_id = current_task.request.id
    logger.info(f"Starting pipeline task {task_id}: {pipeline_id}")

    try:
        self.update_state(
            state="RUNNING",
            meta={
                "pipeline_id": pipeline_id,
                "started_at": datetime.utcnow().isoformat(),
                "records_processed": 0
            }
        )

        from data_pipeline import get_pipeline_manager

        manager = get_pipeline_manager()

        # Progress callback
        def progress_callback(records: int, message: str = ""):
            self.update_state(
                state="RUNNING",
                meta={
                    "pipeline_id": pipeline_id,
                    "records_processed": records,
                    "message": message
                }
            )

        # Run pipeline
        result = manager.run(
            pipeline_id=pipeline_id,
            config=run_config or {},
            progress_callback=progress_callback
        )

        response = {
            "task_id": task_id,
            "pipeline_id": pipeline_id,
            "records_processed": result.get("records_processed", 0),
            "records_failed": result.get("records_failed", 0),
            "duration_seconds": result.get("duration_seconds"),
            "completed_at": datetime.utcnow().isoformat(),
            "status": "completed"
        }

        logger.info(f"Pipeline task {task_id} completed: {response['records_processed']} records")

        return response

    except Exception as e:
        logger.error(f"Pipeline task {task_id} failed: {e}")
        return {
            "task_id": task_id,
            "pipeline_id": pipeline_id,
            "status": "failed",
            "error": str(e)
        }


@celery_app.task(
    bind=True,
    name="cache.tasks.send_webhook_task",
    max_retries=5,
    default_retry_delay=60,
    retry_backoff=True,
    retry_backoff_max=3600
)
def send_webhook_task(
    self,
    webhook_id: str,
    webhook_url: str,
    event_type: str,
    payload: dict[str, Any],
    secret: str | None = None
) -> dict[str, Any]:
    """
    Send a webhook notification.
    
    Args:
        webhook_id: ID of the webhook configuration
        webhook_url: URL to send the webhook to
        event_type: Type of event
        payload: Event payload
        secret: Webhook secret for signature
    
    Returns:
        Delivery result
    """
    import hashlib
    import hmac
    import json

    import requests

    logger.info(f"Sending webhook {webhook_id}: {event_type}")

    try:
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Event": event_type,
            "X-Webhook-ID": webhook_id,
            "X-Webhook-Timestamp": datetime.utcnow().isoformat()
        }

        # Sign payload if secret provided
        if secret:
            body = json.dumps(payload)
            signature = hmac.new(
                secret.encode(),
                body.encode(),
                hashlib.sha256
            ).hexdigest()
            headers["X-Webhook-Signature"] = f"sha256={signature}"

        # Send request
        response = requests.post(
            webhook_url,
            json=payload,
            headers=headers,
            timeout=30
        )

        response.raise_for_status()

        result = {
            "webhook_id": webhook_id,
            "event_type": event_type,
            "status_code": response.status_code,
            "delivered_at": datetime.utcnow().isoformat(),
            "status": "delivered"
        }

        logger.info(f"Webhook {webhook_id} delivered successfully")

        return result

    except requests.exceptions.RequestException as e:
        logger.error(f"Webhook {webhook_id} delivery failed: {e}")

        try:
            self.retry(exc=e)
        except MaxRetriesExceededError:
            return {
                "webhook_id": webhook_id,
                "event_type": event_type,
                "status": "failed",
                "error": str(e),
                "attempts": self.request.retries + 1
            }


@celery_app.task(
    name="cache.tasks.cleanup_old_data_task"
)
def cleanup_old_data_task(
    table_name: str,
    days_to_keep: int = 30
) -> dict[str, Any]:
    """
    Clean up old data from specified table.
    
    Args:
        table_name: Table to clean up
        days_to_keep: Number of days of data to keep
    
    Returns:
        Cleanup result
    """
    logger.info(f"Starting cleanup for {table_name}, keeping {days_to_keep} days")

    try:
        from datetime import datetime, timedelta

        from database import get_database
        from database.models import AuditLog, Prediction

        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        # Map table names to models
        table_map = {
            "predictions": Prediction,
            "audit_logs": AuditLog
        }

        model = table_map.get(table_name)
        if not model:
            return {"status": "error", "message": f"Unknown table: {table_name}"}

        # Note: This is a synchronous cleanup for Celery
        # In production, use async session or sync engine
        db = get_database()
        session = db.get_sync_session()

        try:
            # Count records to delete
            count_query = session.query(model).filter(
                model.created_at < cutoff_date
            ).count()

            # Delete old records
            session.query(model).filter(
                model.created_at < cutoff_date
            ).delete(synchronize_session=False)

            session.commit()

            result = {
                "table": table_name,
                "deleted_count": count_query,
                "cutoff_date": cutoff_date.isoformat(),
                "completed_at": datetime.utcnow().isoformat(),
                "status": "completed"
            }

            logger.info(f"Cleanup completed: {count_query} records deleted from {table_name}")

            return result

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Cleanup failed for {table_name}: {e}")
        return {
            "table": table_name,
            "status": "failed",
            "error": str(e)
        }


@celery_app.task(
    bind=True,
    name="cache.tasks.batch_prediction_task"
)
def batch_prediction_task(
    self,
    model_id: str,
    input_batch: list[dict[str, Any]],
    request_id: str
) -> dict[str, Any]:
    """
    Process batch predictions.
    
    Args:
        model_id: Model to use
        input_batch: List of input data
        request_id: Batch request ID
    
    Returns:
        Batch prediction results
    """
    logger.info(f"Processing batch prediction {request_id}: {len(input_batch)} items")

    try:
        from ml_models import get_model_manager

        manager = get_model_manager()
        results = []
        errors = []

        for i, input_data in enumerate(input_batch):
            try:
                result = manager.predict(model_id, input_data)
                results.append({
                    "index": i,
                    "prediction": result.get("prediction"),
                    "probability": result.get("probability"),
                    "status": "success"
                })
            except Exception as e:
                errors.append({
                    "index": i,
                    "error": str(e),
                    "status": "failed"
                })

            # Update progress
            if (i + 1) % 100 == 0:
                self.update_state(
                    state="PROCESSING",
                    meta={
                        "processed": i + 1,
                        "total": len(input_batch),
                        "progress": (i + 1) / len(input_batch) * 100
                    }
                )

        response = {
            "request_id": request_id,
            "model_id": model_id,
            "total": len(input_batch),
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors if errors else None,
            "completed_at": datetime.utcnow().isoformat(),
            "status": "completed"
        }

        logger.info(
            f"Batch prediction {request_id} completed: "
            f"{len(results)} successful, {len(errors)} failed"
        )

        return response

    except Exception as e:
        logger.error(f"Batch prediction {request_id} failed: {e}")
        return {
            "request_id": request_id,
            "model_id": model_id,
            "status": "failed",
            "error": str(e)
        }
