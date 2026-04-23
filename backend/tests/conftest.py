"""
Pytest Configuration and Fixtures

Central configuration for all tests with reusable fixtures.
"""

import asyncio
import os
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient

# Set test environment before importing app modules
os.environ["APP_ENV"] = "testing"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost:5432/test_db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["ENCRYPTION_KEY"] = "dGVzdC1lbmNyeXB0aW9uLWtleS0zMmJ5dGVz"


# ============================================================================
# Event Loop Configuration
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="session")
async def db_engine():
    """Create database engine for testing."""
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(
        os.environ["DATABASE_URL"],
        echo=False,
        pool_size=5
    )
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine):
    """Create a fresh database session for each test."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from database.models import Base

    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()

    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ============================================================================
# Application Fixtures
# ============================================================================

@pytest.fixture
async def app():
    """Create FastAPI application for testing."""
    from api.main import create_app

    application = create_app()
    return application


@pytest.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for API testing."""
    from httpx import ASGITransport
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Content-Type": "application/json"}
    ) as ac:
        yield ac


@pytest.fixture
async def authenticated_client(client, test_user, auth_token) -> AsyncClient:
    """Create authenticated HTTP client."""
    client.headers["Authorization"] = f"Bearer {auth_token}"
    return client


# ============================================================================
# User Fixtures
# ============================================================================

@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "SecurePassword123!",
        "roles": ["user"],
        "permissions": []
    }


@pytest.fixture
async def test_user(db_session, test_user_data):
    """Create a test user in the database."""
    from database.models import User
    from security.encryption import PasswordHasher

    hasher = PasswordHasher()

    user = User(
        email=test_user_data["email"],
        username=test_user_data["username"],
        hashed_password=hasher.hash(test_user_data["password"]),
        roles=test_user_data["roles"],
        is_active=True,
        is_verified=True
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest.fixture
async def admin_user(db_session):
    """Create an admin user for testing."""
    from database.models import User
    from security.encryption import PasswordHasher

    hasher = PasswordHasher()

    user = User(
        email="admin@example.com",
        username="admin",
        hashed_password=hasher.hash("AdminPassword123!"),
        roles=["admin"],
        is_active=True,
        is_verified=True,
        is_superuser=True
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest.fixture
def auth_token(test_user):
    """Generate JWT token for test user."""
    from security.authentication import JWTHandler

    handler = JWTHandler(
        secret_key=os.environ["JWT_SECRET_KEY"],
        algorithm="HS256"
    )

    return handler.create_access_token(
        user_id=test_user.id,
        roles=test_user.roles
    )


# ============================================================================
# Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_redis():
    """Mock Redis client for testing without Redis."""
    redis_mock = MagicMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock(return_value=True)
    redis_mock.delete = AsyncMock(return_value=1)
    redis_mock.exists = AsyncMock(return_value=0)
    redis_mock.health_check = AsyncMock(return_value=True)
    return redis_mock


@pytest.fixture
def mock_celery():
    """Mock Celery for testing without workers."""
    celery_mock = MagicMock()
    celery_mock.send_task = MagicMock(return_value=MagicMock(id="test-task-id"))
    return celery_mock


# ============================================================================
# ML Model Fixtures
# ============================================================================

@pytest.fixture
def sample_prediction_input():
    """Sample input data for ML predictions."""
    return {
        "feature1": 1.0,
        "feature2": 2.0,
        "feature3": 3.0,
        "category": "A"
    }


@pytest.fixture
async def test_model(db_session):
    """Create a test ML model in the database."""
    from database.models import MLModel

    model = MLModel(
        name="test-model",
        model_type="classification",
        version="1.0.0",
        status="deployed",
        description="Test model for unit tests",
        metrics={"accuracy": 0.95, "f1_score": 0.93}
    )

    db_session.add(model)
    await db_session.commit()
    await db_session.refresh(model)

    return model


# ============================================================================
# Pipeline Fixtures
# ============================================================================

@pytest.fixture
async def test_pipeline(db_session):
    """Create a test pipeline in the database."""
    from database.models import Pipeline

    pipeline = Pipeline(
        name="test-pipeline",
        description="Test pipeline for unit tests",
        status="idle",
        source_type="csv",
        source_config={"path": "/data/test.csv"},
        destination_config={"table": "test_output"}
    )

    db_session.add(pipeline)
    await db_session.commit()
    await db_session.refresh(pipeline)

    return pipeline


# ============================================================================
# Helper Functions
# ============================================================================

def create_test_token(user_id: str, roles: list = None, expired: bool = False):
    """Helper to create JWT tokens for testing."""
    from datetime import timedelta

    from security.authentication import JWTHandler

    handler = JWTHandler(
        secret_key=os.environ["JWT_SECRET_KEY"],
        algorithm="HS256"
    )

    if expired:
        return handler.create_access_token(
            user_id=user_id,
            roles=roles or ["user"],
            expires_delta=timedelta(seconds=-1)
        )

    return handler.create_access_token(
        user_id=user_id,
        roles=roles or ["user"]
    )
