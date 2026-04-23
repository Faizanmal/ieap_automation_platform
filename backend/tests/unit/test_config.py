"""
Unit tests for the configuration module.
"""

import os
from unittest.mock import patch


class TestSettings:
    """Tests for configuration settings."""

    def test_default_settings(self):
        """Test default settings are loaded."""
        with patch.dict(os.environ, {}, clear=True):
            # Set required env vars
            os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/test"
            os.environ["JWT_SECRET_KEY"] = "test-secret"

            from config.settings import Settings
            settings = Settings()

            assert settings.app_name == "IEAP"
            assert settings.debug is False

    def test_environment_override(self):
        """Test environment variables override defaults."""
        with patch.dict(os.environ, {
            "APP_ENV": "testing",
            "DEBUG": "true",
            "DATABASE_URL": "postgresql://test:test@localhost/test",
            "JWT_SECRET_KEY": "test-secret"
        }):
            from config.settings import Settings
            settings = Settings()

            assert settings.environment == "testing"
            assert settings.debug is True


class TestFeatureFlags:
    """Tests for feature flags."""

    def test_feature_flag_enabled(self):
        """Test checking enabled feature flag."""
        from config.feature_flags import FeatureFlags

        flags = FeatureFlags()
        flags._flags = {"test_feature": {"enabled": True}}

        assert flags.is_enabled("test_feature") is True

    def test_feature_flag_disabled(self):
        """Test checking disabled feature flag."""
        from config.feature_flags import FeatureFlags

        flags = FeatureFlags()
        flags._flags = {"test_feature": {"enabled": False}}

        assert flags.is_enabled("test_feature") is False

    def test_feature_flag_missing(self):
        """Test checking missing feature flag returns default."""
        from config.feature_flags import FeatureFlags

        flags = FeatureFlags()
        flags._flags = {}

        assert flags.is_enabled("nonexistent", default=True) is True
        assert flags.is_enabled("nonexistent", default=False) is False

    def test_percentage_rollout(self):
        """Test percentage-based rollout."""
        from config.feature_flags import FeatureFlags

        flags = FeatureFlags()
        flags._flags = {
            "rollout_feature": {
                "enabled": True,
                "percentage": 50
            }
        }

        # With 50% rollout, some should be enabled, some disabled
        results = [
            flags.is_enabled("rollout_feature", user_id=f"user{i}")
            for i in range(100)
        ]

        enabled_count = sum(results)
        # Should be roughly 50%, with some variance
        assert 30 <= enabled_count <= 70
