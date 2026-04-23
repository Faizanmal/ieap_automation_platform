"""
Enterprise Feature Flags System

Provides dynamic feature flag management for:
- Gradual feature rollouts
- A/B testing
- Canary deployments
- Emergency kill switches
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class FeatureState(str, Enum):
    """Feature flag states"""
    ENABLED = "enabled"
    DISABLED = "disabled"
    PERCENTAGE = "percentage"
    USER_LIST = "user_list"
    TIME_BASED = "time_based"


@dataclass
class FeatureCondition:
    """Condition for feature flag evaluation"""
    type: str  # percentage, user_list, time_range, environment
    value: Any

    def evaluate(self, context: dict[str, Any]) -> bool:
        """Evaluate condition against context"""
        if self.type == "percentage":
            # Use user_id hash for consistent evaluation
            user_id = context.get("user_id", "")
            if user_id:
                hash_value = hash(user_id) % 100
                return hash_value < self.value
            return False

        if self.type == "user_list":
            user_id = context.get("user_id", "")
            return user_id in self.value

        if self.type == "environment":
            current_env = context.get("environment", "development")
            return current_env in self.value

        if self.type == "time_range":
            now = datetime.now()
            start = datetime.fromisoformat(self.value.get("start", "2000-01-01"))
            end = datetime.fromisoformat(self.value.get("end", "2100-01-01"))
            return start <= now <= end

        return False


@dataclass
class FeatureFlag:
    """Individual feature flag definition"""
    name: str
    description: str
    state: FeatureState
    conditions: list[FeatureCondition] = field(default_factory=list)
    default_value: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    owner: str = ""
    tags: list[str] = field(default_factory=list)

    def is_enabled(self, context: dict[str, Any] | None = None) -> bool:
        """Check if feature is enabled for given context"""
        context = context or {}

        if self.state == FeatureState.ENABLED:
            return True
        if self.state == FeatureState.DISABLED:
            return False
        if self.state in (FeatureState.PERCENTAGE, FeatureState.USER_LIST, FeatureState.TIME_BASED):
            # Evaluate all conditions (AND logic)
            if not self.conditions:
                return self.default_value
            return all(condition.evaluate(context) for condition in self.conditions)

        return self.default_value


class FeatureFlags:
    """
    Feature flags manager supporting multiple backends.
    
    Supports:
    - File-based configuration
    - Redis-based dynamic flags
    - Remote API-based flags
    """

    def __init__(
        self,
        source: str = "file",
        config_path: str = "config/features.json",
        redis_client: Any = None,
        api_url: str | None = None
    ):
        self.source = source
        self.config_path = config_path
        self.redis_client = redis_client
        self.api_url = api_url
        self.flags: dict[str, FeatureFlag] = {}
        self._load_flags()

    def _load_flags(self):
        """Load feature flags from configured source"""
        if self.source == "file":
            self._load_from_file()
        elif self.source == "redis":
            self._load_from_redis()
        elif self.source == "api":
            self._load_from_api()
        else:
            self._load_default_flags()

    def _load_from_file(self):
        """Load flags from JSON file"""
        try:
            path = Path(self.config_path)
            if path.exists():
                with open(path) as f:
                    data = json.load(f)
                    for name, config in data.get("flags", {}).items():
                        self.flags[name] = self._parse_flag(name, config)
                logger.info(f"Loaded {len(self.flags)} feature flags from file")
            else:
                self._load_default_flags()
        except Exception as e:
            logger.error(f"Error loading feature flags from file: {e}")
            self._load_default_flags()

    def _load_from_redis(self):
        """Load flags from Redis"""
        try:
            if self.redis_client:
                flags_data = self.redis_client.get("feature_flags")
                if flags_data:
                    data = json.loads(flags_data)
                    for name, config in data.items():
                        self.flags[name] = self._parse_flag(name, config)
                    logger.info(f"Loaded {len(self.flags)} feature flags from Redis")
                else:
                    self._load_default_flags()
            else:
                self._load_default_flags()
        except Exception as e:
            logger.error(f"Error loading feature flags from Redis: {e}")
            self._load_default_flags()

    def _load_from_api(self):
        """Load flags from remote API"""
        try:
            import requests
            if self.api_url:
                response = requests.get(f"{self.api_url}/feature-flags", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    for name, config in data.items():
                        self.flags[name] = self._parse_flag(name, config)
                    logger.info(f"Loaded {len(self.flags)} feature flags from API")
                else:
                    self._load_default_flags()
            else:
                self._load_default_flags()
        except Exception as e:
            logger.error(f"Error loading feature flags from API: {e}")
            self._load_default_flags()

    def _load_default_flags(self):
        """Load default feature flags"""
        default_flags = {
            # Core platform features
            "enable_ml_predictions": {
                "description": "Enable ML model predictions",
                "state": "enabled",
                "tags": ["ml", "core"]
            },
            "enable_autonomous_decisions": {
                "description": "Enable autonomous decision making",
                "state": "enabled",
                "tags": ["decision-engine", "core"]
            },
            "enable_realtime_pipeline": {
                "description": "Enable real-time data pipeline",
                "state": "enabled",
                "tags": ["pipeline", "core"]
            },

            # New enterprise features
            "enable_advanced_analytics": {
                "description": "Enable advanced analytics features",
                "state": "percentage",
                "conditions": [{"type": "percentage", "value": 100}],
                "tags": ["analytics", "enterprise"]
            },
            "enable_multi_tenant": {
                "description": "Enable multi-tenant support",
                "state": "disabled",
                "tags": ["enterprise", "multi-tenant"]
            },
            "enable_audit_logging": {
                "description": "Enable comprehensive audit logging",
                "state": "enabled",
                "tags": ["security", "compliance"]
            },
            "enable_api_v2": {
                "description": "Enable API v2 endpoints",
                "state": "percentage",
                "conditions": [{"type": "percentage", "value": 50}],
                "tags": ["api", "beta"]
            },
            "enable_gpu_acceleration": {
                "description": "Enable GPU acceleration for ML models",
                "state": "disabled",
                "tags": ["ml", "performance"]
            },
            "enable_distributed_processing": {
                "description": "Enable distributed data processing",
                "state": "enabled",
                "tags": ["pipeline", "scalability"]
            },
            "enable_auto_scaling": {
                "description": "Enable automatic resource scaling",
                "state": "enabled",
                "tags": ["infrastructure", "scaling"]
            },
            "enable_webhooks": {
                "description": "Enable webhook notifications",
                "state": "enabled",
                "tags": ["integrations", "notifications"]
            },
            "enable_custom_ml_models": {
                "description": "Allow users to deploy custom ML models",
                "state": "disabled",
                "tags": ["ml", "enterprise"]
            },
            "enable_sso": {
                "description": "Enable Single Sign-On",
                "state": "disabled",
                "tags": ["security", "enterprise"]
            }
        }

        for name, config in default_flags.items():
            self.flags[name] = self._parse_flag(name, config)

        logger.info(f"Loaded {len(self.flags)} default feature flags")

    def _parse_flag(self, name: str, config: dict[str, Any]) -> FeatureFlag:
        """Parse flag configuration into FeatureFlag object"""
        conditions = []
        for cond in config.get("conditions", []):
            conditions.append(FeatureCondition(
                type=cond.get("type", "percentage"),
                value=cond.get("value")
            ))

        return FeatureFlag(
            name=name,
            description=config.get("description", ""),
            state=FeatureState(config.get("state", "disabled")),
            conditions=conditions,
            default_value=config.get("default_value", False),
            metadata=config.get("metadata", {}),
            owner=config.get("owner", ""),
            tags=config.get("tags", [])
        )

    def is_enabled(
        self,
        flag_name: str,
        context: dict[str, Any] | None = None,
        default: bool = False
    ) -> bool:
        """
        Check if a feature flag is enabled.
        
        Args:
            flag_name: Name of the feature flag
            context: Evaluation context (user_id, environment, etc.)
            default: Default value if flag doesn't exist
            
        Returns:
            Boolean indicating if feature is enabled
        """
        flag = self.flags.get(flag_name)
        if flag is None:
            logger.warning(f"Feature flag '{flag_name}' not found, using default: {default}")
            return default

        return flag.is_enabled(context)

    def get_flag(self, flag_name: str) -> FeatureFlag | None:
        """Get feature flag by name"""
        return self.flags.get(flag_name)

    def get_all_flags(self) -> dict[str, FeatureFlag]:
        """Get all feature flags"""
        return self.flags.copy()

    def get_flags_by_tag(self, tag: str) -> dict[str, FeatureFlag]:
        """Get all flags with a specific tag"""
        return {
            name: flag
            for name, flag in self.flags.items()
            if tag in flag.tags
        }

    def set_flag(self, flag_name: str, state: FeatureState, persist: bool = True):
        """
        Update a feature flag state.
        
        Args:
            flag_name: Name of the flag to update
            state: New state for the flag
            persist: Whether to persist changes to backend
        """
        if flag_name in self.flags:
            self.flags[flag_name].state = state
            self.flags[flag_name].updated_at = datetime.now()

            if persist:
                self._persist_flags()

            logger.info(f"Feature flag '{flag_name}' updated to '{state.value}'")

    def _persist_flags(self):
        """Persist flags to backend"""
        if self.source == "file":
            self._save_to_file()
        elif self.source == "redis":
            self._save_to_redis()

    def _save_to_file(self):
        """Save flags to JSON file"""
        try:
            data = {"flags": {}}
            for name, flag in self.flags.items():
                data["flags"][name] = {
                    "description": flag.description,
                    "state": flag.state.value,
                    "default_value": flag.default_value,
                    "tags": flag.tags,
                    "owner": flag.owner
                }

            path = Path(self.config_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w") as f:
                json.dump(data, f, indent=2)

            logger.info("Feature flags saved to file")
        except Exception as e:
            logger.error(f"Error saving feature flags to file: {e}")

    def _save_to_redis(self):
        """Save flags to Redis"""
        try:
            if self.redis_client:
                data = {}
                for name, flag in self.flags.items():
                    data[name] = {
                        "description": flag.description,
                        "state": flag.state.value,
                        "default_value": flag.default_value,
                        "tags": flag.tags
                    }
                self.redis_client.set("feature_flags", json.dumps(data))
                logger.info("Feature flags saved to Redis")
        except Exception as e:
            logger.error(f"Error saving feature flags to Redis: {e}")

    def refresh(self):
        """Refresh flags from source"""
        self.flags.clear()
        self._load_flags()


# Global feature flags instance
_feature_flags: FeatureFlags | None = None


@lru_cache
def get_feature_flags() -> FeatureFlags:
    """Get cached feature flags instance"""
    global _feature_flags
    if _feature_flags is None:
        _feature_flags = FeatureFlags()
    return _feature_flags


def is_feature_enabled(
    flag_name: str,
    context: dict[str, Any] | None = None,
    default: bool = False
) -> bool:
    """
    Convenience function to check if a feature is enabled.
    
    Usage:
        from config.feature_flags import is_feature_enabled
        
        if is_feature_enabled("enable_ml_predictions"):
            # Run ML predictions
            pass
    """
    return get_feature_flags().is_enabled(flag_name, context, default)
