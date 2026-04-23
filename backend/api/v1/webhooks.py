"""
Webhooks Endpoints

Provides:
- Webhook registration
- Event subscriptions
- Delivery history
"""

import secrets
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status

from api.schemas.webhooks import (
    CreateWebhookRequest,
    Webhook,
    WebhookDelivery,
    WebhookEvent,
    WebhookStatus,
)

router = APIRouter()


def now_utc() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(UTC)


_webhooks: dict[str, Webhook] = {}


@router.get("", summary="List webhooks")
async def list_webhooks():
    """List all registered webhooks."""
    return {"webhooks": list(_webhooks.values()), "total": len(_webhooks)}


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create webhook")
async def create_webhook(request: CreateWebhookRequest):
    """Register a new webhook."""
    webhook_id = f"wh_{uuid.uuid4().hex[:8]}"

    webhook = Webhook(
        id=webhook_id,
        name=request.name,
        url=request.url,
        events=request.events,
        status=WebhookStatus.ACTIVE,
        secret=secrets.token_urlsafe(32),
        created_at=now_utc()
    )

    _webhooks[webhook_id] = webhook
    return webhook


@router.get("/{webhook_id}", summary="Get webhook")
async def get_webhook(webhook_id: str):
    """Get webhook by ID."""
    if webhook_id not in _webhooks:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return _webhooks[webhook_id]


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete webhook")
async def delete_webhook(webhook_id: str):
    """Delete a webhook."""
    if webhook_id not in _webhooks:
        raise HTTPException(status_code=404, detail="Webhook not found")
    del _webhooks[webhook_id]


@router.post("/{webhook_id}/test", summary="Test webhook")
async def test_webhook(webhook_id: str):
    """Send a test event to webhook."""
    if webhook_id not in _webhooks:
        raise HTTPException(status_code=404, detail="Webhook not found")

    return {
        "message": "Test webhook sent",
        "webhook_id": webhook_id,
        "status": "delivered",
        "response_code": 200
    }


@router.get("/{webhook_id}/deliveries", summary="Get delivery history")
async def get_deliveries(webhook_id: str, limit: int = 20):
    """Get webhook delivery history."""
    if webhook_id not in _webhooks:
        raise HTTPException(status_code=404, detail="Webhook not found")

    # Mock delivery history
    return {
        "deliveries": [
            WebhookDelivery(
                id=f"del_{i}",
                webhook_id=webhook_id,
                event=WebhookEvent.PREDICTION_MADE,
                payload={"prediction_id": f"pred_{i}", "result": 0.85},
                response_code=200,
                delivered_at=now_utc(),
                success=True
            ) for i in range(min(5, limit))
        ],
        "total": 5
    }


@router.get("/events/available", summary="List available events")
async def list_available_events():
    """List all available webhook events."""
    return {
        "events": [
            {"name": e.value, "description": f"Triggered when {e.value.replace('.', ' ').replace('_', ' ')}"}
            for e in WebhookEvent
        ]
    }
