"""
Centralized logging utilities for Holdem CLI.

This module provides consistent logging setup and utilities
across all components of the application.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional
from datetime import datetime


class HoldemLogger:
    """Centralized logger for Holdem CLI with consistent formatting."""

    def __init__(self, name: str = "holdem_cli", level: int = logging.INFO):
        """Initialize the logger with consistent formatting."""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Clear existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Create formatter
        formatter = logging.Formatter(
            fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File handler (if log directory exists or can be created)
        try:
            log_dir = self._get_log_directory()
            log_dir.mkdir(parents=True, exist_ok=True)

            log_file = log_dir / f"holdem_cli_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            file_handler.setLevel(logging.DEBUG)  # More detailed logging to file
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        except Exception as e:
            # If file logging fails, just log to console
            self.logger.warning(f"Could not set up file logging: {e}")

    def _get_log_directory(self) -> Path:
        """Get the appropriate log directory based on OS."""
        import os

        if os.name == 'nt':  # Windows
            base_dir = Path(os.environ.get('APPDATA', '~')).expanduser()
        elif os.name == 'posix':
            if os.uname().sysname == 'Darwin':  # macOS
                base_dir = Path('~/Library/Logs').expanduser()
            else:  # Linux
                base_dir = Path(os.environ.get('XDG_DATA_HOME', '~/.local/share')).expanduser() / 'logs'
        else:
            base_dir = Path('~/.local/share/logs').expanduser()

        return base_dir / 'holdem-cli'

    def debug(self, message: str, *args, **kwargs) -> None:
        """Log debug message."""
        self.logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs) -> None:
        """Log info message."""
        self.logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs) -> None:
        """Log warning message."""
        self.logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs) -> None:
        """Log error message."""
        self.logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs) -> None:
        """Log critical message."""
        self.logger.critical(message, *args, **kwargs)

    def exception(self, message: str, *args, **kwargs) -> None:
        """Log exception with traceback."""
        self.logger.exception(message, *args, **kwargs)


# Global logger instance
_logger = HoldemLogger()


def get_logger() -> HoldemLogger:
    """Get the global logger instance."""
    return _logger


def log_function_call(func_name: str, args: Optional[dict] = None) -> None:
    """Log function call for debugging purposes."""
    if args:
        arg_str = ", ".join(f"{k}={v}" for k, v in args.items())
        get_logger().debug(f"Called {func_name}({arg_str})")
    else:
        get_logger().debug(f"Called {func_name}()")


def log_performance(func_name: str, duration_ms: float) -> None:
    """Log performance metrics."""
    get_logger().info(".2f")


def log_error_with_context(error: Exception, context: str = "") -> None:
    """Log error with additional context."""
    context_msg = f" in {context}" if context else ""
    get_logger().error(f"Error{context_msg}: {error}")
    get_logger().exception(f"Full traceback for error{context_msg}")


def log_security_event(event: str, details: Optional[dict] = None) -> None:
    """Log security-related events."""
    details_str = f" - {details}" if details else ""
    get_logger().warning(f"Security event: {event}{details_str}")
