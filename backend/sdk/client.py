"""
IEAP SDK Client

Async-first Python client with sync wrapper for the IEAP platform.
"""

import asyncio
import logging
from typing import Any

import httpx

from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConnectionError,
    IEAPError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
)
from .models import (
    Analytics,
    APIKey,
    BatchPredictionResponse,
    DataPipeline,
    Decision,
    DecisionStatus,
    MLModel,
    ModelCreateRequest,
    ModelDeployRequest,
    ModelStatus,
    PipelineRunResult,
    PipelineStatus,
    PlatformHealth,
    PredictionResponse,
    TokenResponse,
    User,
)

logger = logging.getLogger(__name__)


class AsyncIEAPClient:
    """
    Async Python client for the IEAP platform.
    
    Usage:
        async with AsyncIEAPClient(api_key="your-api-key") as client:
            models = await client.models.list()
            prediction = await client.predictions.predict("model-id", features={...})
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: str | None = None,
        access_token: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.access_token = access_token
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self._client: httpx.AsyncClient | None = None

        # Sub-clients
        self.auth = _AuthClient(self)
        self.models = _ModelsClient(self)
        self.predictions = _PredictionsClient(self)
        self.pipelines = _PipelinesClient(self)
        self.decisions = _DecisionsClient(self)
        self.health = _HealthClient(self)
        self.analytics = _AnalyticsClient(self)

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def connect(self):
        """Initialize HTTP client"""
        headers = {"Content-Type": "application/json"}

        if self.api_key:
            headers["X-API-Key"] = self.api_key
        elif self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=self.timeout
        )

    async def close(self):
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        **kwargs
    ) -> dict[str, Any]:
        """Make an HTTP request with retry logic"""
        if not self._client:
            await self.connect()

        last_error = None

        for attempt in range(self.max_retries):
            try:
                response = await self._client.request(
                    method,
                    path,
                    params=params,
                    json=json,
                    **kwargs
                )

                # Handle response
                if response.status_code == 200 or response.status_code == 201:
                    return response.json()
                if response.status_code == 204:
                    return {}
                if response.status_code == 401:
                    raise AuthenticationError()
                if response.status_code == 403:
                    raise AuthorizationError()
                if response.status_code == 404:
                    raise NotFoundError("Resource", path)
                if response.status_code == 422:
                    data = response.json()
                    raise ValidationError(data.get("message", "Validation failed"), data.get("errors", {}))
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    raise RateLimitError(retry_after)
                if response.status_code >= 500:
                    raise ServerError()
                raise IEAPError(f"Unexpected status code: {response.status_code}")

            except httpx.TimeoutException:
                last_error = TimeoutError()
            except httpx.ConnectError:
                last_error = ConnectionError()
            except IEAPError:
                raise
            except Exception as e:
                last_error = IEAPError(str(e))

            # Retry with exponential backoff
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay * (2 ** attempt))

        raise last_error or IEAPError("Request failed after retries")


class _AuthClient:
    """Authentication operations"""

    def __init__(self, client: AsyncIEAPClient):
        self._client = client

    async def login(self, email: str, password: str) -> TokenResponse:
        """Login with email and password"""
        data = await self._client._request(
            "POST",
            "/api/v1/auth/login",
            json={"email": email, "password": password}
        )
        return TokenResponse(**data)

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresh access token"""
        data = await self._client._request(
            "POST",
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        return TokenResponse(**data)

    async def me(self) -> User:
        """Get current user"""
        data = await self._client._request("GET", "/api/v1/auth/me")
        return User(**data)

    async def create_api_key(self, name: str, scopes: list[str] = None) -> APIKey:
        """Create a new API key"""
        data = await self._client._request(
            "POST",
            "/api/v1/auth/api-keys",
            json={"name": name, "scopes": scopes or ["read"]}
        )
        return APIKey(**data)


class _ModelsClient:
    """ML model operations"""

    def __init__(self, client: AsyncIEAPClient):
        self._client = client

    async def list(
        self,
        status: ModelStatus | None = None,
        page: int = 1,
        page_size: int = 20
    ) -> list[MLModel]:
        """List all models"""
        params = {"page": page, "page_size": page_size}
        if status:
            params["status"] = status.value

        data = await self._client._request("GET", "/api/v1/models", params=params)
        return [MLModel(**m) for m in data.get("items", data)]

    async def get(self, model_id: str) -> MLModel:
        """Get a model by ID"""
        data = await self._client._request("GET", f"/api/v1/models/{model_id}")
        return MLModel(**data)

    async def create(self, request: ModelCreateRequest) -> MLModel:
        """Create a new model"""
        data = await self._client._request(
            "POST",
            "/api/v1/models",
            json=request.model_dump()
        )
        return MLModel(**data)

    async def deploy(self, model_id: str, request: ModelDeployRequest | None = None) -> MLModel:
        """Deploy a model"""
        json_data = request.model_dump() if request else {}
        data = await self._client._request(
            "POST",
            f"/api/v1/models/{model_id}/deploy",
            json=json_data
        )
        return MLModel(**data)

    async def undeploy(self, model_id: str) -> MLModel:
        """Undeploy a model"""
        data = await self._client._request("POST", f"/api/v1/models/{model_id}/undeploy")
        return MLModel(**data)

    async def delete(self, model_id: str) -> bool:
        """Delete a model"""
        await self._client._request("DELETE", f"/api/v1/models/{model_id}")
        return True


class _PredictionsClient:
    """Prediction operations"""

    def __init__(self, client: AsyncIEAPClient):
        self._client = client

    async def predict(
        self,
        model_id: str,
        features: dict[str, Any],
        include_explanation: bool = False
    ) -> PredictionResponse:
        """Make a single prediction"""
        data = await self._client._request(
            "POST",
            "/api/v1/predictions",
            json={
                "model_id": model_id,
                "features": features,
                "include_explanation": include_explanation
            }
        )
        return PredictionResponse(**data)

    async def batch_predict(
        self,
        model_id: str,
        instances: list[dict[str, Any]],
        include_explanations: bool = False
    ) -> BatchPredictionResponse:
        """Make batch predictions"""
        data = await self._client._request(
            "POST",
            "/api/v1/predictions/batch",
            json={
                "model_id": model_id,
                "instances": instances,
                "include_explanations": include_explanations
            }
        )
        return BatchPredictionResponse(**data)

    async def stream(
        self,
        model_id: str,
        features_stream,  # AsyncIterator[Dict[str, Any]]
        include_explanation: bool = False
    ):
        """Stream predictions (async generator)"""
        async for features in features_stream:
            prediction = await self.predict(model_id, features, include_explanation)
            yield prediction


class _PipelinesClient:
    """Pipeline operations"""

    def __init__(self, client: AsyncIEAPClient):
        self._client = client

    async def list(self, status: PipelineStatus | None = None) -> list[DataPipeline]:
        """List all pipelines"""
        params = {}
        if status:
            params["status"] = status.value

        data = await self._client._request("GET", "/api/v1/pipelines", params=params)
        return [DataPipeline(**p) for p in data.get("items", data)]

    async def get(self, pipeline_id: str) -> DataPipeline:
        """Get a pipeline by ID"""
        data = await self._client._request("GET", f"/api/v1/pipelines/{pipeline_id}")
        return DataPipeline(**data)

    async def run(self, pipeline_id: str, parameters: dict[str, Any] | None = None) -> PipelineRunResult:
        """Trigger a pipeline run"""
        data = await self._client._request(
            "POST",
            f"/api/v1/pipelines/{pipeline_id}/run",
            json={"parameters": parameters or {}}
        )
        return PipelineRunResult(**data)

    async def pause(self, pipeline_id: str) -> DataPipeline:
        """Pause a pipeline"""
        data = await self._client._request("POST", f"/api/v1/pipelines/{pipeline_id}/pause")
        return DataPipeline(**data)

    async def resume(self, pipeline_id: str) -> DataPipeline:
        """Resume a pipeline"""
        data = await self._client._request("POST", f"/api/v1/pipelines/{pipeline_id}/resume")
        return DataPipeline(**data)


class _DecisionsClient:
    """Decision operations"""

    def __init__(self, client: AsyncIEAPClient):
        self._client = client

    async def list(
        self,
        status: DecisionStatus | None = None,
        limit: int = 20
    ) -> list[Decision]:
        """List decisions"""
        params = {"limit": limit}
        if status:
            params["status"] = status.value

        data = await self._client._request("GET", "/api/v1/decisions", params=params)
        return [Decision(**d) for d in data.get("items", data)]

    async def get(self, decision_id: str) -> Decision:
        """Get a decision by ID"""
        data = await self._client._request("GET", f"/api/v1/decisions/{decision_id}")
        return Decision(**data)

    async def approve(self, decision_id: str) -> Decision:
        """Approve a pending decision"""
        data = await self._client._request("POST", f"/api/v1/decisions/{decision_id}/approve")
        return Decision(**data)

    async def reject(self, decision_id: str, reason: str) -> Decision:
        """Reject a pending decision"""
        data = await self._client._request(
            "POST",
            f"/api/v1/decisions/{decision_id}/reject",
            json={"reason": reason}
        )
        return Decision(**data)


class _HealthClient:
    """Health check operations"""

    def __init__(self, client: AsyncIEAPClient):
        self._client = client

    async def check(self) -> PlatformHealth:
        """Get platform health status"""
        data = await self._client._request("GET", "/api/v1/health")
        return PlatformHealth(**data)

    async def ready(self) -> bool:
        """Check if platform is ready"""
        try:
            data = await self._client._request("GET", "/api/v1/health/ready")
            return data.get("ready", False)
        except Exception:
            return False

    async def live(self) -> bool:
        """Check if platform is alive"""
        try:
            data = await self._client._request("GET", "/api/v1/health/live")
            return data.get("live", False)
        except Exception:
            return False


class _AnalyticsClient:
    """Analytics operations"""

    def __init__(self, client: AsyncIEAPClient):
        self._client = client

    async def summary(self) -> Analytics:
        """Get analytics summary"""
        data = await self._client._request("GET", "/api/v1/analytics/summary")
        return Analytics(**data)

    async def predictions_over_time(self, days: int = 30) -> list[dict[str, Any]]:
        """Get predictions over time"""
        data = await self._client._request(
            "GET",
            "/api/v1/analytics/predictions",
            params={"days": days}
        )
        return data.get("data", [])


class IEAPClient:
    """
    Synchronous wrapper for AsyncIEAPClient.
    
    Usage:
        with IEAPClient(api_key="your-api-key") as client:
            models = client.models.list()
            prediction = client.predictions.predict("model-id", features={...})
    """

    def __init__(self, **kwargs):
        self._async_client = AsyncIEAPClient(**kwargs)
        self._loop: asyncio.AbstractEventLoop | None = None

    def __enter__(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._async_client.connect())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._loop.run_until_complete(self._async_client.close())
        self._loop.close()
        self._loop = None

    def _run(self, coro):
        """Run a coroutine synchronously"""
        if self._loop is None:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        return self._loop.run_until_complete(coro)

    @property
    def auth(self):
        return _SyncAuthClient(self._async_client.auth, self._run)

    @property
    def models(self):
        return _SyncModelsClient(self._async_client.models, self._run)

    @property
    def predictions(self):
        return _SyncPredictionsClient(self._async_client.predictions, self._run)

    @property
    def pipelines(self):
        return _SyncPipelinesClient(self._async_client.pipelines, self._run)

    @property
    def decisions(self):
        return _SyncDecisionsClient(self._async_client.decisions, self._run)

    @property
    def health(self):
        return _SyncHealthClient(self._async_client.health, self._run)

    @property
    def analytics(self):
        return _SyncAnalyticsClient(self._async_client.analytics, self._run)


# Sync client wrappers
class _SyncAuthClient:
    def __init__(self, async_client, run):
        self._async = async_client
        self._run = run

    def login(self, email: str, password: str) -> TokenResponse:
        return self._run(self._async.login(email, password))

    def me(self) -> User:
        return self._run(self._async.me())


class _SyncModelsClient:
    def __init__(self, async_client, run):
        self._async = async_client
        self._run = run

    def list(self, **kwargs) -> list[MLModel]:
        return self._run(self._async.list(**kwargs))

    def get(self, model_id: str) -> MLModel:
        return self._run(self._async.get(model_id))

    def deploy(self, model_id: str, **kwargs) -> MLModel:
        return self._run(self._async.deploy(model_id, **kwargs))


class _SyncPredictionsClient:
    def __init__(self, async_client, run):
        self._async = async_client
        self._run = run

    def predict(self, model_id: str, features: dict[str, Any], **kwargs) -> PredictionResponse:
        return self._run(self._async.predict(model_id, features, **kwargs))

    def batch_predict(self, model_id: str, instances: list[dict[str, Any]], **kwargs) -> BatchPredictionResponse:
        return self._run(self._async.batch_predict(model_id, instances, **kwargs))


class _SyncPipelinesClient:
    def __init__(self, async_client, run):
        self._async = async_client
        self._run = run

    def list(self, **kwargs) -> list[DataPipeline]:
        return self._run(self._async.list(**kwargs))

    def run(self, pipeline_id: str, **kwargs) -> PipelineRunResult:
        return self._run(self._async.run(pipeline_id, **kwargs))


class _SyncDecisionsClient:
    def __init__(self, async_client, run):
        self._async = async_client
        self._run = run

    def list(self, **kwargs) -> list[Decision]:
        return self._run(self._async.list(**kwargs))

    def approve(self, decision_id: str) -> Decision:
        return self._run(self._async.approve(decision_id))


class _SyncHealthClient:
    def __init__(self, async_client, run):
        self._async = async_client
        self._run = run

    def check(self) -> PlatformHealth:
        return self._run(self._async.check())

    def ready(self) -> bool:
        return self._run(self._async.ready())


class _SyncAnalyticsClient:
    def __init__(self, async_client, run):
        self._async = async_client
        self._run = run

    def summary(self) -> Analytics:
        return self._run(self._async.summary())
