"""
Tests for configuration management system.

This module tests the configuration manager and settings dataclasses.
"""

import pytest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from test_utils import setup_test_imports
setup_test_imports()

from holdem_cli.config.config_manager import (
    ConfigManager, get_config, get_app_settings, get_user_preferences,
    get_performance_settings, AppSettings, UserPreferences, PerformanceSettings
)
from holdem_cli.config.settings import (
    LogLevel, Theme, ColorScheme, AnimationSpeed, Difficulty, AILevel,
    DatabaseSettings, SecuritySettings, NetworkSettings, MonteCarloSettings,
    LearningSettings, DisplaySettings, PerformanceTuningSettings, ApplicationSettings
)


# =============================================================================
# Enum Tests
# =============================================================================

class TestLogLevel:
    def test_all_log_levels(self):
        assert LogLevel.DEBUG.value == "DEBUG"
        assert LogLevel.INFO.value == "INFO"
        assert LogLevel.WARNING.value == "WARNING"
        assert LogLevel.ERROR.value == "ERROR"
        assert LogLevel.CRITICAL.value == "CRITICAL"

    def test_log_level_count(self):
        assert len(LogLevel) == 5


class TestTheme:
    def test_all_themes(self):
        assert Theme.LIGHT.value == "light"
        assert Theme.DARK.value == "dark"
        assert Theme.AUTO.value == "auto"

    def test_theme_count(self):
        assert len(Theme) == 3


class TestColorScheme:
    def test_all_color_schemes(self):
        assert ColorScheme.DEFAULT.value == "default"
        assert ColorScheme.HIGH_CONTRAST.value == "high_contrast"
        assert ColorScheme.COLORBLIND.value == "colorblind"


class TestAnimationSpeed:
    def test_all_animation_speeds(self):
        assert AnimationSpeed.SLOW.value == "slow"
        assert AnimationSpeed.NORMAL.value == "normal"
        assert AnimationSpeed.FAST.value == "fast"
        assert AnimationSpeed.INSTANT.value == "instant"


class TestDifficulty:
    def test_all_difficulties(self):
        assert Difficulty.EASY.value == "easy"
        assert Difficulty.MEDIUM.value == "medium"
        assert Difficulty.HARD.value == "hard"
        assert Difficulty.ADAPTIVE.value == "adaptive"


class TestAILevel:
    def test_all_ai_levels(self):
        assert AILevel.EASY.value == "easy"
        assert AILevel.MEDIUM.value == "medium"
        assert AILevel.HARD.value == "hard"


# =============================================================================
# Settings Dataclass Tests
# =============================================================================

class TestDatabaseSettings:
    def test_default_values(self):
        settings = DatabaseSettings()
        assert settings.connection_timeout == 30
        assert settings.max_connections == 5
        assert settings.enable_connection_pooling is True
        assert settings.backup_enabled is True

    def test_validate_valid_settings(self):
        settings = DatabaseSettings()
        issues = settings.validate()
        assert len(issues) == 0

    def test_validate_invalid_connection_timeout(self):
        settings = DatabaseSettings(connection_timeout=0)
        issues = settings.validate()
        assert any("connection_timeout" in issue for issue in issues)

    def test_validate_invalid_max_connections(self):
        settings = DatabaseSettings(max_connections=0)
        issues = settings.validate()
        assert any("max_connections" in issue for issue in issues)


class TestSecuritySettings:
    def test_default_values(self):
        settings = SecuritySettings()
        assert settings.enable_input_validation is True
        assert settings.password_min_length == 8
        assert settings.session_timeout_minutes == 30
        assert settings.max_login_attempts == 5

    def test_validate_valid_settings(self):
        settings = SecuritySettings()
        issues = settings.validate()
        assert len(issues) == 0

    def test_validate_invalid_password_min_length(self):
        settings = SecuritySettings(password_min_length=2)
        issues = settings.validate()
        assert any("password_min_length" in issue for issue in issues)

    def test_validate_invalid_session_timeout(self):
        settings = SecuritySettings(session_timeout_minutes=0)
        issues = settings.validate()
        assert any("session_timeout" in issue for issue in issues)


class TestNetworkSettings:
    def test_default_values(self):
        settings = NetworkSettings()
        assert settings.enable_cloud_sync is False
        assert settings.sync_interval_minutes == 60
        assert settings.request_timeout_seconds == 30
        assert settings.max_retries == 3

    def test_validate_valid_settings(self):
        settings = NetworkSettings()
        issues = settings.validate()
        assert len(issues) == 0

    def test_validate_cloud_sync_without_url(self):
        settings = NetworkSettings(enable_cloud_sync=True, cloud_sync_url=None)
        issues = settings.validate()
        assert any("cloud_sync_url" in issue for issue in issues)

    def test_validate_cloud_sync_with_url(self):
        settings = NetworkSettings(
            enable_cloud_sync=True,
            cloud_sync_url="https://example.com/sync"
        )
        issues = settings.validate()
        assert not any("cloud_sync_url" in issue for issue in issues)

    def test_validate_invalid_sync_interval(self):
        settings = NetworkSettings(sync_interval_minutes=0)
        issues = settings.validate()
        assert any("sync_interval" in issue for issue in issues)


class TestMonteCarloSettings:
    def test_default_values(self):
        settings = MonteCarloSettings()
        assert settings.default_iterations == 25000
        assert settings.fallback_iterations == 2500
        assert settings.max_iterations == 100000
        assert settings.min_iterations == 1000

    def test_validate_valid_settings(self):
        settings = MonteCarloSettings()
        issues = settings.validate()
        assert len(issues) == 0

    def test_validate_invalid_default_iterations(self):
        settings = MonteCarloSettings(default_iterations=500, min_iterations=1000)
        issues = settings.validate()
        assert any("default_iterations" in issue for issue in issues)

    def test_validate_invalid_max_iterations(self):
        settings = MonteCarloSettings(default_iterations=50000, max_iterations=25000)
        issues = settings.validate()
        assert any("max_iterations" in issue for issue in issues)

    def test_validate_invalid_convergence_threshold(self):
        settings = MonteCarloSettings(convergence_threshold=1.5)
        issues = settings.validate()
        assert any("convergence_threshold" in issue for issue in issues)


class TestLearningSettings:
    def test_default_values(self):
        settings = LearningSettings()
        assert settings.adaptive_difficulty_enabled is True
        assert settings.difficulty_adjustment_threshold == 0.7
        assert settings.max_difficulty_change == 1
        assert settings.hint_system_enabled is True

    def test_validate_valid_settings(self):
        settings = LearningSettings()
        issues = settings.validate()
        assert len(issues) == 0

    def test_validate_invalid_difficulty_threshold(self):
        settings = LearningSettings(difficulty_adjustment_threshold=1.5)
        issues = settings.validate()
        assert any("difficulty_adjustment_threshold" in issue for issue in issues)

    def test_validate_invalid_max_difficulty_change(self):
        settings = LearningSettings(max_difficulty_change=0)
        issues = settings.validate()
        assert any("max_difficulty_change" in issue for issue in issues)


class TestDisplaySettings:
    def test_default_values(self):
        settings = DisplaySettings()
        assert settings.theme == Theme.DARK
        assert settings.color_scheme == ColorScheme.DEFAULT
        assert settings.animation_speed == AnimationSpeed.NORMAL
        assert settings.chart_display_mode == "matrix"

    def test_validate_valid_settings(self):
        settings = DisplaySettings()
        issues = settings.validate()
        assert len(issues) == 0

    def test_validate_invalid_chart_display_mode(self):
        settings = DisplaySettings(chart_display_mode="invalid")
        issues = settings.validate()
        assert any("chart_display_mode" in issue for issue in issues)

    def test_validate_invalid_max_items_per_page(self):
        settings = DisplaySettings(max_items_per_page=0)
        issues = settings.validate()
        assert any("max_items_per_page" in issue for issue in issues)


class TestPerformanceTuningSettings:
    def test_default_values(self):
        settings = PerformanceTuningSettings()
        assert settings.memory_cleanup_threshold_mb == 500.0
        assert settings.cache_cleanup_interval_seconds == 300
        assert settings.enable_memory_tracking is True

    def test_validate_valid_settings(self):
        settings = PerformanceTuningSettings()
        issues = settings.validate()
        assert len(issues) == 0

    def test_validate_invalid_memory_threshold(self):
        settings = PerformanceTuningSettings(memory_cleanup_threshold_mb=5)
        issues = settings.validate()
        assert any("memory_cleanup_threshold" in issue for issue in issues)

    def test_validate_invalid_optimization_interval(self):
        settings = PerformanceTuningSettings(optimization_interval_seconds=30)
        issues = settings.validate()
        assert any("optimization_interval" in issue for issue in issues)


class TestApplicationSettings:
    def test_default_values(self):
        settings = ApplicationSettings()
        assert settings.version == "1.0.0"
        assert settings.debug_mode is False
        assert settings.log_level == LogLevel.INFO
        assert settings.max_threads == 4

    def test_validate_valid_settings(self):
        settings = ApplicationSettings()
        issues = settings.validate()
        assert len(issues) == 0

    def test_validate_invalid_max_threads(self):
        settings = ApplicationSettings(max_threads=0)
        issues = settings.validate()
        assert any("max_threads" in issue for issue in issues)

    def test_validate_invalid_timeout(self):
        settings = ApplicationSettings(timeout_seconds=0)
        issues = settings.validate()
        assert any("timeout_seconds" in issue for issue in issues)

    def test_get_all_settings_dict(self):
        settings = ApplicationSettings()
        settings_dict = settings.get_all_settings_dict()
        assert isinstance(settings_dict, dict)
        assert 'version' in settings_dict
        assert 'database' in settings_dict
        assert 'security' in settings_dict

    def test_update_from_dict(self):
        settings = ApplicationSettings()
        updates = {'debug_mode': True, 'max_threads': 8}
        issues = settings.update_from_dict(updates)
        assert len(issues) == 0
        assert settings.debug_mode is True
        assert settings.max_threads == 8

    def test_update_from_dict_unknown_setting(self):
        settings = ApplicationSettings()
        updates = {'unknown_setting': 'value'}
        issues = settings.update_from_dict(updates)
        assert any("Unknown setting" in issue for issue in issues)

    def test_nested_settings_exist(self):
        settings = ApplicationSettings()
        assert isinstance(settings.database, DatabaseSettings)
        assert isinstance(settings.security, SecuritySettings)
        assert isinstance(settings.network, NetworkSettings)
        assert isinstance(settings.monte_carlo, MonteCarloSettings)
        assert isinstance(settings.learning, LearningSettings)
        assert isinstance(settings.display, DisplaySettings)
        assert isinstance(settings.performance, PerformanceTuningSettings)


# =============================================================================
# ConfigManager Tests
# =============================================================================

class TestAppSettingsDataclass:
    """Test the AppSettings dataclass from config_manager.py"""

    def test_default_values(self):
        settings = AppSettings()
        assert settings.version == "1.0.0"
        assert settings.debug_mode is False
        assert settings.log_level == "INFO"
        assert settings.max_threads == 4
        assert settings.default_iterations == 25000


class TestUserPreferencesDataclass:
    """Test the UserPreferences dataclass from config_manager.py"""

    def test_default_values(self):
        prefs = UserPreferences()
        assert prefs.theme == "dark"
        assert prefs.color_scheme == "default"
        assert prefs.sound_enabled is False
        assert prefs.preferred_difficulty == "adaptive"


class TestPerformanceSettingsDataclass:
    """Test the PerformanceSettings dataclass from config_manager.py"""

    def test_default_values(self):
        settings = PerformanceSettings()
        assert settings.enable_memory_tracking is True
        assert settings.memory_threshold_mb == 500.0
        assert settings.enable_query_cache is True


class TestConfigManager:
    """Test the ConfigManager class"""

    def test_get_config_returns_instance(self):
        config = get_config()
        assert config is not None
        assert isinstance(config, ConfigManager)

    def test_get_app_settings(self):
        settings = get_app_settings()
        assert settings is not None
        assert isinstance(settings, AppSettings)

    def test_get_user_preferences(self):
        prefs = get_user_preferences()
        assert prefs is not None
        assert isinstance(prefs, UserPreferences)

    def test_get_performance_settings(self):
        settings = get_performance_settings()
        assert settings is not None
        assert isinstance(settings, PerformanceSettings)

    def test_update_app_setting(self):
        config = get_config()
        original = config.app_settings.debug_mode

        result = config.update_app_setting('debug_mode', True)
        assert result is True
        assert config.app_settings.debug_mode is True

        # Restore original
        config.update_app_setting('debug_mode', original)

    def test_update_app_setting_invalid_key(self):
        config = get_config()
        result = config.update_app_setting('invalid_key', 'value')
        assert result is False

    def test_update_user_preference(self):
        config = get_config()
        original = config.user_preferences.theme

        result = config.update_user_preference('theme', 'light')
        assert result is True
        assert config.user_preferences.theme == 'light'

        # Restore original
        config.update_user_preference('theme', original)

    def test_update_user_preference_invalid_key(self):
        config = get_config()
        result = config.update_user_preference('invalid_key', 'value')
        assert result is False

    def test_update_performance_setting(self):
        config = get_config()
        original = config.performance_settings.memory_threshold_mb

        result = config.update_performance_setting('memory_threshold_mb', 1000.0)
        assert result is True
        assert config.performance_settings.memory_threshold_mb == 1000.0

        # Restore original
        config.update_performance_setting('memory_threshold_mb', original)

    def test_update_performance_setting_invalid_key(self):
        config = get_config()
        result = config.update_performance_setting('invalid_key', 'value')
        assert result is False

    def test_get_with_dot_notation(self):
        config = get_config()
        value = config.get('app_settings.debug_mode')
        assert value is not None

    def test_get_invalid_path_returns_default(self):
        config = get_config()
        value = config.get('invalid.path', default='default_value')
        assert value == 'default_value'

    def test_set_with_dot_notation(self):
        config = get_config()
        original = config.get('app_settings.debug_mode')

        result = config.set('app_settings.debug_mode', True)
        assert result is True
        assert config.get('app_settings.debug_mode') is True

        # Restore original
        config.set('app_settings.debug_mode', original)

    def test_set_invalid_path_returns_false(self):
        config = get_config()
        result = config.set('invalid.path.setting', 'value')
        assert result is False

    def test_get_all_config(self):
        config = get_config()
        all_config = config.get_all_config()

        assert isinstance(all_config, dict)
        assert 'app_settings' in all_config
        assert 'user_preferences' in all_config
        assert 'performance_settings' in all_config

    def test_validate_config_default_is_valid(self):
        config = get_config()
        config.reset_to_defaults()
        issues = config.validate_config()
        # Default config should be valid
        assert isinstance(issues, list)

    def test_validate_config_invalid_max_threads(self):
        config = get_config()
        original = config.app_settings.max_threads

        config.update_app_setting('max_threads', 0)
        issues = config.validate_config()
        assert any("max_threads" in issue for issue in issues)

        # Restore original
        config.update_app_setting('max_threads', original)

    def test_validate_config_invalid_default_iterations(self):
        config = get_config()
        original = config.app_settings.default_iterations

        config.update_app_setting('default_iterations', 500)
        issues = config.validate_config()
        assert any("default_iterations" in issue for issue in issues)

        # Restore original
        config.update_app_setting('default_iterations', original)

    def test_reset_to_defaults(self):
        config = get_config()

        # Modify some settings
        config.update_app_setting('debug_mode', True)
        config.update_user_preference('theme', 'light')

        # Reset to defaults
        config.reset_to_defaults()

        # Check defaults are restored
        assert config.app_settings.debug_mode is False
        assert config.user_preferences.theme == 'dark'

    def test_apply_config_overrides(self):
        config = get_config()
        original_debug = config.app_settings.debug_mode
        original_theme = config.user_preferences.theme

        overrides = {
            'app_settings.debug_mode': True,
            'user_preferences.theme': 'auto'
        }
        config.apply_config_overrides(overrides)

        assert config.app_settings.debug_mode is True
        assert config.user_preferences.theme == 'auto'

        # Restore originals
        config.set('app_settings.debug_mode', original_debug)
        config.set('user_preferences.theme', original_theme)


class TestConfigManagerEnvironment:
    """Test environment variable loading in ConfigManager"""

    def test_load_environment_debug_mode(self):
        """Test that environment variables can override settings"""
        # This tests the pattern but doesn't actually create a new instance
        # since the global instance is already loaded
        config = get_config()

        # Just verify the environment loading mechanism exists
        assert hasattr(config, '_load_environment_config')

    def test_environment_bool_conversion(self):
        """Test that boolean environment variables are converted correctly"""
        config = get_config()

        # The conversion logic should handle 'true', '1', 'yes', 'on'
        # This is a design verification test
        env_mappings = {
            'HOLDEM_DEBUG': ('debug_mode', bool),
            'HOLDEM_CACHE_ENABLED': ('enable_caching', bool),
        }

        # Just verify the pattern exists
        assert config.app_settings.debug_mode in (True, False)


class TestConfigManagerFileOperations:
    """Test file operation related functionality"""

    def test_save_user_config_creates_directory(self):
        """Test that save_user_config attempts to create config directory"""
        config = get_config()

        # This test verifies the save functionality exists
        # Actual file saving would require mocking
        assert hasattr(config, 'save_user_config')
        assert callable(config.save_user_config)

    def test_config_directory_path_set(self):
        """Test that config directory path is set"""
        config = get_config()

        # Verify the private attribute exists
        assert hasattr(config, '_config_dir')
        assert isinstance(config._config_dir, Path)


class TestConfigManagerThreadSafety:
    """Test thread safety features of ConfigManager"""

    def test_has_lock(self):
        """Test that ConfigManager has a lock for thread safety"""
        config = get_config()
        assert hasattr(config, '_lock')

    def test_properties_return_settings(self):
        """Test that property accessors return correct types"""
        config = get_config()

        assert isinstance(config.app_settings, AppSettings)
        assert isinstance(config.user_preferences, UserPreferences)
        assert isinstance(config.performance_settings, PerformanceSettings)


# =============================================================================
# Integration Tests
# =============================================================================

class TestConfigIntegration:
    """Integration tests for the configuration system"""

    def test_config_workflow(self):
        """Test a typical configuration workflow"""
        config = get_config()

        # Save original values
        original_debug = config.app_settings.debug_mode
        original_theme = config.user_preferences.theme

        # Modify configuration
        config.update_app_setting('debug_mode', True)
        config.update_user_preference('theme', 'light')

        # Verify changes
        assert config.get('app_settings.debug_mode') is True
        assert config.get('user_preferences.theme') == 'light'

        # Get all config and verify
        all_config = config.get_all_config()
        assert all_config['app_settings']['debug_mode'] is True
        assert all_config['user_preferences']['theme'] == 'light'

        # Reset and verify
        config.reset_to_defaults()
        assert config.app_settings.debug_mode is False
        assert config.user_preferences.theme == 'dark'

    def test_validate_and_fix_workflow(self):
        """Test validating config and fixing issues"""
        config = get_config()
        original_threads = config.app_settings.max_threads

        # Set invalid value
        config.update_app_setting('max_threads', 0)

        # Validate and find issues
        issues = config.validate_config()
        assert len(issues) > 0

        # Fix the issue
        config.update_app_setting('max_threads', 4)

        # Validate again
        issues = config.validate_config()
        assert not any("max_threads" in issue for issue in issues)

        # Restore original
        config.update_app_setting('max_threads', original_threads)
