"""
Prometheus Metrics

Enterprise metrics collection and export.
"""


from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    Counter,
    Gauge,
    Histogram,
    Info,
    Summary,
    generate_latest,
)


class MetricsRegistry:
    """
    Centralized metrics registry.
    """

    def __init__(self, namespace: str = "ieap"):
        self.namespace = namespace
        self.registry = REGISTRY
        self._metrics: dict[str, any] = {}

    def counter(
        self,
        name: str,
        description: str,
        labels: list[str] | None = None
    ) -> Counter:
        """Create or get a counter metric."""
        full_name = f"{self.namespace}_{name}"

        if full_name not in self._metrics:
            self._metrics[full_name] = Counter(
                full_name,
                description,
                labels or [],
                registry=self.registry
            )

        return self._metrics[full_name]

    def histogram(
        self,
        name: str,
        description: str,
        labels: list[str] | None = None,
        buckets: list[float] | None = None
    ) -> Histogram:
        """Create or get a histogram metric."""
        full_name = f"{self.namespace}_{name}"

        if full_name not in self._metrics:
            kwargs = {
                "name": full_name,
                "documentation": description,
                "labelnames": labels or [],
                "registry": self.registry
            }
            if buckets:
                kwargs["buckets"] = buckets

            self._metrics[full_name] = Histogram(**kwargs)

        return self._metrics[full_name]

    def gauge(
        self,
        name: str,
        description: str,
        labels: list[str] | None = None
    ) -> Gauge:
        """Create or get a gauge metric."""
        full_name = f"{self.namespace}_{name}"

        if full_name not in self._metrics:
            self._metrics[full_name] = Gauge(
                full_name,
                description,
                labels or [],
                registry=self.registry
            )

        return self._metrics[full_name]

    def summary(
        self,
        name: str,
        description: str,
        labels: list[str] | None = None
    ) -> Summary:
        """Create or get a summary metric."""
        full_name = f"{self.namespace}_{name}"

        if full_name not in self._metrics:
            self._metrics[full_name] = Summary(
                full_name,
                description,
                labels or [],
                registry=self.registry
            )

        return self._metrics[full_name]

    def info(
        self,
        name: str,
        description: str
    ) -> Info:
        """Create or get an info metric."""
        full_name = f"{self.namespace}_{name}"

        if full_name not in self._metrics:
            self._metrics[full_name] = Info(
                full_name,
                description,
                registry=self.registry
            )

        return self._metrics[full_name]

    def export(self) -> bytes:
        """Export metrics in Prometheus format."""
        return generate_latest(self.registry)

    @property
    def content_type(self) -> str:
        """Get Prometheus content type."""
        return CONTENT_TYPE_LATEST


# Global metrics registry
_metrics: MetricsRegistry | None = None


def get_metrics() -> MetricsRegistry:
    """Get global metrics registry."""
    global _metrics
    if _metrics is None:
        _metrics = MetricsRegistry()
    return _metrics


# ============================================================================
# Pre-defined Application Metrics
# ============================================================================

# HTTP Request Metrics
request_counter = Counter(
    "ieap_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

request_latency = Histogram(
    "ieap_http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

active_requests = Gauge(
    "ieap_http_requests_active",
    "Active HTTP requests",
    ["method", "endpoint"]
)

# ML Model Metrics
model_predictions = Counter(
    "ieap_model_predictions_total",
    "Total model predictions",
    ["model_id", "model_type", "status"]
)

model_prediction_latency = Histogram(
    "ieap_model_prediction_duration_seconds",
    "Model prediction latency",
    ["model_id", "model_type"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

model_training_duration = Histogram(
    "ieap_model_training_duration_seconds",
    "Model training duration",
    ["model_type"],
    buckets=[60, 300, 600, 1800, 3600, 7200, 14400]
)

active_models = Gauge(
    "ieap_active_models",
    "Number of active/deployed models",
    ["model_type"]
)

# Pipeline Metrics
pipeline_records = Counter(
    "ieap_pipeline_records_total",
    "Total pipeline records processed",
    ["pipeline_id", "status"]
)

pipeline_duration = Histogram(
    "ieap_pipeline_duration_seconds",
    "Pipeline execution duration",
    ["pipeline_id"],
    buckets=[1, 5, 10, 30, 60, 300, 600, 1800]
)

active_pipelines = Gauge(
    "ieap_active_pipelines",
    "Number of running pipelines"
)

# Cache Metrics
cache_operations = Counter(
    "ieap_cache_operations_total",
    "Total cache operations",
    ["operation", "status"]
)

cache_hit_ratio = Gauge(
    "ieap_cache_hit_ratio",
    "Cache hit ratio"
)

# Task Queue Metrics
task_queue_size = Gauge(
    "ieap_task_queue_size",
    "Number of tasks in queue",
    ["queue"]
)

task_processing_time = Histogram(
    "ieap_task_processing_seconds",
    "Task processing time",
    ["task_type"],
    buckets=[0.1, 0.5, 1, 5, 10, 30, 60, 300]
)

task_failures = Counter(
    "ieap_task_failures_total",
    "Total task failures",
    ["task_type", "error_type"]
)

# Decision Engine Metrics
decisions_made = Counter(
    "ieap_decisions_total",
    "Total decisions made",
    ["domain", "status"]
)

decision_confidence = Histogram(
    "ieap_decision_confidence",
    "Decision confidence distribution",
    ["domain"],
    buckets=[0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.99]
)

# System Metrics
system_info = Info(
    "ieap_system",
    "System information"
)

uptime_seconds = Gauge(
    "ieap_uptime_seconds",
    "Application uptime in seconds"
)

# Database Metrics
db_connections_active = Gauge(
    "ieap_db_connections_active",
    "Active database connections"
)

db_query_duration = Histogram(
    "ieap_db_query_duration_seconds",
    "Database query duration",
    ["operation"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
)

# Error Metrics
errors_total = Counter(
    "ieap_errors_total",
    "Total application errors",
    ["type", "component"]
)
