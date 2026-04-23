"""
Integration tests for API endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestHealthEndpoints:
    """Tests for health check endpoints."""

    async def test_liveness_probe(self, client: AsyncClient):
        """Test liveness endpoint returns 200."""
        response = await client.get("/health/live")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    async def test_readiness_probe(self, client: AsyncClient):
        """Test readiness endpoint."""
        response = await client.get("/health/ready")

        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data

    async def test_full_health_check(self, client: AsyncClient):
        """Test full health check endpoint."""
        response = await client.get("/health")

        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "components" in data
        assert "version" in data


@pytest.mark.integration
class TestAuthEndpoints:
    """Tests for authentication endpoints."""

    async def test_register_user(self, client: AsyncClient):
        """Test user registration."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "SecurePassword123!"
        })

        # Should return 201 or 400 if user exists
        assert response.status_code in [201, 400]

    async def test_login_success(self, client: AsyncClient, test_user, test_user_data):
        """Test successful login."""
        response = await client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials."""
        response = await client.post("/api/v1/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "WrongPassword123!"
        })

        assert response.status_code == 401

    async def test_protected_endpoint_without_token(self, client: AsyncClient):
        """Test accessing protected endpoint without token."""
        response = await client.get("/api/v1/models")

        assert response.status_code == 401

    async def test_protected_endpoint_with_token(
        self,
        authenticated_client: AsyncClient
    ):
        """Test accessing protected endpoint with valid token."""
        response = await authenticated_client.get("/api/v1/models")

        assert response.status_code == 200


@pytest.mark.integration
class TestModelEndpoints:
    """Tests for ML model endpoints."""

    async def test_list_models(self, authenticated_client: AsyncClient):
        """Test listing models."""
        response = await authenticated_client.get("/api/v1/models")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    async def test_get_model_not_found(self, authenticated_client: AsyncClient):
        """Test getting non-existent model."""
        response = await authenticated_client.get(
            "/api/v1/models/nonexistent-id"
        )

        assert response.status_code == 404

    async def test_get_model(
        self,
        authenticated_client: AsyncClient,
        test_model
    ):
        """Test getting existing model."""
        response = await authenticated_client.get(
            f"/api/v1/models/{test_model.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_model.id
        assert data["name"] == test_model.name


@pytest.mark.integration
class TestPredictionEndpoints:
    """Tests for prediction endpoints."""

    async def test_prediction_unauthorized(self, client: AsyncClient):
        """Test prediction without auth."""
        response = await client.post("/api/v1/predictions", json={
            "model_id": "test-model",
            "input": {"feature": 1.0}
        })

        assert response.status_code == 401

    async def test_prediction_model_not_found(
        self,
        authenticated_client: AsyncClient
    ):
        """Test prediction with non-existent model."""
        response = await authenticated_client.post("/api/v1/predictions", json={
            "model_id": "nonexistent-model",
            "input": {"feature": 1.0}
        })

        assert response.status_code == 404
