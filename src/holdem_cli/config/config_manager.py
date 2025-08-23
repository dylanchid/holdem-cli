"""
Centralized configuration management for Holdem CLI.

This module provides a unified interface for managing application configuration
with support for environment variables, user preferences, and runtime settings.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, asdict
import threading

from ..utils.logging_utils import get_logger


@dataclass
class AppSettings:
    """Core application settings."""
    version: str = "1.0.0"
    debug_mode: bool = False
    log_level: str = "INFO"
    max_threads: int = 4
    timeout_seconds: int = 30
    enable_caching: bool = True
    enable_metrics: bool = True

    # Security settings
    secure_random: bool = True
    validate_inputs: bool = True
    sanitize_outputs: bool = True

    # Performance settings
    max_cache_size_mb: float = 100.0
    chart_cache_size_mb: float = 50.0
    query_cache_ttl_seconds: int = 300
    max_concurrent_charts: int = 10

    # Database settings
    db_optimization_enabled: bool = True
    db_batch_size: int = 100
    db_connection_timeout: int = 30

    # Monte Carlo settings
    default_iterations: int = 25000
    fallback_iterations: int = 2500
    max_iterations: int = 100000
    iteration_timeout_seconds: float = 2.0

    # Quiz settings
    adaptive_difficulty_enabled: bool = True
    quiz_timeout_seconds: int = 300
    max_quiz_questions: int = 50

    # Simulator settings
    default_ai_level: str = "easy"
    max_simulation_time_seconds: int = 60
    simulation_timeout_enabled: bool = True


@dataclass
class UserPreferences:
    """User-specific preferences."""
    theme: str = "dark"
    color_scheme: str = "default"
    sound_enabled: bool = False
    notifications_enabled: bool = True
    auto_save_enabled: bool = True
    show_hints: bool = True
    compact_display: bool = False

    # Learning preferences
    preferred_difficulty: str = "adaptive"
    show_explanations: bool = True
    auto_advance: bool = True
    review_mistakes: bool = True

    # Performance preferences
    animation_speed: str = "normal"
    chart_display_mode: str = "matrix"
    max_history_items: int = 100

    # Privacy settings
    collect_usage_stats: bool = False
    share_progress: bool = False
    enable_cloud_sync: bool = False


@dataclass
class PerformanceSettings:
    """Performance monitoring and optimization settings."""
    enable_memory_tracking: bool = True
    memory_threshold_mb: float = 500.0
    enable_cpu_monitoring: bool = False
    performance_log_interval_seconds: int = 60

    # Cache settings
    enable_query_cache: bool = True
    enable_chart_cache: bool = True
    cache_cleanup_interval_seconds: int = 300

    # Optimization flags
    enable_parallel_processing: bool = True
    enable_batch_operations: bool = True
    enable_compression: bool = False


class ConfigManager:
    """Centralized configuration manager with thread-safe operations."""

    def __init__(self):
        """Initialize configuration manager."""
        self._logger = get_logger()
        self._lock = threading.Lock()

        # Configuration sources (in priority order)
        self._config_sources = [
            self._load_environment_config,
            self._load_user_config,
            self._load_default_config
        ]

        # Configuration instances
        self._app_settings = AppSettings()
        self._user_preferences = UserPreferences()
        self._performance_settings = PerformanceSettings()

        # Configuration file paths
        self._config_dir = self._get_config_directory()
        self._user_config_file = self._config_dir / "user_config.json"
        self._app_config_file = self._config_dir / "app_config.json"

        # Load configuration
        self._load_configuration()

    def _get_config_directory(self) -> Path:
        """Get the configuration directory based on OS."""
        if os.name == 'nt':  # Windows
            base_dir = Path(os.environ.get('APPDATA', '~')).expanduser()
        elif os.name == 'posix':
            if os.uname().sysname == 'Darwin':  # macOS
                base_dir = Path('~/Library/Application Support').expanduser()
            else:  # Linux
                base_dir = Path(os.environ.get('XDG_CONFIG_HOME', '~/.config')).expanduser()
        else:
            base_dir = Path('~/.config').expanduser()

        return base_dir / 'holdem-cli'

    def _load_configuration(self) -> None:
        """Load configuration from all sources in priority order."""
        with self._lock:
            for config_loader in self._config_sources:
                try:
                    config_loader()
                except Exception as e:
                    self._logger.warning(f"Failed to load configuration from {config_loader.__name__}: {e}")

            self._logger.info("Configuration loaded successfully")

    def _load_environment_config(self) -> None:
        """Load configuration from environment variables."""
        # App settings from environment
        env_mappings = {
            'HOLDEM_DEBUG': ('debug_mode', bool),
            'HOLDEM_LOG_LEVEL': ('log_level', str),
            'HOLDEM_MAX_THREADS': ('max_threads', int),
            'HOLDEM_TIMEOUT': ('timeout_seconds', int),
            'HOLDEM_CACHE_ENABLED': ('enable_caching', bool),
            'HOLDEM_METRICS_ENABLED': ('enable_metrics', bool),
            'HOLDEM_SECURE_RANDOM': ('secure_random', bool),
            'HOLDEM_DEFAULT_ITERATIONS': ('default_iterations', int),
            'HOLDEM_MAX_ITERATIONS': ('max_iterations', int),
        }

        for env_var, (attr_name, attr_type) in env_mappings.items():
            if env_var in os.environ:
                value = os.environ[env_var]
                try:
                    if attr_type == bool:
                        # Handle boolean conversion
                        converted_value = value.lower() in ('true', '1', 'yes', 'on')
                    else:
                        converted_value = attr_type(value)

                    setattr(self._app_settings, attr_name, converted_value)
                    self._logger.debug(f"Environment config: {attr_name} = {converted_value}")
                except (ValueError, TypeError) as e:
                    self._logger.warning(f"Invalid environment value for {env_var}: {value} ({e})")

    def _load_user_config(self) -> None:
        """Load user configuration from file."""
        if not self._user_config_file.exists():
            self._logger.debug("No user configuration file found")
            return

        try:
            with open(self._user_config_file, 'r') as f:
                config_data = json.load(f)

            # Load user preferences
            if 'user_preferences' in config_data:
                user_prefs = config_data['user_preferences']
                for key, value in user_prefs.items():
                    if hasattr(self._user_preferences, key):
                        setattr(self._user_preferences, key, value)
                        self._logger.debug(f"User config: {key} = {value}")

            # Load performance settings
            if 'performance_settings' in config_data:
                perf_settings = config_data['performance_settings']
                for key, value in perf_settings.items():
                    if hasattr(self._performance_settings, key):
                        setattr(self._performance_settings, key, value)
                        self._logger.debug(f"Performance config: {key} = {value}")

        except (json.JSONDecodeError, IOError) as e:
            self._logger.warning(f"Failed to load user configuration: {e}")

    def _load_default_config(self) -> None:
        """Load default configuration values."""
        # Defaults are already set in the dataclass definitions
        self._logger.debug("Using default configuration values")

    def save_user_config(self) -> bool:
        """Save current user configuration to file."""
        try:
            self._config_dir.mkdir(parents=True, exist_ok=True)

            config_data = {
                'user_preferences': asdict(self._user_preferences),
                'performance_settings': asdict(self._performance_settings)
            }

            with open(self._user_config_file, 'w') as f:
                json.dump(config_data, f, indent=2)

            self._logger.info("User configuration saved successfully")
            return True

        except Exception as e:
            self._logger.error(f"Failed to save user configuration: {e}")
            return False

    def reset_to_defaults(self) -> None:
        """Reset all configuration to default values."""
        with self._lock:
            self._app_settings = AppSettings()
            self._user_preferences = UserPreferences()
            self._performance_settings = PerformanceSettings()
            self._logger.info("Configuration reset to defaults")

    # Property accessors
    @property
    def app_settings(self) -> AppSettings:
        """Get application settings."""
        return self._app_settings

    @property
    def user_preferences(self) -> UserPreferences:
        """Get user preferences."""
        return self._user_preferences

    @property
    def performance_settings(self) -> PerformanceSettings:
        """Get performance settings."""
        return self._performance_settings

    # Configuration update methods
    def update_app_setting(self, key: str, value: Any) -> bool:
        """Update an application setting."""
        with self._lock:
            if hasattr(self._app_settings, key):
                setattr(self._app_settings, key, value)
                self._logger.debug(f"Updated app setting: {key} = {value}")
                return True
            return False

    def update_user_preference(self, key: str, value: Any) -> bool:
        """Update a user preference."""
        with self._lock:
            if hasattr(self._user_preferences, key):
                setattr(self._user_preferences, key, value)
                self._logger.debug(f"Updated user preference: {key} = {value}")
                return True
            return False

    def update_performance_setting(self, key: str, value: Any) -> bool:
        """Update a performance setting."""
        with self._lock:
            if hasattr(self._performance_settings, key):
                setattr(self._performance_settings, key, value)
                self._logger.debug(f"Updated performance setting: {key} = {value}")
                return True
            return False

    # Utility methods
    def get(self, path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'app_settings.debug_mode')."""
        try:
            parts = path.split('.')
            obj = self

            for part in parts:
                if hasattr(obj, part):
                    obj = getattr(obj, part)
                else:
                    return default

            return obj
        except Exception:
            return default

    def set(self, path: str, value: Any) -> bool:
        """Set configuration value using dot notation."""
        try:
            parts = path.split('.')
            obj = self

            # Navigate to parent object
            for part in parts[:-1]:
                if hasattr(obj, part):
                    obj = getattr(obj, part)
                else:
                    return False

            # Set the final attribute
            attr_name = parts[-1]
            if hasattr(obj, attr_name):
                setattr(obj, attr_name, value)
                return True

            return False
        except Exception:
            return False

    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration as a dictionary."""
        return {
            'app_settings': asdict(self._app_settings),
            'user_preferences': asdict(self._user_preferences),
            'performance_settings': asdict(self._performance_settings)
        }

    def validate_config(self) -> List[str]:
        """Validate current configuration and return list of issues."""
        issues = []

        # Validate app settings
        if self._app_settings.max_threads < 1:
            issues.append("max_threads must be >= 1")

        if self._app_settings.default_iterations < 1000:
            issues.append("default_iterations must be >= 1000")

        if self._app_settings.timeout_seconds < 1:
            issues.append("timeout_seconds must be >= 1")

        # Validate user preferences
        valid_difficulties = ['easy', 'medium', 'hard', 'adaptive']
        if self._user_preferences.preferred_difficulty not in valid_difficulties:
            issues.append(f"preferred_difficulty must be one of: {valid_difficulties}")

        valid_themes = ['light', 'dark', 'auto']
        if self._user_preferences.theme not in valid_themes:
            issues.append(f"theme must be one of: {valid_themes}")

        return issues

    def apply_config_overrides(self, overrides: Dict[str, Any]) -> None:
        """Apply configuration overrides (useful for testing)."""
        with self._lock:
            for path, value in overrides.items():
                self.set(path, value)
            self._logger.debug(f"Applied {len(overrides)} configuration overrides")


# Global configuration instance
_config_manager = ConfigManager()


def get_config() -> ConfigManager:
    """Get the global configuration manager instance."""
    return _config_manager


def get_app_settings() -> AppSettings:
    """Get application settings."""
    return _config_manager.app_settings


def get_user_preferences() -> UserPreferences:
    """Get user preferences."""
    return _config_manager.user_preferences


def get_performance_settings() -> PerformanceSettings:
    """Get performance settings."""
    return _config_manager.performance_settings
