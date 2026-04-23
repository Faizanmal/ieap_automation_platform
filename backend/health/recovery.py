"""
Recovery Manager

Auto-recovery mechanisms for failed components.
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from .aggregator import ComponentHealth

logger = logging.getLogger(__name__)


class RecoveryAction(Enum):
    """Types of recovery actions"""
    RESTART_SERVICE = "restart_service"
    RECONNECT = "reconnect"
    CLEAR_CACHE = "clear_cache"
    SCALE_UP = "scale_up"
    NOTIFY = "notify"
    FAILOVER = "failover"
    NONE = "none"


@dataclass
class RecoveryAttempt:
    """Record of a recovery attempt"""
    component: str
    action: RecoveryAction
    timestamp: datetime
    success: bool
    duration_ms: float
    message: str | None = None


@dataclass
class RecoveryStrategy:
    """Strategy for recovering a component"""
    component: str
    actions: list[RecoveryAction]
    max_attempts: int = 3
    cooldown_seconds: float = 60.0
    escalation_threshold: int = 5
    recovery_func: Callable | None = None


class RecoveryManager:
    """
    Manages auto-recovery for failed components.
    
    Features:
    - Configurable recovery strategies per component
    - Cooldown periods between attempts
    - Escalation after repeated failures
    - Recovery history tracking
    - Notification integration
    
    Usage:
        manager = RecoveryManager()
        
        # Register recovery strategy
        manager.register_strategy(RecoveryStrategy(
            component="database",
            actions=[RecoveryAction.RECONNECT, RecoveryAction.NOTIFY],
            max_attempts=3
        ))
        
        # Attempt recovery
        success = await manager.attempt_recovery("database", health_status)
    """

    def __init__(
        self,
        notification_handler: Callable | None = None,
        max_history: int = 100
    ):
        self.notification_handler = notification_handler
        self.max_history = max_history

        self._strategies: dict[str, RecoveryStrategy] = {}
        self._attempt_counts: dict[str, int] = {}
        self._last_attempts: dict[str, datetime] = {}
        self._history: list[RecoveryAttempt] = []
        self._recovery_lock = asyncio.Lock()

    def register_strategy(self, strategy: RecoveryStrategy):
        """Register a recovery strategy for a component"""
        self._strategies[strategy.component] = strategy
        self._attempt_counts[strategy.component] = 0
        logger.info(f"Registered recovery strategy for {strategy.component}")

    def get_strategy(self, component: str) -> RecoveryStrategy | None:
        """Get recovery strategy for a component"""
        return self._strategies.get(component)

    async def attempt_recovery(
        self,
        component: str,
        health: ComponentHealth
    ) -> bool:
        """
        Attempt to recover a failed component.
        
        Returns True if recovery was successful.
        """
        async with self._recovery_lock:
            strategy = self._strategies.get(component)

            if not strategy:
                logger.warning(f"No recovery strategy for {component}")
                return False

            # Check cooldown
            last_attempt = self._last_attempts.get(component)
            if last_attempt:
                cooldown_end = last_attempt + timedelta(seconds=strategy.cooldown_seconds)
                if datetime.now() < cooldown_end:
                    logger.debug(f"Recovery for {component} still in cooldown")
                    return False

            # Check max attempts
            attempt_count = self._attempt_counts.get(component, 0)
            if attempt_count >= strategy.max_attempts:
                logger.warning(
                    f"Max recovery attempts reached for {component}, "
                    f"escalating..."
                )
                await self._escalate(component, health, strategy)
                return False

            # Execute recovery actions
            success = False
            for action in strategy.actions:
                start_time = datetime.now()

                try:
                    if action == RecoveryAction.RESTART_SERVICE:
                        success = await self._restart_service(component)
                    elif action == RecoveryAction.RECONNECT:
                        success = await self._reconnect(component, strategy)
                    elif action == RecoveryAction.CLEAR_CACHE:
                        success = await self._clear_cache(component)
                    elif action == RecoveryAction.NOTIFY:
                        await self._notify(component, health)
                        success = True
                    elif action == RecoveryAction.FAILOVER:
                        success = await self._failover(component)
                    elif action == RecoveryAction.SCALE_UP:
                        success = await self._scale_up(component)
                    else:
                        continue

                    duration = (datetime.now() - start_time).total_seconds() * 1000

                    attempt = RecoveryAttempt(
                        component=component,
                        action=action,
                        timestamp=datetime.now(),
                        success=success,
                        duration_ms=duration,
                        message=f"Action {action.value} {'succeeded' if success else 'failed'}"
                    )
                    self._record_attempt(attempt)

                    if success:
                        logger.info(f"Recovery action {action.value} succeeded for {component}")
                        self._attempt_counts[component] = 0
                        return True

                except Exception as e:
                    logger.error(f"Recovery action {action.value} failed for {component}: {e}")
                    duration = (datetime.now() - start_time).total_seconds() * 1000
                    self._record_attempt(RecoveryAttempt(
                        component=component,
                        action=action,
                        timestamp=datetime.now(),
                        success=False,
                        duration_ms=duration,
                        message=str(e)
                    ))

            # Update attempt tracking
            self._attempt_counts[component] = attempt_count + 1
            self._last_attempts[component] = datetime.now()

            return False

    async def _restart_service(self, component: str) -> bool:
        """Restart a service (placeholder)"""
        logger.info(f"Restarting service: {component}")
        # Implementation would depend on deployment environment
        await asyncio.sleep(1)  # Simulate restart
        return True

    async def _reconnect(
        self,
        component: str,
        strategy: RecoveryStrategy
    ) -> bool:
        """Attempt to reconnect a component"""
        logger.info(f"Attempting reconnection for: {component}")

        if strategy.recovery_func:
            try:
                await strategy.recovery_func()
                return True
            except Exception as e:
                logger.error(f"Reconnection failed: {e}")
                return False

        return False

    async def _clear_cache(self, component: str) -> bool:
        """Clear cache for a component"""
        logger.info(f"Clearing cache for: {component}")
        # Implementation would clear relevant caches
        return True

    async def _notify(self, component: str, health: ComponentHealth):
        """Send notification about component failure"""
        if self.notification_handler:
            try:
                await self.notification_handler(
                    component=component,
                    status=health.status.value,
                    message=health.message,
                    timestamp=datetime.now()
                )
            except Exception as e:
                logger.error(f"Failed to send notification: {e}")

    async def _failover(self, component: str) -> bool:
        """Trigger failover for a component"""
        logger.info(f"Triggering failover for: {component}")
        # Implementation would switch to backup
        return True

    async def _scale_up(self, component: str) -> bool:
        """Scale up resources for a component"""
        logger.info(f"Scaling up: {component}")
        # Implementation would add more instances
        return True

    async def _escalate(
        self,
        component: str,
        health: ComponentHealth,
        strategy: RecoveryStrategy
    ):
        """Escalate after max recovery attempts"""
        logger.critical(
            f"Recovery escalation for {component}: "
            f"Max attempts ({strategy.max_attempts}) exceeded"
        )

        # Reset counter after escalation threshold
        if self._attempt_counts.get(component, 0) >= strategy.escalation_threshold:
            self._attempt_counts[component] = 0

        # Always notify on escalation
        await self._notify(component, health)

    def _record_attempt(self, attempt: RecoveryAttempt):
        """Record a recovery attempt"""
        self._history.append(attempt)

        # Trim history if needed
        if len(self._history) > self.max_history:
            self._history = self._history[-self.max_history:]

    def get_recovery_history(
        self,
        component: str | None = None,
        limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get recovery attempt history"""
        history = self._history

        if component:
            history = [h for h in history if h.component == component]

        return [
            {
                "component": h.component,
                "action": h.action.value,
                "timestamp": h.timestamp.isoformat(),
                "success": h.success,
                "duration_ms": round(h.duration_ms, 2),
                "message": h.message
            }
            for h in history[-limit:]
        ]

    def reset_attempts(self, component: str):
        """Reset attempt counter for a component"""
        self._attempt_counts[component] = 0
        self._last_attempts.pop(component, None)
