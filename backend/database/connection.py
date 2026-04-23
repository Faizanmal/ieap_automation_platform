"""
Database Connection Management

Provides async database connections with:
- Connection pooling
- Health checking
- Transaction management
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Database connection manager with async support.
    """

    def __init__(
        self,
        database_url: str,
        pool_size: int = 20,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        echo: bool = False
    ):
        self.database_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.echo = echo

        self._async_engine = None
        self._sync_engine = None
        self._async_session_factory = None
        self._sync_session_factory = None

    async def initialize(self):
        """Initialize database engines and session factories."""
        logger.info("Initializing database connection...")

        # Async engine for FastAPI
        self._async_engine = create_async_engine(
            self.database_url,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout,
            pool_recycle=self.pool_recycle,
            echo=self.echo,
            future=True
        )

        self._async_session_factory = async_sessionmaker(
            bind=self._async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )

        logger.info("Database connection initialized successfully")

    def initialize_sync(self, sync_url: str):
        """Initialize synchronous engine for migrations and CLI tools."""
        self._sync_engine = create_engine(
            sync_url,
            poolclass=QueuePool,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout,
            pool_recycle=self.pool_recycle,
            echo=self.echo
        )

        self._sync_session_factory = sessionmaker(
            bind=self._sync_engine,
            autocommit=False,
            autoflush=False
        )

    async def close(self):
        """Close all database connections."""
        logger.info("Closing database connections...")

        if self._async_engine:
            await self._async_engine.dispose()

        if self._sync_engine:
            self._sync_engine.dispose()

        logger.info("Database connections closed")

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Async context manager for database sessions.
        
        Usage:
            async with db.session() as session:
                result = await session.execute(query)
        """
        if not self._async_session_factory:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        session = self._async_session_factory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()

    async def get_session(self) -> AsyncSession:
        """Get a new async session (caller is responsible for closing)."""
        if not self._async_session_factory:
            raise RuntimeError("Database not initialized")
        return self._async_session_factory()

    def get_sync_session(self) -> Session:
        """Get a synchronous session."""
        if not self._sync_session_factory:
            raise RuntimeError("Sync database not initialized")
        return self._sync_session_factory()

    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            async with self.session() as session:
                await session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    @property
    def engine(self):
        """Get async engine."""
        return self._async_engine

    @property
    def sync_engine(self):
        """Get sync engine."""
        return self._sync_engine


# Global database instance
_database: DatabaseManager | None = None


def get_database() -> DatabaseManager:
    """Get global database instance."""
    global _database
    if _database is None:
        from config import get_settings
        settings = get_settings()
        _database = DatabaseManager(
            database_url=settings.database.connection_url,
            pool_size=settings.database.pool_size,
            max_overflow=settings.database.max_overflow,
            pool_timeout=settings.database.pool_timeout,
            pool_recycle=settings.database.pool_recycle,
            echo=settings.debug
        )
    return _database


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions."""
    db = get_database()
    async with db.session() as session:
        yield session


async def init_database():
    """Initialize the database (called on app startup)."""
    db = get_database()
    await db.initialize()


async def close_database():
    """Close database connections (called on app shutdown)."""
    global _database
    if _database:
        await _database.close()
        _database = None
