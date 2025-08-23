"""
Configuration settings and validation for Holdem CLI.

This module defines the data structures and validation logic for
application configuration settings.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class LogLevel(Enum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Theme(Enum):
    """UI theme enumeration."""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class ColorScheme(Enum):
    """Color scheme enumeration."""
    DEFAULT = "default"
    HIGH_CONTRAST = "high_contrast"
    COLORBLIND = "colorblind"


class AnimationSpeed(Enum):
    """Animation speed enumeration."""
    SLOW = "slow"
    NORMAL = "normal"
    FAST = "fast"
    INSTANT = "instant"


class Difficulty(Enum):
    """Quiz difficulty enumeration."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    ADAPTIVE = "adaptive"


class AILevel(Enum):
    """AI difficulty level enumeration."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass
class DatabaseSettings:
    """Database-related configuration."""
    connection_timeout: int = 30
    max_connections: int = 5
    enable_connection_pooling: bool = True
    enable_query_logging: bool = False
    enable_performance_monitoring: bool = True
    backup_enabled: bool = True
    backup_interval_hours: int = 24
    max_backup_files: int = 7

    def validate(self) -> List[str]:
        """Validate database settings."""
        issues = []
        if self.connection_timeout < 1:
            issues.append("connection_timeout must be >= 1 second")
        if self.max_connections < 1:
            issues.append("max_connections must be >= 1")
        if self.backup_interval_hours < 1:
            issues.append("backup_interval_hours must be >= 1")
        if self.max_backup_files < 1:
            issues.append("max_backup_files must be >= 1")
        return issues


@dataclass
class SecuritySettings:
    """Security-related configuration."""
    enable_input_validation: bool = True
    enable_output_sanitization: bool = True
    enable_audit_logging: bool = True
    password_min_length: int = 8
    session_timeout_minutes: int = 30
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    enable_encryption: bool = False
    encryption_key_path: Optional[str] = None

    def validate(self) -> List[str]:
        """Validate security settings."""
        issues = []
        if self.password_min_length < 4:
            issues.append("password_min_length must be >= 4")
        if self.session_timeout_minutes < 1:
            issues.append("session_timeout_minutes must be >= 1")
        if self.max_login_attempts < 1:
            issues.append("max_login_attempts must be >= 1")
        if self.lockout_duration_minutes < 1:
            issues.append("lockout_duration_minutes must be >= 1")
        return issues


@dataclass
class NetworkSettings:
    """Network-related configuration."""
    enable_cloud_sync: bool = False
    cloud_sync_url: Optional[str] = None
    cloud_sync_api_key: Optional[str] = None
    sync_interval_minutes: int = 60
    enable_metrics_upload: bool = False
    metrics_upload_url: Optional[str] = None
    request_timeout_seconds: int = 30
    max_retries: int = 3
    retry_delay_seconds: int = 1

    def validate(self) -> List[str]:
        """Validate network settings."""
        issues = []
        if self.enable_cloud_sync and not self.cloud_sync_url:
            issues.append("cloud_sync_url is required when cloud sync is enabled")
        if self.sync_interval_minutes < 1:
            issues.append("sync_interval_minutes must be >= 1")
        if self.request_timeout_seconds < 1:
            issues.append("request_timeout_seconds must be >= 1")
        if self.max_retries < 0:
            issues.append("max_retries must be >= 0")
        if self.retry_delay_seconds < 0:
            issues.append("retry_delay_seconds must be >= 0")
        return issues


@dataclass
class MonteCarloSettings:
    """Monte Carlo simulation configuration."""
    default_iterations: int = 25000
    fallback_iterations: int = 2500
    max_iterations: int = 100000
    min_iterations: int = 1000
    iteration_timeout_seconds: float = 2.0
    enable_adaptive_iterations: bool = True
    convergence_threshold: float = 0.005  # 0.5%
    enable_parallel_processing: bool = True
    max_worker_threads: int = 4

    def validate(self) -> List[str]:
        """Validate Monte Carlo settings."""
        issues = []
        if self.default_iterations < self.min_iterations:
            issues.append(f"default_iterations must be >= min_iterations ({self.min_iterations})")
        if self.fallback_iterations < 100:
            issues.append("fallback_iterations must be >= 100")
        if self.max_iterations < self.default_iterations:
            issues.append("max_iterations must be >= default_iterations")
        if self.iteration_timeout_seconds <= 0:
            issues.append("iteration_timeout_seconds must be > 0")
        if not 0 < self.convergence_threshold < 1:
            issues.append("convergence_threshold must be between 0 and 1")
        if self.max_worker_threads < 1:
            issues.append("max_worker_threads must be >= 1")
        return issues


@dataclass
class LearningSettings:
    """Learning and quiz configuration."""
    adaptive_difficulty_enabled: bool = True
    difficulty_adjustment_threshold: float = 0.7  # 70% correct
    max_difficulty_change: int = 1  # Max levels to change at once
    review_mistakes_enabled: bool = True
    max_review_questions: int = 10
    explanation_timeout_seconds: int = 10
    hint_system_enabled: bool = True
    progress_tracking_enabled: bool = True
    streak_bonus_enabled: bool = True

    def validate(self) -> List[str]:
        """Validate learning settings."""
        issues = []
        if not 0 <= self.difficulty_adjustment_threshold <= 1:
            issues.append("difficulty_adjustment_threshold must be between 0 and 1")
        if self.max_difficulty_change < 1:
            issues.append("max_difficulty_change must be >= 1")
        if self.max_review_questions < 0:
            issues.append("max_review_questions must be >= 0")
        if self.explanation_timeout_seconds < 0:
            issues.append("explanation_timeout_seconds must be >= 0")
        return issues


@dataclass
class DisplaySettings:
    """Display and UI configuration."""
    theme: Theme = Theme.DARK
    color_scheme: ColorScheme = ColorScheme.DEFAULT
    animation_speed: AnimationSpeed = AnimationSpeed.NORMAL
    enable_animations: bool = True
    compact_display: bool = False
    show_hints: bool = True
    show_progress_bars: bool = True
    chart_display_mode: str = "matrix"  # matrix, tree, list
    max_items_per_page: int = 20
    enable_sound_effects: bool = False

    def validate(self) -> List[str]:
        """Validate display settings."""
        issues = []
        valid_chart_modes = ["matrix", "tree", "list", "graph"]
        if self.chart_display_mode not in valid_chart_modes:
            issues.append(f"chart_display_mode must be one of: {valid_chart_modes}")
        if self.max_items_per_page < 1:
            issues.append("max_items_per_page must be >= 1")
        return issues


@dataclass
class PerformanceTuningSettings:
    """Performance tuning configuration."""
    memory_cleanup_threshold_mb: float = 500.0
    cache_cleanup_interval_seconds: int = 300
    enable_memory_tracking: bool = True
    enable_cpu_monitoring: bool = False
    performance_log_interval_seconds: int = 60
    enable_background_optimization: bool = True
    optimization_interval_seconds: int = 3600  # 1 hour

    def validate(self) -> List[str]:
        """Validate performance tuning settings."""
        issues = []
        if self.memory_cleanup_threshold_mb < 10:
            issues.append("memory_cleanup_threshold_mb must be >= 10")
        if self.cache_cleanup_interval_seconds < 10:
            issues.append("cache_cleanup_interval_seconds must be >= 10")
        if self.performance_log_interval_seconds < 10:
            issues.append("performance_log_interval_seconds must be >= 10")
        if self.optimization_interval_seconds < 60:
            issues.append("optimization_interval_seconds must be >= 60")
        return issues


@dataclass
class ApplicationSettings:
    """Complete application configuration."""
    # Core settings
    version: str = "1.0.0"
    debug_mode: bool = False
    log_level: LogLevel = LogLevel.INFO
    max_threads: int = 4
    timeout_seconds: int = 30
    enable_caching: bool = True
    enable_metrics: bool = True

    # Component settings
    database: DatabaseSettings = field(default_factory=DatabaseSettings)
    security: SecuritySettings = field(default_factory=SecuritySettings)
    network: NetworkSettings = field(default_factory=NetworkSettings)
    monte_carlo: MonteCarloSettings = field(default_factory=MonteCarloSettings)
    learning: LearningSettings = field(default_factory=LearningSettings)
    display: DisplaySettings = field(default_factory=DisplaySettings)
    performance: PerformanceTuningSettings = field(default_factory=PerformanceTuningSettings)

    def validate(self) -> List[str]:
        """Validate all settings."""
        issues = []

        # Validate core settings
        if self.max_threads < 1:
            issues.append("max_threads must be >= 1")
        if self.timeout_seconds < 1:
            issues.append("timeout_seconds must be >= 1")

        # Validate component settings
        issues.extend(self.database.validate())
        issues.extend(self.security.validate())
        issues.extend(self.network.validate())
        issues.extend(self.monte_carlo.validate())
        issues.extend(self.learning.validate())
        issues.extend(self.display.validate())
        issues.extend(self.performance.validate())

        return issues

    def get_all_settings_dict(self) -> Dict[str, Any]:
        """Get all settings as a nested dictionary."""
        from dataclasses import asdict
        return asdict(self)

    def update_from_dict(self, updates: Dict[str, Any]) -> List[str]:
        """Update settings from a dictionary, return validation issues."""
        issues = []

        for key, value in updates.items():
            if hasattr(self, key):
                try:
                    setattr(self, key, value)
                except Exception as e:
                    issues.append(f"Failed to update {key}: {e}")
            else:
                issues.append(f"Unknown setting: {key}")

        return issues
