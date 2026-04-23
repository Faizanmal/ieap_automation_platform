"""
Enterprise Audit Logging System

Provides comprehensive audit trail for:
- User actions
- System events
- Security events
- Data access
- Configuration changes
- Compliance reporting
"""

import asyncio
import json
import logging
import threading
import uuid
from collections import deque
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    """Types of audit events"""

    # Authentication events
    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    AUTH_FAILED = "auth.failed"
    AUTH_MFA = "auth.mfa"
    AUTH_PASSWORD_CHANGE = "auth.password_change"
    AUTH_PASSWORD_RESET = "auth.password_reset"

    # User management
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_ROLE_CHANGE = "user.role_change"

    # API access
    API_REQUEST = "api.request"
    API_KEY_CREATE = "api_key.create"
    API_KEY_REVOKE = "api_key.revoke"

    # Data operations
    DATA_READ = "data.read"
    DATA_CREATE = "data.create"
    DATA_UPDATE = "data.update"
    DATA_DELETE = "data.delete"
    DATA_EXPORT = "data.export"

    # ML operations
    MODEL_TRAIN = "model.train"
    MODEL_DEPLOY = "model.deploy"
    MODEL_PREDICT = "model.predict"
    MODEL_DELETE = "model.delete"

    # Pipeline operations
    PIPELINE_START = "pipeline.start"
    PIPELINE_STOP = "pipeline.stop"
    PIPELINE_ERROR = "pipeline.error"

    # Decision engine
    DECISION_MADE = "decision.made"
    DECISION_APPROVED = "decision.approved"
    DECISION_REJECTED = "decision.rejected"

    # System operations
    SYSTEM_CONFIG_CHANGE = "system.config_change"
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"

    # Security events
    SECURITY_THREAT_DETECTED = "security.threat_detected"
    SECURITY_ACCESS_DENIED = "security.access_denied"
    SECURITY_RATE_LIMIT = "security.rate_limit"


class AuditSeverity(str, Enum):
    """Severity levels for audit events"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Represents an audit event"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    event_type: AuditEventType = AuditEventType.API_REQUEST
    severity: AuditSeverity = AuditSeverity.INFO

    # Actor information
    user_id: str | None = None
    username: str | None = None
    user_email: str | None = None
    user_roles: list[str] = field(default_factory=list)

    # Request context
    request_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None

    # Resource information
    resource_type: str | None = None
    resource_id: str | None = None

    # Action details
    action: str = ""
    status: str = "success"  # success, failure, pending

    # Additional data
    details: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    # Error information
    error_message: str | None = None
    error_code: str | None = None
    stack_trace: str | None = None

    # Compliance tags
    compliance_tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["event_type"] = self.event_type.value
        data["severity"] = self.severity.value
        return data

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())


class AuditEventBuilder:
    """Builder pattern for creating audit events"""

    def __init__(self):
        self._event = AuditEvent()

    def set_type(self, event_type: AuditEventType) -> "AuditEventBuilder":
        self._event.event_type = event_type
        return self

    def set_severity(self, severity: AuditSeverity) -> "AuditEventBuilder":
        self._event.severity = severity
        return self

    def set_user(
        self,
        user_id: str,
        username: str | None = None,
        email: str | None = None,
        roles: list[str] | None = None
    ) -> "AuditEventBuilder":
        self._event.user_id = user_id
        self._event.username = username
        self._event.user_email = email
        self._event.user_roles = roles or []
        return self

    def set_request_context(
        self,
        request_id: str,
        ip_address: str | None = None,
        user_agent: str | None = None
    ) -> "AuditEventBuilder":
        self._event.request_id = request_id
        self._event.ip_address = ip_address
        self._event.user_agent = user_agent
        return self

    def set_resource(
        self,
        resource_type: str,
        resource_id: str
    ) -> "AuditEventBuilder":
        self._event.resource_type = resource_type
        self._event.resource_id = resource_id
        return self

    def set_action(
        self,
        action: str,
        status: str = "success"
    ) -> "AuditEventBuilder":
        self._event.action = action
        self._event.status = status
        return self

    def set_details(self, details: dict[str, Any]) -> "AuditEventBuilder":
        self._event.details = details
        return self

    def set_error(
        self,
        message: str,
        code: str | None = None,
        stack_trace: str | None = None
    ) -> "AuditEventBuilder":
        self._event.error_message = message
        self._event.error_code = code
        self._event.stack_trace = stack_trace
        self._event.status = "failure"
        return self

    def add_compliance_tag(self, tag: str) -> "AuditEventBuilder":
        self._event.compliance_tags.append(tag)
        return self

    def build(self) -> AuditEvent:
        return self._event


class AuditBackend:
    """Base class for audit log backends"""

    async def write(self, event: AuditEvent):
        """Write an audit event"""
        raise NotImplementedError

    async def query(
        self,
        filters: dict[str, Any],
        limit: int = 100,
        offset: int = 0
    ) -> list[AuditEvent]:
        """Query audit events"""
        raise NotImplementedError


class InMemoryAuditBackend(AuditBackend):
    """In-memory audit backend for development/testing"""

    def __init__(self, max_size: int = 10000):
        self.events: deque = deque(maxlen=max_size)
        self._lock = threading.Lock()

    async def write(self, event: AuditEvent):
        with self._lock:
            self.events.append(event)

    async def query(
        self,
        filters: dict[str, Any],
        limit: int = 100,
        offset: int = 0
    ) -> list[AuditEvent]:
        with self._lock:
            events = list(self.events)

        # Apply filters
        if filters.get("event_type"):
            events = [e for e in events if e.event_type.value == filters["event_type"]]
        if filters.get("user_id"):
            events = [e for e in events if e.user_id == filters["user_id"]]
        if filters.get("resource_type"):
            events = [e for e in events if e.resource_type == filters["resource_type"]]
        if filters.get("severity"):
            events = [e for e in events if e.severity.value == filters["severity"]]
        if filters.get("start_time"):
            events = [e for e in events if e.timestamp >= filters["start_time"]]
        if filters.get("end_time"):
            events = [e for e in events if e.timestamp <= filters["end_time"]]

        # Apply pagination
        return events[offset:offset + limit]


class FileAuditBackend(AuditBackend):
    """File-based audit backend"""

    def __init__(self, log_path: str = "/var/log/ieap/audit.log"):
        self.log_path = log_path
        self._ensure_log_directory()

    def _ensure_log_directory(self):
        from pathlib import Path
        Path(self.log_path).parent.mkdir(parents=True, exist_ok=True)

    async def write(self, event: AuditEvent):
        try:
            with open(self.log_path, "a") as f:
                f.write(event.to_json() + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    async def query(
        self,
        filters: dict[str, Any],
        limit: int = 100,
        offset: int = 0
    ) -> list[AuditEvent]:
        # For file backend, reading is expensive
        # In production, use a proper database
        events = []
        try:
            with open(self.log_path) as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        # Basic filtering would happen here
                        events.append(data)
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            pass

        return events[offset:offset + limit]


class AuditLogger:
    """
    Central audit logging service.
    
    Features:
    - Multiple backend support
    - Async logging
    - Buffered writes
    - Event filtering
    - Compliance tagging
    """

    def __init__(
        self,
        backends: list[AuditBackend] | None = None,
        buffer_size: int = 100,
        flush_interval: float = 5.0
    ):
        self.backends = backends or [InMemoryAuditBackend()]
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval

        self._buffer: list[AuditEvent] = []
        self._buffer_lock = threading.Lock()
        self._flush_timer: threading.Timer | None = None

        # Event hooks
        self._pre_write_hooks: list[Callable[[AuditEvent], AuditEvent]] = []
        self._post_write_hooks: list[Callable[[AuditEvent], None]] = []

    def add_pre_write_hook(self, hook: Callable[[AuditEvent], AuditEvent]):
        """Add hook to run before writing event"""
        self._pre_write_hooks.append(hook)

    def add_post_write_hook(self, hook: Callable[[AuditEvent], None]):
        """Add hook to run after writing event"""
        self._post_write_hooks.append(hook)

    async def log(self, event: AuditEvent):
        """
        Log an audit event.
        
        Args:
            event: Audit event to log
        """
        # Run pre-write hooks
        for hook in self._pre_write_hooks:
            event = hook(event)

        # Write to all backends
        for backend in self.backends:
            try:
                await backend.write(event)
            except Exception as e:
                logger.error(f"Audit backend write failed: {e}")

        # Run post-write hooks
        for hook in self._post_write_hooks:
            try:
                hook(event)
            except Exception as e:
                logger.error(f"Post-write hook failed: {e}")

    def log_sync(self, event: AuditEvent):
        """Synchronous logging (adds to buffer)"""
        with self._buffer_lock:
            self._buffer.append(event)

            if len(self._buffer) >= self.buffer_size:
                self._flush_buffer()

    def _flush_buffer(self):
        """Flush buffered events"""
        with self._buffer_lock:
            events = self._buffer.copy()
            self._buffer.clear()

        if events:
            asyncio.create_task(self._write_events(events))

    async def _write_events(self, events: list[AuditEvent]):
        """Write multiple events to backends"""
        for event in events:
            await self.log(event)

    async def query(
        self,
        event_type: AuditEventType | None = None,
        user_id: str | None = None,
        resource_type: str | None = None,
        severity: AuditSeverity | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[AuditEvent]:
        """
        Query audit events.
        
        Args:
            event_type: Filter by event type
            user_id: Filter by user
            resource_type: Filter by resource type
            severity: Filter by severity
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Max results
            offset: Pagination offset
            
        Returns:
            List of matching audit events
        """
        filters = {}
        if event_type:
            filters["event_type"] = event_type.value
        if user_id:
            filters["user_id"] = user_id
        if resource_type:
            filters["resource_type"] = resource_type
        if severity:
            filters["severity"] = severity.value
        if start_time:
            filters["start_time"] = start_time
        if end_time:
            filters["end_time"] = end_time

        # Query first backend (in production, use primary backend)
        if self.backends:
            return await self.backends[0].query(filters, limit, offset)
        return []

    # Convenience methods for common events
    async def log_login(
        self,
        user_id: str,
        username: str,
        ip_address: str,
        success: bool = True,
        error_message: str | None = None
    ):
        """Log login event"""
        event = (
            AuditEventBuilder()
            .set_type(AuditEventType.AUTH_LOGIN if success else AuditEventType.AUTH_FAILED)
            .set_severity(AuditSeverity.INFO if success else AuditSeverity.WARNING)
            .set_user(user_id, username)
            .set_request_context(str(uuid.uuid4()), ip_address)
            .set_action("login", "success" if success else "failure")
        )

        if error_message:
            event.set_error(error_message)

        await self.log(event.build())

    async def log_data_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        details: dict | None = None
    ):
        """Log data access event"""
        event_type = {
            "read": AuditEventType.DATA_READ,
            "create": AuditEventType.DATA_CREATE,
            "update": AuditEventType.DATA_UPDATE,
            "delete": AuditEventType.DATA_DELETE,
            "export": AuditEventType.DATA_EXPORT
        }.get(action, AuditEventType.DATA_READ)

        event = (
            AuditEventBuilder()
            .set_type(event_type)
            .set_severity(AuditSeverity.INFO)
            .set_user(user_id)
            .set_resource(resource_type, resource_id)
            .set_action(action)
            .set_details(details or {})
            .build()
        )

        await self.log(event)


# Global audit logger instance
_audit_logger: AuditLogger | None = None


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


async def log_audit_event(event: AuditEvent):
    """Convenience function to log an audit event"""
    await get_audit_logger().log(event)
