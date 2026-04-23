"""
IEAP Application Factory with All New Features

This module integrates all the production-ready enhancements
into the main FastAPI application.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import Settings

logger = logging.getLogger(__name__)


def create_production_app(settings: Settings | None = None) -> FastAPI:
    """
    Create production-ready FastAPI application with all enhancements.
    
    Features included:
    - GraphQL API
    - WebSocket Hub
    - Advanced Rate Limiting
    - Circuit Breakers
    - Event Bus
    - Health Aggregation
    - Plugin System
    - Admin Dashboard
    - Model Explainability
    """
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application lifespan manager"""
        logger.info("Starting IEAP Production Application...")

        # Initialize all systems
        await initialize_systems(app, settings)

        yield

        # Cleanup
        await cleanup_systems(app)
        logger.info("IEAP Application shutdown complete")

    app = FastAPI(
        title="IEAP - Intelligent Enterprise Automation Platform",
        description="Production-Ready AI-Powered Enterprise Automation",
        version="2.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Add CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins if hasattr(settings, "cors_origins") else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    # Register all routes
    register_routes(app)

    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": "Welcome to IEAP - Intelligent Enterprise Automation Platform",
            "version": "2.0.0",
            "docs": "/docs",
            "health": "/api/v1/health"
        }

    return app


async def initialize_systems(app: FastAPI, settings: Settings):
    """Initialize all production systems"""

    # 1. Initialize Event Bus
    from events import EventBus
    app.state.event_bus = EventBus()
    await app.state.event_bus.start()
    logger.info("✓ Event Bus initialized")

    # 2. Initialize Health Aggregator
    from health import DiskHealthCheck, HealthAggregator, MemoryHealthCheck
    app.state.health = HealthAggregator()

    # Register default health checks
    app.state.health.register(
        "memory",
        MemoryHealthCheck().check,
        critical=False
    )
    app.state.health.register(
        "disk",
        DiskHealthCheck().check,
        critical=False
    )
    logger.info("✓ Health Aggregator initialized")

    # 3. Initialize Rate Limiter
    from ratelimit import RateLimiter
    app.state.rate_limiter = RateLimiter()
    logger.info("✓ Rate Limiter initialized")

    # 4. Initialize Plugin Manager
    from plugins import PluginManager
    app.state.plugins = PluginManager(app=app)
    await app.state.plugins.initialize()

    # Discover and load plugins
    try:
        await app.state.plugins.discover_plugins("./plugins")
        await app.state.plugins.load_all()
    except Exception as e:
        logger.warning(f"Plugin discovery error (non-fatal): {e}")

    logger.info("✓ Plugin Manager initialized")

    # 5. Initialize WebSocket Manager
    from api.websocket import WebSocketManager
    app.state.ws_manager = WebSocketManager()
    logger.info("✓ WebSocket Manager initialized")

    # 6. Initialize Circuit Breakers
    from resilience import CircuitBreakerRegistry
    app.state.circuit_breakers = CircuitBreakerRegistry()
    logger.info("✓ Circuit Breakers initialized")

    # 7. Initialize Admin Dashboard
    from admin import AdminDashboard
    app.state.admin = AdminDashboard()
    logger.info("✓ Admin Dashboard initialized")

    logger.info("All production systems initialized successfully!")


async def cleanup_systems(app: FastAPI):
    """Cleanup all systems on shutdown"""

    # Stop event bus
    if hasattr(app.state, "event_bus"):
        await app.state.event_bus.stop()

    # Unload plugins
    if hasattr(app.state, "plugins"):
        await app.state.plugins.unload_all()

    # Close WebSocket connections
    if hasattr(app.state, "ws_manager"):
        await app.state.ws_manager.close_all()


def register_routes(app: FastAPI):
    """Register all API routes"""

    # Core API routes
    from api.routes import api_router
    app.include_router(api_router)

    # GraphQL endpoint
    try:
        from api.graphql import graphql_router
        app.include_router(graphql_router)
        logger.info("✓ GraphQL API mounted at /graphql")
    except ImportError as e:
        logger.warning(f"GraphQL not available: {e}")

    # WebSocket endpoints
    try:
        from api.websocket import websocket_router
        app.include_router(websocket_router)
        logger.info("✓ WebSocket endpoints mounted")
    except ImportError as e:
        logger.warning(f"WebSocket not available: {e}")

    # Health endpoints
    try:
        from health import health_router
        app.include_router(health_router)
        logger.info("✓ Health endpoints mounted")
    except ImportError as e:
        logger.warning(f"Health endpoints not available: {e}")

    # Admin endpoints
    try:
        from admin import admin_router
        app.include_router(admin_router)
        logger.info("✓ Admin endpoints mounted at /admin")
    except ImportError as e:
        logger.warning(f"Admin endpoints not available: {e}")


# Application instance for uvicorn
app = create_production_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app_production:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
