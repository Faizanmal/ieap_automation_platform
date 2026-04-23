"""
Integration tests for database operations.
"""

from datetime import datetime

import pytest


@pytest.mark.integration
class TestUserRepository:
    """Tests for user repository."""

    async def test_create_user(self, db_session):
        """Test creating a user."""
        from database.repositories import UserRepository
        from security.encryption import PasswordHasher

        repo = UserRepository(db_session)
        hasher = PasswordHasher()

        user = await repo.create(
            email="test@example.com",
            username="testuser",
            hashed_password=hasher.hash("password123"),
            roles=["user"]
        )

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.username == "testuser"

    async def test_get_user_by_email(self, db_session, test_user):
        """Test getting user by email."""
        from database.repositories import UserRepository

        repo = UserRepository(db_session)
        user = await repo.get_by_email(test_user.email)

        assert user is not None
        assert user.id == test_user.id

    async def test_get_user_by_username(self, db_session, test_user):
        """Test getting user by username."""
        from database.repositories import UserRepository

        repo = UserRepository(db_session)
        user = await repo.get_by_username(test_user.username)

        assert user is not None
        assert user.id == test_user.id

    async def test_update_user(self, db_session, test_user):
        """Test updating a user."""
        from database.repositories import UserRepository

        repo = UserRepository(db_session)
        updated = await repo.update(
            test_user.id,
            is_verified=True,
            last_login=datetime.utcnow()
        )

        assert updated is not None
        assert updated.is_verified is True
        assert updated.last_login is not None

    async def test_delete_user(self, db_session, test_user):
        """Test deleting a user."""
        from database.repositories import UserRepository

        repo = UserRepository(db_session)
        result = await repo.delete(test_user.id)

        assert result is True

        # Verify deletion
        user = await repo.get(test_user.id)
        assert user is None


@pytest.mark.integration
class TestMLModelRepository:
    """Tests for ML model repository."""

    async def test_create_model(self, db_session):
        """Test creating an ML model."""
        from database.repositories import MLModelRepository

        repo = MLModelRepository(db_session)

        model = await repo.create(
            name="test-model",
            model_type="classification",
            version="1.0.0",
            status="ready",
            metrics={"accuracy": 0.95}
        )

        assert model.id is not None
        assert model.name == "test-model"
        assert model.metrics["accuracy"] == 0.95

    async def test_get_by_name_version(self, db_session, test_model):
        """Test getting model by name and version."""
        from database.repositories import MLModelRepository

        repo = MLModelRepository(db_session)
        model = await repo.get_by_name_version(
            test_model.name,
            test_model.version
        )

        assert model is not None
        assert model.id == test_model.id

    async def test_get_deployed_models(self, db_session, test_model):
        """Test getting deployed models."""
        from database.repositories import MLModelRepository

        repo = MLModelRepository(db_session)
        models = await repo.get_deployed_models()

        assert len(models) >= 1
        assert all(m.status == "deployed" for m in models)


@pytest.mark.integration
class TestPredictionRepository:
    """Tests for prediction repository."""

    async def test_create_prediction(self, db_session, test_model, test_user):
        """Test creating a prediction."""
        import uuid

        from database.repositories import PredictionRepository

        repo = PredictionRepository(db_session)

        prediction = await repo.create(
            model_id=test_model.id,
            user_id=test_user.id,
            input_data={"feature": 1.0},
            request_id=str(uuid.uuid4()),
            prediction={"class": "A", "probability": 0.95},
            latency_ms=15.5
        )

        assert prediction.id is not None
        assert prediction.model_id == test_model.id
        assert prediction.latency_ms == 15.5

    async def test_get_model_stats(self, db_session, test_model):
        """Test getting prediction statistics."""
        from database.repositories import PredictionRepository

        repo = PredictionRepository(db_session)

        # Create some predictions
        import uuid
        for i in range(5):
            await repo.create(
                model_id=test_model.id,
                input_data={"feature": float(i)},
                request_id=str(uuid.uuid4()),
                latency_ms=10.0 + i
            )

        stats = await repo.get_model_stats(test_model.id)

        assert stats["total_predictions"] == 5
        assert stats["avg_latency_ms"] > 0
