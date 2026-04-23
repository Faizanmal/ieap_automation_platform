# IEAP Production Features Guide

This document describes all the production-ready features added to transform IEAP into a market-ready enterprise platform.

## Table of Contents

1. [CLI Tool](#cli-tool)
2. [GraphQL API](#graphql-api)
3. [WebSocket Hub](#websocket-hub)
4. [Python SDK](#python-sdk)
5. [Resilience Patterns](#resilience-patterns)
6. [Batch Processing](#batch-processing)
7. [Event Bus](#event-bus)
8. [Model Explainability](#model-explainability)
9. [Advanced Rate Limiting](#advanced-rate-limiting)
10. [Admin Dashboard](#admin-dashboard)
11. [Health Aggregation](#health-aggregation)
12. [Plugin System](#plugin-system)

---

## CLI Tool

Professional command-line interface built with Click and Rich for beautiful terminal output.

### Location
- `cli/main.py`

### Features
- Health checks and system status
- Model management (list, deploy, retire)
- Pipeline operations (run, status)
- Decision engine control
- Interactive mode
- Configuration management

### Usage

```bash
# Check system health
ieap health

# List models
ieap models list

# Run a pipeline
ieap pipelines run my-pipeline

# Interactive mode
ieap interactive
```

---

## GraphQL API

Flexible GraphQL endpoint using Strawberry for efficient data fetching.

### Location
- `api/graphql/schema.py`
- `api/graphql/router.py`

### Features
- Query: models, pipelines, predictions, decisions
- Mutations: create predictions, deployments
- Subscriptions: real-time updates

### Usage

```graphql
# Query models
query {
  models(limit: 10) {
    id
    name
    version
    status
    accuracy
  }
}

# Create prediction
mutation {
  createPrediction(
    modelId: "model-123"
    inputData: "{\"feature\": 1.0}"
  ) {
    id
    prediction
    confidence
  }
}

# Subscribe to updates
subscription {
  modelUpdates {
    id
    event
    timestamp
  }
}
```

---

## WebSocket Hub

Real-time bidirectional communication for live updates.

### Location
- `api/websocket/manager.py`
- `api/websocket/router.py`

### Features
- Connection management with heartbeat
- Channel-based subscriptions
- Broadcast capabilities
- Authentication support
- Connection pooling

### Usage

```python
# Client-side
import websockets

async with websockets.connect("ws://localhost:8000/ws") as ws:
    # Subscribe to channel
    await ws.send('{"type": "subscribe", "channel": "predictions"}')
    
    # Receive updates
    async for message in ws:
        print(f"Update: {message}")
```

---

## Python SDK

Full-featured SDK for integrating IEAP into applications.

### Location
- `sdk/client.py`
- `sdk/models.py`

### Features
- Async and sync clients
- Typed responses with Pydantic
- Sub-clients for each domain
- Automatic retry and error handling
- Connection pooling

### Usage

```python
from sdk import IEAPClient

# Async usage
async with AsyncIEAPClient(base_url="https://api.ieap.io") as client:
    # Make prediction
    result = await client.predictions.create(
        model_id="fraud-detection",
        input_data={"amount": 1000, "merchant": "online"}
    )
    print(f"Prediction: {result.prediction}")

# Sync usage
with IEAPClient(api_key="your-key") as client:
    models = client.models.list()
    for model in models:
        print(f"Model: {model.name}")
```

---

## Resilience Patterns

Enterprise-grade fault tolerance patterns.

### Location
- `resilience/circuit_breaker.py`
- `resilience/retry.py`
- `resilience/bulkhead.py`
- `resilience/timeout.py`
- `resilience/fallback.py`

### Features

#### Circuit Breaker
```python
from resilience import circuit_breaker

@circuit_breaker(failure_threshold=5, recovery_timeout=30)
async def call_external_api():
    return await external_service.fetch()
```

#### Retry with Backoff
```python
from resilience import with_retry, RetryPolicy

@with_retry(max_attempts=3, backoff="exponential")
async def unreliable_operation():
    return await do_something()
```

#### Bulkhead (Concurrency Limiting)
```python
from resilience import Bulkhead

bulkhead = Bulkhead(max_concurrent=10)

@bulkhead.limit
async def limited_operation():
    return await process()
```

---

## Batch Processing

High-performance batch processing with progress tracking.

### Location
- `batch/processor.py`
- `batch/workers.py`

### Features
- Progress tracking and checkpointing
- Resumable jobs
- Parallel processing with worker pools
- Error handling and recovery

### Usage

```python
from batch import BatchProcessor

processor = BatchProcessor(
    worker_count=4,
    batch_size=100
)

# Process items
async def process_item(item):
    return await transform(item)

result = await processor.process(
    items=large_dataset,
    handler=process_item,
    progress_callback=lambda p: print(f"Progress: {p}%")
)
```

---

## Event Bus

Publish-subscribe system for decoupled communication.

### Location
- `events/bus.py`
- `events/decorators.py`

### Features
- Async pub-sub pattern
- Priority-based handlers
- Dead letter queue
- Pre-defined event types
- Decorator-based subscriptions

### Usage

```python
from events import EventBus, ModelDeployedEvent, on_event

bus = EventBus()

# Subscribe with decorator
@on_event(ModelDeployedEvent)
async def handle_deployment(event):
    print(f"Model {event.model_name} deployed!")

# Or subscribe programmatically
bus.subscribe(ModelDeployedEvent, handle_deployment)

# Emit events
await bus.emit(ModelDeployedEvent(
    model_id="123",
    model_name="fraud-detector",
    version="1.0.0"
))
```

---

## Model Explainability

SHAP and LIME integration for ML interpretability.

### Location
- `explainability/explainer.py`
- `explainability/shap_explainer.py`
- `explainability/lime_explainer.py`
- `explainability/visualization.py`

### Features
- SHAP explanations
- LIME explanations
- Feature importance
- Visualization generation
- API-ready output

### Usage

```python
from explainability import ModelExplainer, ExplanationType

explainer = ModelExplainer(
    model=trained_model,
    feature_names=["age", "income", "history"],
    background_data=training_data
)

# Explain single prediction
explanation = explainer.explain(
    instance={"age": 35, "income": 50000, "history": 5},
    method=ExplanationType.SHAP
)

print(f"Top factors: {explanation.top_positive_features}")
print(f"Summary: {explanation.get_summary()}")

# Get API-ready response
api_response = explainer.explain_for_api(instance, include_visualization=True)
```

---

## Advanced Rate Limiting

Tiered rate limiting with quotas and multiple strategies.

### Location
- `ratelimit/limiter.py`
- `ratelimit/strategies.py`
- `ratelimit/middleware.py`
- `ratelimit/decorators.py`

### Features
- Multiple time windows (second, minute, hour, day)
- User tiers (Free, Starter, Professional, Enterprise)
- Daily/monthly quotas
- Multiple algorithms (Token Bucket, Sliding Window, etc.)
- Redis-backed for distributed systems

### Usage

```python
from ratelimit import RateLimiter, RateLimitTier, rate_limit

limiter = RateLimiter(redis_client=redis)

# Check rate limit
result = await limiter.check(
    key=f"user:{user_id}",
    tier=RateLimitTier.PROFESSIONAL
)

if not result.allowed:
    raise HTTPException(429, headers=result.to_headers())

# Decorator-based
@rate_limit(limit=100, window=60)
async def my_endpoint():
    return {"data": "response"}
```

---

## Admin Dashboard

Comprehensive system administration API.

### Location
- `admin/dashboard.py`
- `admin/analytics.py`
- `admin/operations.py`
- `admin/router.py`

### Features
- Real-time system status
- User management
- API key management
- Analytics and reporting
- Maintenance mode control
- Backup management
- Feature flags

### Endpoints

```
GET  /admin/dashboard          # Complete dashboard summary
GET  /admin/analytics/usage    # Usage statistics
GET  /admin/analytics/report   # Generate comprehensive report
GET  /admin/users              # List users
POST /admin/maintenance/enable # Enable maintenance mode
POST /admin/backups            # Create backup
GET  /admin/feature-flags      # Get feature flags
```

---

## Health Aggregation

Dependency-aware health checking with auto-recovery.

### Location
- `health/aggregator.py`
- `health/checks.py`
- `health/recovery.py`
- `health/router.py`

### Features
- Dependency tree management
- Multiple health check types
- Graceful degradation
- Auto-recovery mechanisms
- Kubernetes probes support

### Usage

```python
from health import HealthAggregator, DatabaseHealthCheck

aggregator = HealthAggregator()

# Register checks with dependencies
aggregator.register("database", db_check, critical=True)
aggregator.register("redis", redis_check, dependencies=["database"])
aggregator.register("ml_models", ml_check, dependencies=["redis"])

# Check health
health = await aggregator.check_health()
print(f"Status: {health.status.value}")
print(f"Components: {health.healthy_count}/{len(health.components)}")
```

### Endpoints

```
GET /health           # Full health check
GET /health/live      # Kubernetes liveness probe
GET /health/ready     # Kubernetes readiness probe
GET /health/startup   # Kubernetes startup probe
GET /health/components/{name}  # Check specific component
```

---

## Plugin System

Extensible architecture for custom integrations.

### Location
- `plugins/base.py`
- `plugins/manager.py`
- `plugins/loader.py`
- `plugins/hooks.py`

### Features
- Hot-loadable plugins
- Lifecycle management
- Hook system for extension points
- Dependency resolution
- Configuration per plugin

### Creating a Plugin

```python
from plugins import Plugin, PluginInfo, PluginContext

class MyPlugin(Plugin):
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="my-plugin",
            version="1.0.0",
            description="My custom plugin"
        )
    
    async def on_load(self, context: PluginContext) -> None:
        # Initialize plugin
        self.db = context.get_service("database")
    
    async def on_unload(self) -> None:
        # Cleanup
        pass
    
    def get_routes(self):
        # Return FastAPI routers
        router = APIRouter()
        @router.get("/my-endpoint")
        async def my_endpoint():
            return {"plugin": self.name}
        return [router]
```

### Using Plugins

```python
from plugins import PluginManager

manager = PluginManager(app=fastapi_app)
await manager.initialize()

# Discover and load
await manager.discover_plugins("./plugins")
await manager.load_all()

# Execute hooks
results = await manager.execute_hook("before_prediction", model=model, data=data)
```

---

## Quick Start

### Running with All Features

```bash
# Install dependencies
pip install -r requirements.txt

# Run production app
python app_production.py

# Or with uvicorn
uvicorn app_production:app --host 0.0.0.0 --port 8000
```

### API Endpoints Overview

| Feature | Endpoints |
|---------|-----------|
| REST API | `/api/v1/*` |
| GraphQL | `/graphql` |
| WebSocket | `/ws` |
| Health | `/health/*` |
| Admin | `/admin/*` |
| Docs | `/docs`, `/redoc` |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    IEAP Production Platform                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  REST API   │  │  GraphQL    │  │  WebSocket  │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
│         │                │                │                     │
│  ┌──────┴────────────────┴────────────────┴──────┐             │
│  │              Rate Limiter / Auth              │             │
│  └──────────────────────┬────────────────────────┘             │
│                         │                                       │
│  ┌──────────────────────┴────────────────────────┐             │
│  │                 Event Bus                      │             │
│  └──────────────────────┬────────────────────────┘             │
│         ┌───────────────┼───────────────┐                      │
│  ┌──────┴──────┐ ┌──────┴──────┐ ┌──────┴──────┐              │
│  │   Models    │ │  Decisions  │ │  Pipelines  │              │
│  │  + Explain  │ │   Engine    │ │   + Batch   │              │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘              │
│         └───────────────┼───────────────┘                      │
│  ┌──────────────────────┴────────────────────────┐             │
│  │     Resilience (Circuit Breaker, Retry)       │             │
│  └──────────────────────┬────────────────────────┘             │
│         ┌───────────────┼───────────────┐                      │
│  ┌──────┴──────┐ ┌──────┴──────┐ ┌──────┴──────┐              │
│  │  Database   │ │    Redis    │ │  Plugins    │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┤
│  │  Health Aggregator │ Admin Dashboard │ Monitoring          │
│  └─────────────────────────────────────────────────────────────┤
└─────────────────────────────────────────────────────────────────┘
```

---

## License

MIT License - See LICENSE file for details.
