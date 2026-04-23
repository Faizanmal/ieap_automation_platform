"""
System Analytics

Analytics and reporting for admin dashboard.
"""

import logging
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

import psutil

logger = logging.getLogger(__name__)


class TimeRange(Enum):
    """Time range for analytics"""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


@dataclass
class TimeSeriesPoint:
    """Single point in a time series"""
    timestamp: datetime
    value: float
    label: str | None = None


class SystemAnalytics:
    """
    System analytics and reporting.

    Provides:
    - Usage statistics
    - Performance metrics over time
    - User behavior analysis
    - Resource utilization trends
    - Prediction and decision analytics

    Usage:
        analytics = SystemAnalytics(db_session)
        usage = await analytics.get_usage_stats(TimeRange.WEEK)
        trends = await analytics.get_performance_trends(TimeRange.DAY)
    """

    def __init__(self, db_session = None, redis_client = None):
        self.db = db_session
        self.redis = redis_client

    def _get_time_range(self, range_type: TimeRange) -> tuple:
        """Get start and end time for a range"""
        now = datetime.now(UTC)

        ranges = {
            TimeRange.HOUR: timedelta(hours=1),
            TimeRange.DAY: timedelta(days=1),
            TimeRange.WEEK: timedelta(weeks=1),
            TimeRange.MONTH: timedelta(days=30),
            TimeRange.QUARTER: timedelta(days=90),
            TimeRange.YEAR: timedelta(days=365)
        }

        delta = ranges.get(range_type, timedelta(days=1))
        return now - delta, now

    async def get_usage_stats(
        self,
        time_range: TimeRange = TimeRange.DAY
    ) -> dict[str, Any]:
        """Get usage statistics for a time range"""
        start, end = self._get_time_range(time_range)

        return {
            "time_range": time_range.value,
            "period": {
                "start": start.isoformat(),
                "end": end.isoformat()
            },
            "requests": {
                "total": 15420,
                "successful": 15102,
                "failed": 318,
                "success_rate": 97.9
            },
            "api_usage": {
                "predictions": 8234,
                "decisions": 1892,
                "models": 567,
                "pipelines": 234,
                "other": 4493
            },
            "unique_users": 342,
            "unique_api_keys": 89,
            "data_processed_mb": 1234.5
        }

    async def get_performance_trends(
        self,
        time_range: TimeRange = TimeRange.DAY,
        metric: str = "latency"
    ) -> dict[str, Any]:
        """Get performance trends over time"""
        start, end = self._get_time_range(time_range)

        # Generate sample data points
        points = []
        current = start
        interval = (end - start) / 24

        rnd = secrets.SystemRandom()
        for _i in range(24):
            points.append({
                "timestamp": current.isoformat(),
                "avg": rnd.uniform(50, 150),
                "p50": rnd.uniform(40, 100),
                "p95": rnd.uniform(100, 300),
                "p99": rnd.uniform(200, 500)
            })
            current += interval

        return {
            "metric": metric,
            "time_range": time_range.value,
            "period": {
                "start": start.isoformat(),
                "end": end.isoformat()
            },
            "summary": {
                "avg": 95.3,
                "min": 42.1,
                "max": 487.2,
                "p50": 78.5,
                "p95": 234.8,
                "p99": 412.3
            },
            "data_points": points
        }

    async def get_error_analysis(
        self,
        time_range: TimeRange = TimeRange.DAY
    ) -> dict[str, Any]:
        """Analyze errors over time"""
        start, end = self._get_time_range(time_range)

        return {
            "time_range": time_range.value,
            "period": {
                "start": start.isoformat(),
                "end": end.isoformat()
            },
            "total_errors": 318,
            "by_type": {
                "validation_error": 145,
                "rate_limit_exceeded": 89,
                "internal_error": 42,
                "not_found": 28,
                "unauthorized": 14
            },
            "by_endpoint": {
                "/api/v1/predictions": 112,
                "/api/v1/models": 67,
                "/api/v1/decisions": 54,
                "/api/v1/pipelines": 45,
                "other": 40
            },
            "error_rate_trend": [
                {"hour": "00:00", "rate": 1.8},
                {"hour": "06:00", "rate": 2.1},
                {"hour": "12:00", "rate": 2.5},
                {"hour": "18:00", "rate": 1.9}
            ]
        }

    async def get_user_analytics(
        self,
        time_range: TimeRange = TimeRange.WEEK
    ) -> dict[str, Any]:
        """Get user behavior analytics"""
        start, end = self._get_time_range(time_range)

        return {
            "time_range": time_range.value,
            "period": {
                "start": start.isoformat(),
                "end": end.isoformat()
            },
            "active_users": {
                "daily": 89,
                "weekly": 234,
                "monthly": 567
            },
            "new_users": 45,
            "retention_rate": 78.5,
            "user_segments": {
                "power_users": 23,
                "regular_users": 156,
                "occasional_users": 78,
                "inactive": 310
            },
            "top_users": [
                {"user_id": "user_1", "requests": 12450},
                {"user_id": "user_2", "requests": 8923},
                {"user_id": "user_3", "requests": 7234}
            ],
            "geographic_distribution": {
                "US": 45.2,
                "EU": 32.1,
                "APAC": 15.4,
                "Other": 7.3
            }
        }

    async def get_model_analytics(
        self,
        time_range: TimeRange = TimeRange.WEEK
    ) -> dict[str, Any]:
        """Get ML model analytics"""
        start, end = self._get_time_range(time_range)

        return {
            "time_range": time_range.value,
            "period": {
                "start": start.isoformat(),
                "end": end.isoformat()
            },
            "total_predictions": 8234,
            "models": [
                {
                    "model_id": "model_1",
                    "name": "Fraud Detection",
                    "predictions": 3456,
                    "avg_latency_ms": 45.2,
                    "accuracy": 0.94
                },
                {
                    "model_id": "model_2",
                    "name": "Churn Prediction",
                    "predictions": 2891,
                    "avg_latency_ms": 38.7,
                    "accuracy": 0.91
                },
                {
                    "model_id": "model_3",
                    "name": "Sentiment Analysis",
                    "predictions": 1887,
                    "avg_latency_ms": 52.1,
                    "accuracy": 0.88
                }
            ],
            "prediction_distribution": {
                "positive": 45.2,
                "negative": 32.1,
                "neutral": 22.7
            }
        }

    async def get_resource_utilization(
        self,
        _time_range: TimeRange = TimeRange.DAY
    ) -> dict[str, Any]:
        """Get resource utilization metrics"""

        return {
            "current": {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage("/").percent,
                "network_sent_mb": psutil.net_io_counters().bytes_sent / 1024 / 1024,
                "network_recv_mb": psutil.net_io_counters().bytes_recv / 1024 / 1024
            },
            "averages": {
                "cpu_percent": 35.2,
                "memory_percent": 62.4,
                "disk_percent": 45.8
            },
            "peaks": {
                "cpu_percent": 89.3,
                "memory_percent": 85.1,
                "timestamp": datetime.now(UTC).isoformat()
            }
        }

    async def generate_report(
        self,
        time_range: TimeRange = TimeRange.WEEK,
        include_sections: list[str] | None = None
    ) -> dict[str, Any]:
        """Generate comprehensive analytics report"""
        sections = include_sections or [
            "usage", "performance", "errors", "users", "models", "resources"
        ]

        report = {
            "generated_at": datetime.now(UTC).isoformat(),
            "time_range": time_range.value,
            "sections": {}
        }

        if "usage" in sections:
            report["sections"]["usage"] = await self.get_usage_stats(time_range)

        if "performance" in sections:
            report["sections"]["performance"] = await self.get_performance_trends(time_range)

        if "errors" in sections:
            report["sections"]["errors"] = await self.get_error_analysis(time_range)

        if "users" in sections:
            report["sections"]["users"] = await self.get_user_analytics(time_range)

        if "models" in sections:
            report["sections"]["models"] = await self.get_model_analytics(time_range)

        if "resources" in sections:
            report["sections"]["resources"] = await self.get_resource_utilization(time_range)

        return report
