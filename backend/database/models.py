"""
SQLAlchemy ORM Models

Enterprise database models for all platform entities.
"""

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all models."""


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


class User(Base, TimestampMixin):
    """User model."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)

    roles: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    permissions: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    tenant_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)

    metadata_: Mapped[dict] = mapped_column(JSONB, default=dict, name="metadata")

    # Relationships
    api_keys: Mapped[list["APIKey"]] = relationship("APIKey", back_populates="user")
    predictions: Mapped[list["Prediction"]] = relationship("Prediction", back_populates="user")

    __table_args__ = (
        Index("ix_users_tenant_active", "tenant_id", "is_active"),
    )


class APIKey(Base, TimestampMixin):
    """API Key model."""
    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    scopes: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    rate_limit: Mapped[int] = mapped_column(Integer, default=1000)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="api_keys")


class MLModel(Base, TimestampMixin):
    """ML Model registry."""
    __tablename__ = "ml_models"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(20), nullable=False)

    status: Mapped[str] = mapped_column(
        String(20),
        default="ready",
        index=True
    )

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Model artifacts
    artifact_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    artifact_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Performance metrics
    metrics: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Training configuration
    training_config: Mapped[dict] = mapped_column(JSONB, default=dict)
    feature_names: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    # Deployment info
    deployed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deployment_config: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Owner
    created_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    predictions: Mapped[list["Prediction"]] = relationship("Prediction", back_populates="model")

    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_model_name_version"),
        Index("ix_models_type_status", "model_type", "status"),
    )


class Prediction(Base, TimestampMixin):
    """Prediction logs."""
    __tablename__ = "predictions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    model_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ml_models.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Request
    input_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    request_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # Response
    prediction: Mapped[Any] = mapped_column(JSONB, nullable=True)
    probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Performance
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)

    # Feedback for model improvement
    feedback: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    actual_outcome: Mapped[Any | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    model: Mapped["MLModel"] = relationship("MLModel", back_populates="predictions")
    user: Mapped[Optional["User"]] = relationship("User", back_populates="predictions")

    __table_args__ = (
        Index("ix_predictions_model_created", "model_id", "created_at"),
    )


class Pipeline(Base, TimestampMixin):
    """Data pipeline definitions."""
    __tablename__ = "pipelines"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="idle", index=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Configuration
    source_config: Mapped[dict] = mapped_column(JSONB, default=dict)
    destination_config: Mapped[dict] = mapped_column(JSONB, default=dict)
    transformations: Mapped[list[dict]] = mapped_column(JSONB, default=list)

    # Scheduling
    schedule: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Execution info
    last_run: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Metrics
    records_processed: Mapped[int] = mapped_column(Integer, default=0)
    records_failed: Mapped[int] = mapped_column(Integer, default=0)


class Task(Base, TimestampMixin):
    """Task queue items."""
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    priority: Mapped[str] = mapped_column(String(20), default="medium")

    # Execution
    assigned_agent: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Payload and result
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Retry info
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)

    __table_args__ = (
        Index("ix_tasks_status_priority", "status", "priority"),
    )


class Decision(Base, TimestampMixin):
    """Autonomous decisions log."""
    __tablename__ = "decisions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    domain: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    impact: Mapped[str] = mapped_column(String(20), default="low")

    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)

    # Options and selection
    options: Mapped[list[dict]] = mapped_column(JSONB, default=list)
    selected_option: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Cost/benefit
    cost_estimate: Mapped[float] = mapped_column(Float, default=0)
    expected_benefit: Mapped[float] = mapped_column(Float, default=0)

    # Approval workflow
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditLog(Base):
    """Audit log entries."""
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )

    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), default="info")

    # Actor
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    # Resource
    resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # Action
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="success")

    # Details
    details: Mapped[dict] = mapped_column(JSONB, default=dict)
    request_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    __table_args__ = (
        Index("ix_audit_logs_user_time", "user_id", "timestamp"),
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
    )


class Webhook(Base, TimestampMixin):
    """Webhook configurations."""
    __tablename__ = "webhooks"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)

    events: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    status: Mapped[str] = mapped_column(String(20), default="active")

    secret: Mapped[str | None] = mapped_column(String(64), nullable=True)

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Statistics
    last_triggered: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
