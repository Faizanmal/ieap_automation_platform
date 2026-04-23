"""Initial migration - create all tables

Revision ID: 001
Revises:
Create Date: 2024-01-15

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("is_verified", sa.Boolean(), default=False),
        sa.Column("is_superuser", sa.Boolean(), default=False),
        sa.Column("roles", postgresql.ARRAY(sa.String()), default=[]),
        sa.Column("permissions", postgresql.ARRAY(sa.String()), default=[]),
        sa.Column("tenant_id", sa.String(36), nullable=True),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column("mfa_enabled", sa.Boolean(), default=False),
        sa.Column("mfa_secret", sa.String(255), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), default={}),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])
    op.create_index("ix_users_tenant_active", "users", ["tenant_id", "is_active"])

    # Create api_keys table
    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("key_hash", sa.String(64), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("scopes", postgresql.ARRAY(sa.String()), default=[]),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rate_limit", sa.Integer(), default=1000),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE")
    )
    op.create_index("ix_api_keys_key_hash", "api_keys", ["key_hash"], unique=True)
    op.create_index("ix_api_keys_user_id", "api_keys", ["user_id"])

    # Create ml_models table
    op.create_table(
        "ml_models",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("model_type", sa.String(50), nullable=False),
        sa.Column("version", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), default="ready"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("artifact_path", sa.String(500), nullable=True),
        sa.Column("artifact_size_bytes", sa.Integer(), nullable=True),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), default={}),
        sa.Column("training_config", postgresql.JSONB(astext_type=sa.Text()), default={}),
        sa.Column("feature_names", postgresql.ARRAY(sa.String()), default=[]),
        sa.Column("deployed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deployment_config", postgresql.JSONB(astext_type=sa.Text()), default={}),
        sa.Column("created_by", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", "version", name="uq_model_name_version"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL")
    )
    op.create_index("ix_ml_models_model_type", "ml_models", ["model_type"])
    op.create_index("ix_ml_models_status", "ml_models", ["status"])
    op.create_index("ix_models_type_status", "ml_models", ["model_type", "status"])

    # Create predictions table
    op.create_table(
        "predictions",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("model_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("input_data", postgresql.JSONB(astext_type=sa.Text()), default={}),
        sa.Column("request_id", sa.String(36), nullable=False),
        sa.Column("prediction", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("probability", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("latency_ms", sa.Float(), nullable=False),
        sa.Column("feedback", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("actual_outcome", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["model_id"], ["ml_models.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL")
    )
    op.create_index("ix_predictions_model_id", "predictions", ["model_id"])
    op.create_index("ix_predictions_user_id", "predictions", ["user_id"])
    op.create_index("ix_predictions_request_id", "predictions", ["request_id"])
    op.create_index("ix_predictions_model_created", "predictions", ["model_id", "created_at"])

    # Create pipelines table
    op.create_table(
        "pipelines",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), default="idle"),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("source_config", postgresql.JSONB(astext_type=sa.Text()), default={}),
        sa.Column("destination_config", postgresql.JSONB(astext_type=sa.Text()), default={}),
        sa.Column("transformations", postgresql.JSONB(astext_type=sa.Text()), default=[]),
        sa.Column("schedule", sa.String(100), nullable=True),
        sa.Column("last_run", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run", sa.DateTime(timezone=True), nullable=True),
        sa.Column("records_processed", sa.Integer(), default=0),
        sa.Column("records_failed", sa.Integer(), default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("ix_pipelines_status", "pipelines", ["status"])

    # Create tasks table
    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("task_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), default="pending"),
        sa.Column("priority", sa.String(20), default="medium"),
        sa.Column("assigned_agent", sa.String(100), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), default={}),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), default=0),
        sa.Column("max_retries", sa.Integer(), default=3),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("ix_tasks_task_type", "tasks", ["task_type"])
    op.create_index("ix_tasks_status", "tasks", ["status"])
    op.create_index("ix_tasks_assigned_agent", "tasks", ["assigned_agent"])
    op.create_index("ix_tasks_status_priority", "tasks", ["status", "priority"])

    # Create decisions table
    op.create_table(
        "decisions",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("domain", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), default="pending"),
        sa.Column("impact", sa.String(20), default="low"),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=False),
        sa.Column("options", postgresql.JSONB(astext_type=sa.Text()), default=[]),
        sa.Column("selected_option", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("cost_estimate", sa.Float(), default=0),
        sa.Column("expected_benefit", sa.Float(), default=0),
        sa.Column("requires_approval", sa.Boolean(), default=False),
        sa.Column("approved_by", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"], ondelete="SET NULL")
    )
    op.create_index("ix_decisions_domain", "decisions", ["domain"])
    op.create_index("ix_decisions_status", "decisions", ["status"])

    # Create audit_logs table
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), default="info"),
        sa.Column("user_id", sa.String(36), nullable=True),
        sa.Column("username", sa.String(100), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("resource_id", sa.String(36), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), default="success"),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), default={}),
        sa.Column("request_id", sa.String(36), nullable=True),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("ix_audit_logs_timestamp", "audit_logs", ["timestamp"])
    op.create_index("ix_audit_logs_event_type", "audit_logs", ["event_type"])
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_user_time", "audit_logs", ["user_id", "timestamp"])
    op.create_index("ix_audit_logs_resource", "audit_logs", ["resource_type", "resource_id"])

    # Create webhooks table
    op.create_table(
        "webhooks",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("events", postgresql.ARRAY(sa.String()), default=[]),
        sa.Column("status", sa.String(20), default="active"),
        sa.Column("secret", sa.String(64), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("last_triggered", sa.DateTime(timezone=True), nullable=True),
        sa.Column("success_count", sa.Integer(), default=0),
        sa.Column("failure_count", sa.Integer(), default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE")
    )
    op.create_index("ix_webhooks_user_id", "webhooks", ["user_id"])


def downgrade() -> None:
    op.drop_table("webhooks")
    op.drop_table("audit_logs")
    op.drop_table("decisions")
    op.drop_table("tasks")
    op.drop_table("pipelines")
    op.drop_table("predictions")
    op.drop_table("ml_models")
    op.drop_table("api_keys")
    op.drop_table("users")
