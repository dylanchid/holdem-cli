"""
Configuration management for Holdem CLI.

This module provides centralized configuration management with support for
environment variables, user preferences, and application settings.
"""

from .config_manager import (
    ConfigManager, get_config, get_app_settings, get_user_preferences,
    get_performance_settings, AppSettings, UserPreferences, PerformanceSettings
)
from .settings import (
    LogLevel, Theme, ColorScheme, AnimationSpeed, Difficulty, AILevel,
    DatabaseSettings, SecuritySettings, NetworkSettings, MonteCarloSettings,
    LearningSettings, DisplaySettings, PerformanceTuningSettings, ApplicationSettings
)

__all__ = [
    'ConfigManager', 'get_config', 'get_app_settings', 'get_user_preferences',
    'get_performance_settings', 'AppSettings', 'UserPreferences', 'PerformanceSettings',
    'LogLevel', 'Theme', 'ColorScheme', 'AnimationSpeed', 'Difficulty', 'AILevel',
    'DatabaseSettings', 'SecuritySettings', 'NetworkSettings', 'MonteCarloSettings',
    'LearningSettings', 'DisplaySettings', 'PerformanceTuningSettings', 'ApplicationSettings'
]
