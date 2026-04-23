"""
Enterprise Settings Configuration

Centralized configuration using Pydantic Settings with full validation,
environment variable support, and secrets management.
"""

import json
from enum import Enum
from functools import lru_cache
from typing import Any

from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Application environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class DatabaseSettings(BaseModel):
    """Database configuration settings"""

    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    name: str = Field(default="ieap_db", description="Database name")
    user: str = Field(default="ieap_user", description="Database user")
    password: SecretStr = Field(default=SecretStr(""), description="Database password")

    # Connection pool settings
    pool_size: int = Field(default=20, ge=1, le=100, description="Connection pool size")
    max_overflow: int = Field(default=10, ge=0, le=50, description="Max overflow connections")
    pool_timeout: int = Field(default=30, ge=5, le=300, description="Pool timeout in seconds")
    pool_recycle: int = Field(default=3600, description="Connection recycle time in seconds")

    # SSL settings
    ssl_mode: str = Field(default="prefer", description="SSL mode")
    ssl_cert_path: str | None = Field(default=None, description="SSL certificate path")

    # Read replicas for scaling
    read_replicas: list[str] = Field(default_factory=list, description="Read replica hosts")

    @property
    def connection_url(self) -> str:
        """Generate PostgreSQL connection URL"""
        password = self.password.get_secret_value() if self.password else ""
        return f"postgresql+asyncpg://{self.user}:{password}@{self.host}:{self.port}/{self.name}"

    @property
    def sync_connection_url(self) -> str:
        """Generate synchronous PostgreSQL connection URL"""
        password = self.password.get_secret_value() if self.password else ""
        return f"postgresql://{self.user}:{password}@{self.host}:{self.port}/{self.name}"


class SecuritySettings(BaseModel):
    """Security and authentication settings"""

    @staticmethod
    def _parse_str_list(value: str) -> list[str] | str:
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if item is not None]
            except json.JSONDecodeError:
                pass
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("oauth2_providers", mode="before")
    def parse_oauth2_providers(cls, value: list[str] | str) -> list[str] | str:
        return cls._parse_str_list(value)

    @field_validator("cors_origins", mode="before")
    def parse_cors_origins(cls, value: list[str] | str) -> list[str] | str:
        return cls._parse_str_list(value)

    # JWT Configuration
    jwt_secret_key: SecretStr = Field(
        default=SecretStr("change-me-in-production-use-strong-secret-key"),
        description="JWT secret key for token signing"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_access_token_expire_minutes: int = Field(default=30, ge=5, le=1440)
    jwt_refresh_token_expire_days: int = Field(default=7, ge=1, le=30)

    # API Key settings
    api_key_header: str = Field(default="X-API-Key", description="API key header name")
    api_key_prefix: str = Field(default="ieap_", description="API key prefix")

    # OAuth2 settings
    oauth2_enabled: bool = Field(default=False, description="Enable OAuth2 authentication", env="OAUTH2_ENABLED")
    oauth2_providers: list[str] = Field(default_factory=list, description="Enabled OAuth2 providers", env="OAUTH2_PROVIDERS")
    oauth2_google_client_id: str = Field(default="", description="Google OAuth2 client ID", env="OAUTH2_GOOGLE_CLIENT_ID")
    oauth2_google_client_secret: SecretStr = Field(default=SecretStr(""), description="Google OAuth2 client secret", env="OAUTH2_GOOGLE_CLIENT_SECRET")
    oauth2_google_redirect_uri: str = Field(default="http://localhost:8000/api/v1/auth/oauth/google/callback", description="Google OAuth2 redirect URI", env="OAUTH2_GOOGLE_REDIRECT_URI")

    # Encryption settings
    encryption_key: SecretStr = Field(
        default=SecretStr(""),
        description="Data encryption key (Fernet compatible)",
        env="ENCRYPTION_KEY"
    )

    # Password policy
    password_min_length: int = Field(default=12, ge=8, le=128)
    password_require_uppercase: bool = Field(default=True)
    password_require_lowercase: bool = Field(default=True)
    password_require_digits: bool = Field(default=True)
    password_require_special: bool = Field(default=True)

    # Rate limiting
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_requests_per_minute: int = Field(default=60, ge=1, le=10000)
    rate_limit_burst: int = Field(default=100, ge=1, le=1000)

    # CORS settings
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins",
        env="CORS_ORIGINS"
    )
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")

    # Security headers
    enable_hsts: bool = Field(default=True, description="Enable HTTP Strict Transport Security")
    enable_csp: bool = Field(default=True, description="Enable Content Security Policy")

    # Audit logging
    audit_log_enabled: bool = Field(default=True)
    audit_log_retention_days: int = Field(default=90, ge=7, le=365)


class CacheSettings(BaseModel):
    """Caching configuration settings"""

    # Redis configuration
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_db: int = Field(default=0, ge=0, le=15, description="Redis database number")
    redis_password: SecretStr = Field(default=SecretStr(""), description="Redis password")
    redis_ssl: bool = Field(default=False, description="Enable Redis SSL")

    # Connection pool
    redis_pool_size: int = Field(default=10, ge=1, le=100)
    redis_socket_timeout: int = Field(default=5, ge=1, le=60)
    redis_socket_connect_timeout: int = Field(default=5, ge=1, le=60)

    # Cache settings
    default_ttl: int = Field(default=3600, description="Default cache TTL in seconds")
    max_memory: str = Field(default="256mb", description="Max cache memory")

    # Cluster mode (for production)
    cluster_enabled: bool = Field(default=False)
    cluster_nodes: list[str] = Field(default_factory=list)

    @property
    def redis_url(self) -> str:
        """Generate Redis connection URL"""
        password = self.redis_password.get_secret_value()
        protocol = "rediss" if self.redis_ssl else "redis"
        if password:
            return f"{protocol}://:{password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"{protocol}://{self.redis_host}:{self.redis_port}/{self.redis_db}"


class MonitoringSettings(BaseModel):
    """Monitoring and observability settings"""

    # Prometheus metrics
    prometheus_enabled: bool = Field(default=True)
    prometheus_port: int = Field(default=9090)
    prometheus_path: str = Field(default="/metrics")

    # OpenTelemetry tracing
    otel_enabled: bool = Field(default=True)
    otel_service_name: str = Field(default="ieap-platform")
    otel_exporter_endpoint: str = Field(default="http://localhost:4317")
    otel_sample_rate: float = Field(default=1.0, ge=0.0, le=1.0)

    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json", description="Log format: json or text")
    log_output: str = Field(default="stdout", description="Log output: stdout, file, or both")
    log_file_path: str = Field(default="/var/log/ieap/app.log")
    log_file_max_size_mb: int = Field(default=100, ge=1, le=1000)
    log_file_backup_count: int = Field(default=10, ge=1, le=100)

    # Health checks
    health_check_enabled: bool = Field(default=True)
    health_check_interval: int = Field(default=30, description="Health check interval in seconds")

    # Alerting
    alerting_enabled: bool = Field(default=True)
    alert_webhook_url: str | None = Field(default=None)
    pagerduty_key: SecretStr | None = Field(default=None)
    slack_webhook_url: str | None = Field(default=None)


class APISettings(BaseModel):
    """API configuration settings"""

    # Server settings
    host: str = Field(default="0.0.0.0", description="API host")
    port: int = Field(default=8000, description="API port")
    workers: int = Field(default=4, ge=1, le=32, description="Number of workers")

    # API versioning
    api_version: str = Field(default="v1", description="Current API version")
    api_prefix: str = Field(default="/api", description="API prefix")

    # Documentation
    docs_enabled: bool = Field(default=True, description="Enable API documentation")
    docs_url: str = Field(default="/docs", description="OpenAPI docs URL")
    redoc_url: str = Field(default="/redoc", description="ReDoc URL")

    # Request/Response settings
    request_timeout: int = Field(default=30, ge=5, le=300, description="Request timeout in seconds")
    max_request_size_mb: int = Field(default=10, ge=1, le=100)

    # Pagination
    default_page_size: int = Field(default=20, ge=1, le=100)
    max_page_size: int = Field(default=100, ge=1, le=1000)

    # Compression
    enable_gzip: bool = Field(default=True)
    gzip_min_size: int = Field(default=1000, description="Minimum size for gzip compression")


class MLSettings(BaseModel):
    """Machine Learning configuration settings"""

    # Model storage
    model_storage_path: str = Field(default="./models", description="Path to model storage")
    model_registry_url: str | None = Field(default=None, description="MLflow registry URL")

    # Training settings
    training_batch_size: int = Field(default=32, ge=1, le=1024)
    training_epochs: int = Field(default=100, ge=1, le=1000)
    early_stopping_patience: int = Field(default=10, ge=1, le=50)

    # Inference settings
    inference_batch_size: int = Field(default=128, ge=1, le=1024)
    inference_timeout: int = Field(default=30, ge=5, le=300)

    # GPU settings
    gpu_enabled: bool = Field(default=False)
    gpu_memory_fraction: float = Field(default=0.8, ge=0.1, le=1.0)

    # Model versioning
    enable_model_versioning: bool = Field(default=True)
    max_model_versions: int = Field(default=5, ge=1, le=20)

    # Auto-retraining
    auto_retrain_enabled: bool = Field(default=False)
    retrain_threshold: float = Field(default=0.05, description="Performance drop threshold for retraining")
    retrain_schedule: str = Field(default="0 2 * * 0", description="Cron schedule for retraining")


class CelerySettings(BaseModel):
    """Celery task queue settings"""

    broker_url: str = Field(default="redis://localhost:6379/1", description="Celery broker URL")
    result_backend: str = Field(default="redis://localhost:6379/2", description="Celery result backend")

    # Task settings
    task_time_limit: int = Field(default=3600, description="Task time limit in seconds")
    task_soft_time_limit: int = Field(default=3000, description="Soft time limit in seconds")

    # Worker settings
    worker_concurrency: int = Field(default=4, ge=1, le=32)
    worker_prefetch_multiplier: int = Field(default=4, ge=1, le=16)

    # Queue settings
    task_default_queue: str = Field(default="default")
    task_queues: list[str] = Field(
        default=["default", "high_priority", "ml_training", "data_processing"]
    )


class Settings(BaseSettings):
    """
    Main application settings class.
    
    Loads configuration from environment variables and falls back to .env file if present.
    """

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore"
    )

    # Application settings
    app_name: str = Field(
        default="Intelligent Enterprise Automation Platform",
        description="Application name"
    )
    app_version: str = Field(default="2.0.0", description="Application version")
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Application environment"
    )
    debug: bool = Field(default=False, description="Debug mode")

    # Nested settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    api: APISettings = Field(default_factory=APISettings)
    ml: MLSettings = Field(default_factory=MLSettings)
    celery: CelerySettings = Field(default_factory=CelerySettings)

    # Feature flags
    feature_flags_enabled: bool = Field(default=True)
    feature_flags_source: str = Field(
        default="file",
        description="Feature flags source: file, redis, or api"
    )

    # Orchestrator settings
    orchestrator_max_concurrent_tasks: int = Field(default=50, ge=1, le=500)
    orchestrator_task_timeout: int = Field(default=3600, ge=60, le=86400)
    orchestrator_health_check_interval: int = Field(default=30, ge=5, le=300)

    # Decision engine settings
    decision_engine_max_autonomous_spend: float = Field(default=100000.0)
    decision_engine_min_confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    decision_engine_critical_decisions_allowed: bool = Field(default=False)

    # Data pipeline settings
    pipeline_batch_size: int = Field(default=1000, ge=100, le=100000)
    pipeline_processing_threads: int = Field(default=4, ge=1, le=32)
    pipeline_buffer_size: int = Field(default=10000, ge=1000, le=1000000)

    @model_validator(mode="after")
    def validate_settings(self) -> "Settings":
        """Validate settings after initialization"""
        if self.environment == Environment.PRODUCTION:
            # Enforce production security settings
            if self.debug:
                raise ValueError("Debug mode cannot be enabled in production")
            if self.security.jwt_secret_key.get_secret_value() == "change-me-in-production-use-strong-secret-key":
                raise ValueError("JWT secret key must be changed in production")
        return self

    def get_config_dict(self) -> dict[str, Any]:
        """Get configuration as dictionary (excluding secrets)"""
        return {
            "app_name": self.app_name,
            "app_version": self.app_version,
            "environment": self.environment.value,
            "debug": self.debug,
            "api": {
                "host": self.api.host,
                "port": self.api.port,
                "api_version": self.api.api_version,
            },
            "monitoring": {
                "prometheus_enabled": self.monitoring.prometheus_enabled,
                "otel_enabled": self.monitoring.otel_enabled,
            }
        }

    @model_validator(mode="before")
    def map_legacy_security_env_vars(cls, values: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(values, dict):
            return values

        security_values = dict(values.get("security", {}) or {})
        legacy_mapping = {
            "JWT_SECRET_KEY": "jwt_secret_key",
            "JWT_ALGORITHM": "jwt_algorithm",
            "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "jwt_access_token_expire_minutes",
            "JWT_REFRESH_TOKEN_EXPIRE_DAYS": "jwt_refresh_token_expire_days",
            "API_KEY_HEADER": "api_key_header",
            "API_KEY_PREFIX": "api_key_prefix",
            "OAUTH2_ENABLED": "oauth2_enabled",
            "OAUTH2_PROVIDERS": "oauth2_providers",
            "OAUTH2_GOOGLE_CLIENT_ID": "oauth2_google_client_id",
            "OAUTH2_GOOGLE_CLIENT_SECRET": "oauth2_google_client_secret",
            "OAUTH2_GOOGLE_REDIRECT_URI": "oauth2_google_redirect_uri",
            "ENCRYPTION_KEY": "encryption_key",
            "PASSWORD_MIN_LENGTH": "password_min_length",
            "PASSWORD_REQUIRE_UPPERCASE": "password_require_uppercase",
            "PASSWORD_REQUIRE_LOWERCASE": "password_require_lowercase",
            "PASSWORD_REQUIRE_DIGITS": "password_require_digits",
            "PASSWORD_REQUIRE_SPECIAL": "password_require_special",
            "CORS_ORIGINS": "cors_origins",
            "CORS_ALLOW_CREDENTIALS": "cors_allow_credentials",
            "ENABLE_HSTS": "enable_hsts",
            "ENABLE_CSP": "enable_csp",
        }

        for env_key, nested_key in legacy_mapping.items():
            if env_key in values and nested_key not in security_values:
                security_values[nested_key] = values.pop(env_key)

        if security_values:
            values["security"] = security_values

        return values


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()


def reload_settings() -> Settings:
    """
    Reload settings from environment.
    
    Clears the cache and returns fresh settings.
    """
    get_settings.cache_clear()
    return get_settings()
