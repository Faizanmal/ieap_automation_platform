"""
Repository Pattern Implementation

Provides data access layer with:
- CRUD operations
- Query builders
- Pagination
- Filtering
"""

from abc import ABC
from datetime import datetime
from typing import Any, Generic, TypeVar

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Base, MLModel, Prediction, User

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType], ABC):
    """
    Base repository with common CRUD operations.
    """

    def __init__(self, session: AsyncSession, model: type[ModelType]):
        self.session = session
        self.model = model

    async def get(self, id: str) -> ModelType | None:
        """Get entity by ID."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: dict[str, Any] | None = None
    ) -> list[ModelType]:
        """Get multiple entities with pagination."""
        query = select(self.model)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)

        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """Count entities."""
        query = select(func.count()).select_from(self.model)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def create(self, **kwargs) -> ModelType:
        """Create a new entity."""
        entity = self.model(**kwargs)
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def update(self, id: str, **kwargs) -> ModelType | None:
        """Update an entity."""
        entity = await self.get(id)
        if entity:
            for key, value in kwargs.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
            await self.session.flush()
            await self.session.refresh(entity)
        return entity

    async def delete(self, id: str) -> bool:
        """Delete an entity."""
        entity = await self.get(id)
        if entity:
            await self.session.delete(entity)
            await self.session.flush()
            return True
        return False


class UserRepository(BaseRepository[User]):
    """Repository for User operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        """Get user by username."""
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_active_users(
        self,
        tenant_id: str | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[User]:
        """Get active users, optionally filtered by tenant."""
        query = select(User).where(User.is_active == True)

        if tenant_id:
            query = query.where(User.tenant_id == tenant_id)

        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def search(
        self,
        query: str,
        skip: int = 0,
        limit: int = 20
    ) -> list[User]:
        """Search users by email or username."""
        search_query = select(User).where(
            or_(
                User.email.ilike(f"%{query}%"),
                User.username.ilike(f"%{query}%")
            )
        ).offset(skip).limit(limit)

        result = await self.session.execute(search_query)
        return list(result.scalars().all())


class MLModelRepository(BaseRepository[MLModel]):
    """Repository for ML Model operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, MLModel)

    async def get_by_name_version(
        self,
        name: str,
        version: str
    ) -> MLModel | None:
        """Get model by name and version."""
        result = await self.session.execute(
            select(MLModel).where(
                and_(MLModel.name == name, MLModel.version == version)
            )
        )
        return result.scalar_one_or_none()

    async def get_deployed_models(
        self,
        model_type: str | None = None
    ) -> list[MLModel]:
        """Get all deployed models."""
        query = select(MLModel).where(MLModel.status == "deployed")

        if model_type:
            query = query.where(MLModel.model_type == model_type)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_latest_version(self, name: str) -> MLModel | None:
        """Get the latest version of a model."""
        result = await self.session.execute(
            select(MLModel)
            .where(MLModel.name == name)
            .order_by(MLModel.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class PredictionRepository(BaseRepository[Prediction]):
    """Repository for Prediction operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Prediction)

    async def get_by_model(
        self,
        model_id: str,
        skip: int = 0,
        limit: int = 100,
        start_date: datetime | None = None,
        end_date: datetime | None = None
    ) -> list[Prediction]:
        """Get predictions for a model with optional date filtering."""
        query = select(Prediction).where(Prediction.model_id == model_id)

        if start_date:
            query = query.where(Prediction.created_at >= start_date)
        if end_date:
            query = query.where(Prediction.created_at <= end_date)

        query = query.order_by(Prediction.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_model_stats(
        self,
        model_id: str,
        start_date: datetime | None = None
    ) -> dict[str, Any]:
        """Get prediction statistics for a model."""
        query = select(
            func.count(Prediction.id).label("total"),
            func.avg(Prediction.latency_ms).label("avg_latency"),
            func.min(Prediction.latency_ms).label("min_latency"),
            func.max(Prediction.latency_ms).label("max_latency")
        ).where(Prediction.model_id == model_id)

        if start_date:
            query = query.where(Prediction.created_at >= start_date)

        result = await self.session.execute(query)
        row = result.one()

        return {
            "total_predictions": row.total or 0,
            "avg_latency_ms": float(row.avg_latency or 0),
            "min_latency_ms": float(row.min_latency or 0),
            "max_latency_ms": float(row.max_latency or 0)
        }
