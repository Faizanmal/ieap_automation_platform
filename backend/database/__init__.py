"""
Enterprise Database Layer

Provides:
- SQLAlchemy ORM models
- Async database sessions
- Connection pooling
- Repository pattern
- Alembic migrations support
"""

from .connection import (
    DatabaseManager,
    close_database,
    get_async_session,
    get_database,
    init_database,
)
from .models import (
    APIKey,
    AuditLog,
    Base,
    Decision,
    MLModel,
    Pipeline,
    Prediction,
    Task,
    User,
    Webhook,
)
from .repositories import (
    BaseRepository,
    MLModelRepository,
    PredictionRepository,
    UserRepository,
)

__all__ = [
    # Connection
    "get_database",
    "get_async_session",
    "init_database",
    "close_database",
    "DatabaseManager",

    # Models
    "Base",
    "User",
    "APIKey",
    "MLModel",
    "Prediction",
    "Pipeline",
    "Task",
    "Decision",
    "AuditLog",
    "Webhook",

    # Repositories
    "BaseRepository",
    "UserRepository",
    "MLModelRepository",
    "PredictionRepository"
]
