"""
Comprehensive error handling utilities for Holdem CLI.

This module provides standardized error handling patterns, custom exceptions,
error recovery mechanisms, and logging integration.
"""

import traceback
import functools
from typing import Callable, Any, Optional, Dict, List, Type, Union
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
import time
import threading

from .logging_utils import get_logger


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    DATABASE = "database"
    NETWORK = "network"
    FILESYSTEM = "filesystem"
    PERMISSION = "permission"
    RESOURCE = "resource"
    CALCULATION = "calculation"
    USER_INPUT = "user_input"
    SYSTEM = "system"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Context information for errors."""
    operation: str = ""
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    stack_trace: str = ""
    timestamp: float = field(default_factory=time.time)
    thread_id: int = field(default_factory=threading.get_ident)

    def to_dict(self) -> Dict[str, Any]:
        """Convert error context to dictionary."""
        return {
            'operation': self.operation,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'parameters': self.parameters,
            'stack_trace': self.stack_trace,
            'timestamp': self.timestamp,
            'thread_id': self.thread_id
        }


class HoldemError(Exception):
    """Base exception class for Holdem CLI."""

    def __init__(
        self,
        message: str,
        error_code: str = "GENERIC_ERROR",
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        context: Optional[ErrorContext] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.severity = severity
        self.category = category
        self.context = context or ErrorContext()
        self.original_error = original_error

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/serialization."""
        return {
            'error_code': self.error_code,
            'message': self.message,
            'severity': self.severity.value,
            'category': self.category.value,
            'context': self.context.to_dict(),
            'original_error': str(self.original_error) if self.original_error else None,
            'type': self.__class__.__name__
        }


# Specific exception classes
class ValidationError(HoldemError):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            severity=ErrorSeverity.LOW,
            category=ErrorCategory.VALIDATION,
            **kwargs
        )
        self.field = field


class ConfigurationError(HoldemError):
    """Raised when configuration issues occur."""

    def __init__(self, message: str, setting: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            error_code="CONFIG_ERROR",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.CONFIGURATION,
            **kwargs
        )
        self.setting = setting


class DatabaseError(HoldemError):
    """Raised when database operations fail."""

    def __init__(self, message: str, operation: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            error_code="DB_ERROR",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DATABASE,
            **kwargs
        )
        self.operation = operation


class PokerCalculationError(HoldemError):
    """Raised when poker calculations fail."""

    def __init__(self, message: str, calculation_type: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            error_code="CALCULATION_ERROR",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.CALCULATION,
            **kwargs
        )
        self.calculation_type = calculation_type


class ResourceError(HoldemError):
    """Raised when resource allocation fails."""

    def __init__(self, message: str, resource_type: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            error_code="RESOURCE_ERROR",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.RESOURCE,
            **kwargs
        )
        self.resource_type = resource_type


class ErrorHandler:
    """Central error handling and recovery system."""

    def __init__(self):
        """Initialize error handler."""
        self._logger = get_logger()
        self._error_history: List[HoldemError] = []
        self._recovery_strategies: Dict[str, Callable] = {}
        self._error_counts: Dict[str, int] = {}
        self._lock = threading.Lock()

    def handle_error(
        self,
        error: Exception,
        context: Optional[ErrorContext] = None,
        re_raise: bool = True
    ) -> Optional[HoldemError]:
        """Handle an error with logging and optional recovery."""

        # Convert to HoldemError if needed
        if isinstance(error, HoldemError):
            holdem_error = error
        else:
            holdem_error = HoldemError(
                message=str(error),
                original_error=error,
                context=context
            )

        # Update context with stack trace if not present
        if not holdem_error.context.stack_trace:
            holdem_error.context.stack_trace = traceback.format_exc()

        # Update context
        if context:
            holdem_error.context = context

        # Log error
        self._log_error(holdem_error)

        # Track error
        self._track_error(holdem_error)

        # Attempt recovery
        recovered = self._attempt_recovery(holdem_error)
        if recovered:
            self._logger.info(f"Successfully recovered from error: {holdem_error.error_code}")
            return None

        # Re-raise if requested
        if re_raise:
            raise holdem_error

        return holdem_error

    def _log_error(self, error: HoldemError) -> None:
        """Log error with appropriate level based on severity."""
        error_dict = error.to_dict()

        if error.severity == ErrorSeverity.LOW:
            self._logger.debug(f"Low severity error: {error}", extra=error_dict)
        elif error.severity == ErrorSeverity.MEDIUM:
            self._logger.warning(f"Medium severity error: {error}", extra=error_dict)
        elif error.severity == ErrorSeverity.HIGH:
            self._logger.error(f"High severity error: {error}", extra=error_dict)
        elif error.severity == ErrorSeverity.CRITICAL:
            self._logger.critical(f"Critical error: {error}", extra=error_dict)

    def _track_error(self, error: HoldemError) -> None:
        """Track error for monitoring and analysis."""
        with self._lock:
            self._error_history.append(error)
            self._error_counts[error.error_code] = self._error_counts.get(error.error_code, 0) + 1

            # Keep only recent errors (last 1000)
            if len(self._error_history) > 1000:
                self._error_history = self._error_history[-1000:]

    def _attempt_recovery(self, error: HoldemError) -> bool:
        """Attempt to recover from error using registered strategies."""
        recovery_func = self._recovery_strategies.get(error.error_code)
        if recovery_func:
            try:
                return recovery_func(error)
            except Exception as recovery_error:
                self._logger.error(f"Recovery failed for {error.error_code}: {recovery_error}")
                return False
        return False

    def register_recovery_strategy(self, error_code: str, strategy: Callable[[HoldemError], bool]) -> None:
        """Register a recovery strategy for an error code."""
        self._recovery_strategies[error_code] = strategy

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring."""
        with self._lock:
            return {
                'total_errors': len(self._error_history),
                'error_counts': self._error_counts.copy(),
                'recent_errors': [e.to_dict() for e in self._error_history[-10:]],
                'recovery_strategies': list(self._recovery_strategies.keys())
            }

    def clear_error_history(self) -> None:
        """Clear error history."""
        with self._lock:
            self._error_history.clear()
            self._error_counts.clear()


# Global error handler instance
_error_handler = ErrorHandler()


def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance."""
    return _error_handler


def handle_errors(
    operation: str = "",
    re_raise: bool = True,
    log_errors: bool = True
):
    """Decorator for comprehensive error handling."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            context = ErrorContext(operation=operation)

            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    _error_handler.handle_error(e, context, re_raise)
                else:
                    raise

        return wrapper

    return decorator


def with_error_context(**context_kwargs):
    """Decorator to add context to errors."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            context = ErrorContext(**context_kwargs)
            try:
                return func(*args, **kwargs)
            except Exception as e:
                _error_handler.handle_error(e, context, re_raise=True)

        return wrapper

    return decorator


@contextmanager
def error_context(operation: str = "", **kwargs):
    """Context manager for adding error context."""

    context = ErrorContext(operation=operation, parameters=kwargs)
    try:
        yield context
    except Exception as e:
        _error_handler.handle_error(e, context, re_raise=True)


def safe_operation(
    operation: str,
    fallback: Any = None,
    log_error: bool = True
):
    """Decorator for safe operations with fallbacks."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    context = ErrorContext(operation=operation)
                    _error_handler.handle_error(e, context, re_raise=False)

                return fallback

        return wrapper

    return decorator


def validate_and_handle(
    validator: Callable[[Any], bool],
    error_message: str = "Validation failed"
):
    """Decorator that validates input and handles validation errors."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Validate first argument (typically self is not validated)
            if len(args) > 1:
                if not validator(args[1]):  # Skip self
                    raise ValidationError(error_message)

            # Validate keyword arguments
            for key, value in kwargs.items():
                if not validator(value):
                    raise ValidationError(f"{error_message}: {key}={value}")

            return func(*args, **kwargs)

        return wrapper

    return decorator


def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception
):
    """Decorator that retries operations on failure."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        break

                    get_logger().warning(
                        f"Operation {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}), "
                        ".1f"
                    )

                    time.sleep(current_delay)
                    current_delay *= backoff

            # If we get here, all retries failed
            context = ErrorContext(
                operation=f"{func.__name__}_retry",
                parameters={'max_retries': max_retries, 'final_delay': current_delay}
            )

            raise HoldemError(
                message=f"Operation failed after {max_retries + 1} attempts",
                original_error=last_exception,
                context=context
            )

        return wrapper

    return decorator


# Convenience functions for common error scenarios
def log_error_and_continue(error: Exception, operation: str = "") -> None:
    """Log an error but continue execution."""
    context = ErrorContext(operation=operation)
    _error_handler.handle_error(error, context, re_raise=False)


def create_user_friendly_error(error: Exception) -> str:
    """Create a user-friendly error message from an exception."""

    if isinstance(error, ValidationError):
        return f"Input validation failed: {error.message}"

    elif isinstance(error, ConfigurationError):
        return f"Configuration issue: {error.message}"

    elif isinstance(error, DatabaseError):
        return "A database error occurred. Please try again."

    elif isinstance(error, PokerCalculationError):
        return f"Calculation error: {error.message}"

    elif isinstance(error, ResourceError):
        return "System resources are currently unavailable. Please try again later."

    else:
        return "An unexpected error occurred. Please try again or contact support."


def setup_error_recovery() -> None:
    """Set up common error recovery strategies."""

    def retry_database_connection(error: HoldemError) -> bool:
        """Retry database connections on failure."""
        if error.category == ErrorCategory.DATABASE:
            # Simple retry logic - in real implementation, you'd have
            # more sophisticated connection management
            time.sleep(1)
            return True
        return False

    def handle_validation_error(error: HoldemError) -> bool:
        """Handle validation errors (typically not recoverable)."""
        return False  # Validation errors are usually not recoverable

    # Register recovery strategies
    _error_handler.register_recovery_strategy("DB_CONNECTION_ERROR", retry_database_connection)
    _error_handler.register_recovery_strategy("VALIDATION_ERROR", handle_validation_error)


# Initialize error recovery on module import
setup_error_recovery()
