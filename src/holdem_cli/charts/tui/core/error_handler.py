"""
Error handling and recovery system for TUI components.

This module provides comprehensive error handling including:
- Error boundaries for widgets and screens
- User-friendly error messages
- Error recovery mechanisms
- Error logging and reporting
- Graceful degradation
"""

from typing import Any, Dict, Optional, Callable, Type, Union
from dataclasses import dataclass, field
from datetime import datetime
import traceback
import logging
from contextlib import contextmanager
from enum import Enum, auto

from ..core.events import get_event_bus, EventType, create_error_event


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()


class ErrorCategory(Enum):
    """Error categories for better organization."""
    FILE_IO = auto()
    PARSING = auto()
    VALIDATION = auto()
    NETWORK = auto()
    DATABASE = auto()
    UI_RENDERING = auto()
    MEMORY = auto()
    UNKNOWN = auto()


@dataclass
class TUIError:
    """Structured error information."""
    message: str
    category: ErrorCategory = ErrorCategory.UNKNOWN
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    original_exception: Optional[Exception] = None
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    error_id: Optional[str] = None

    def __post_init__(self):
        if self.error_id is None:
            import uuid
            self.error_id = str(uuid.uuid4())[:8]

    @property
    def user_message(self) -> str:
        """Get user-friendly error message."""
        return self._get_user_friendly_message()

    def _get_user_friendly_message(self) -> str:
        """Generate user-friendly error message based on category and context."""
        base_messages = {
            ErrorCategory.FILE_IO: "File operation failed. Please check file permissions and path.",
            ErrorCategory.PARSING: "Unable to parse the file. Please verify the format.",
            ErrorCategory.VALIDATION: "Invalid data detected. Please review your input.",
            ErrorCategory.NETWORK: "Network connection issue. Please check your internet connection.",
            ErrorCategory.DATABASE: "Database operation failed. Please try again.",
            ErrorCategory.UI_RENDERING: "Display error occurred. The interface may not render correctly.",
            ErrorCategory.MEMORY: "Memory issue detected. Please restart the application.",
            ErrorCategory.UNKNOWN: "An unexpected error occurred. Please restart the application."
        }

        message = base_messages.get(self.category, base_messages[ErrorCategory.UNKNOWN])

        # Add context-specific information
        if self.category == ErrorCategory.FILE_IO and 'file_path' in self.context:
            message += f"\nFile: {self.context['file_path']}"

        if self.category == ErrorCategory.PARSING and 'format_type' in self.context:
            message += f"\nFormat: {self.context['format_type']}"

        return message


class ErrorHandler:
    """
    Centralized error handling system for TUI components.

    Features:
    - Error collection and logging
    - User notification system
    - Recovery mechanisms
    - Error boundary management
    """

    def __init__(self):
        self.errors: list[TUIError] = []
        self.max_errors = 100
        self.recovery_handlers: Dict[ErrorCategory, Callable] = {}
        self.notification_callback: Optional[Callable[[str, ErrorSeverity], None]] = None
        self.logger = logging.getLogger('tui_error_handler')
        self.logger.setLevel(logging.ERROR)

        # Setup event bus integration
        self._event_bus = get_event_bus()

        # Setup default recovery handlers
        self._setup_default_recovery_handlers()

    def handle_error(
        self,
        error: Union[Exception, TUIError],
        context: Optional[Dict[str, Any]] = None,
        notify_user: bool = True
    ) -> TUIError:
        """
        Handle an error with proper logging and user notification.

        Args:
            error: The error to handle
            context: Additional context information
            notify_user: Whether to notify the user

        Returns:
            Structured TUIError object
        """
        if isinstance(error, TUIError):
            tui_error = error
        else:
            tui_error = self._create_tui_error(error, context or {})

        # Add to error list
        self.errors.append(tui_error)
        if len(self.errors) > self.max_errors:
            self.errors.pop(0)

        # Log error
        self.logger.error(f"TUI Error [{tui_error.error_id}]: {tui_error.message}", exc_info=True)

        # Publish error event
        error_event = create_error_event(
            error_message=tui_error.user_message,
            error_type=tui_error.category.name,
            recoverable=tui_error.severity != ErrorSeverity.CRITICAL,
            source=context.get('source', 'unknown') if context else 'unknown'
        )
        self._event_bus.publish_sync(error_event)

        # Notify user if requested
        if notify_user and self.notification_callback:
            self.notification_callback(tui_error.user_message, tui_error.severity)

        # Attempt recovery
        self._attempt_recovery(tui_error)

        return tui_error

    def _create_tui_error(self, exception: Exception, context: Dict[str, Any]) -> TUIError:
        """Create a TUIError from a Python exception."""
        # Categorize the error based on exception type
        error_category = self._categorize_exception(exception)

        # Determine severity
        error_severity = self._get_exception_severity(exception)

        return TUIError(
            message=str(exception),
            category=error_category,
            severity=error_severity,
            original_exception=exception,
            context=context
        )

    def _categorize_exception(self, exception: Exception) -> ErrorCategory:
        """Categorize an exception by type."""
        exception_type = type(exception).__name__

        if exception_type in ['FileNotFoundError', 'PermissionError', 'OSError']:
            return ErrorCategory.FILE_IO
        elif exception_type in ['ValueError', 'TypeError'] and 'parse' in str(exception).lower():
            return ErrorCategory.PARSING
        elif exception_type in ['ValueError', 'TypeError'] and 'valid' in str(exception).lower():
            return ErrorCategory.VALIDATION
        elif exception_type in ['sqlite3.Error', 'DatabaseError']:
            return ErrorCategory.DATABASE
        elif exception_type in ['MemoryError']:
            return ErrorCategory.MEMORY
        else:
            return ErrorCategory.UNKNOWN

    def _get_exception_severity(self, exception: Exception) -> ErrorSeverity:
        """Determine error severity from exception type."""
        exception_type = type(exception).__name__

        if exception_type in ['MemoryError', 'SystemExit']:
            return ErrorSeverity.CRITICAL
        elif exception_type in ['FileNotFoundError', 'PermissionError', 'sqlite3.Error']:
            return ErrorSeverity.HIGH
        elif exception_type in ['ValueError', 'TypeError']:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW

    def _setup_default_recovery_handlers(self):
        """Setup default recovery handlers for different error categories."""
        self.recovery_handlers[ErrorCategory.FILE_IO] = self._recover_file_io_error
        self.recovery_handlers[ErrorCategory.PARSING] = self._recover_parsing_error
        self.recovery_handlers[ErrorCategory.DATABASE] = self._recover_database_error
        self.recovery_handlers[ErrorCategory.MEMORY] = self._recover_memory_error

    def _attempt_recovery(self, error: TUIError):
        """Attempt to recover from an error."""
        if error.category in self.recovery_handlers:
            try:
                handler = self.recovery_handlers[error.category]
                handler(error)
            except Exception as recovery_error:
                self.logger.error(f"Recovery failed: {recovery_error}", exc_info=True)

    def _recover_file_io_error(self, error: TUIError):
        """Recovery handler for file I/O errors."""
        # For file not found, we might try alternative paths
        if 'file_path' in error.context:
            file_path = error.context['file_path']
            # Could implement logic to try alternative paths or create directories
            pass

    def _recover_parsing_error(self, error: TUIError):
        """Recovery handler for parsing errors."""
        # For parsing errors, we might try alternative parsing methods
        if 'file_path' in error.context:
            # Could implement fallback parsing logic
            pass

    def _recover_database_error(self, error: TUIError):
        """Recovery handler for database errors."""
        # For database errors, we might try to reconnect or use cached data
        # Could implement connection retry logic
        pass

    def _recover_memory_error(self, error: TUIError):
        """Recovery handler for memory errors."""
        # For memory errors, we might try to free up resources
        # Could implement cache clearing or garbage collection
        import gc
        gc.collect()

    def set_notification_callback(self, callback: Callable[[str, ErrorSeverity], None]):
        """Set callback for user notifications."""
        self.notification_callback = callback

    def get_recent_errors(self, limit: int = 10) -> list[TUIError]:
        """Get recent errors."""
        return self.errors[-limit:]

    def get_errors_by_category(self, category: ErrorCategory) -> list[TUIError]:
        """Get errors by category."""
        return [error for error in self.errors if error.category == category]

    def clear_errors(self):
        """Clear all errors."""
        self.errors.clear()

    def get_error_summary(self) -> Dict[str, int]:
        """Get summary of errors by category."""
        summary = {}
        for error in self.errors:
            category_name = error.category.name
            summary[category_name] = summary.get(category_name, 0) + 1
        return summary


# Global error handler instance
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Get or create the global error handler instance."""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def reset_error_handler():
    """Reset the global error handler instance."""
    global _error_handler
    _error_handler = None


# Decorator for error handling
def handle_errors(
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    notify_user: bool = True
):
    """
    Decorator to handle errors in functions.

    Args:
        category: Error category
        severity: Error severity
        notify_user: Whether to notify user

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handler = get_error_handler()

                # Add function context
                context = {
                    'function': func.__name__,
                    'module': func.__module__,
                    'args': len(args),
                    'kwargs': list(kwargs.keys())
                }

                # Create and handle TUI error
                tui_error = TUIError(
                    message=str(e),
                    category=category,
                    severity=severity,
                    original_exception=e,
                    context=context
                )

                handler.handle_error(tui_error, context, notify_user)
                return None  # Or raise the original exception if needed

        return wrapper
    return decorator


# Context manager for error handling
@contextmanager
def error_boundary(
    operation: str,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    context: Optional[Dict[str, Any]] = None
):
    """
    Context manager for error boundaries.

    Args:
        operation: Description of the operation being performed
        category: Error category
        context: Additional context information
    """
    handler = get_error_handler()
    full_context = {
        'operation': operation,
        **(context or {})
    }

    try:
        yield
    except Exception as e:
        tui_error = TUIError(
            message=f"Error in {operation}: {str(e)}",
            category=category,
            original_exception=e,
            context=full_context
        )
        handler.handle_error(tui_error, full_context, True)


# Error boundary widget mixin
class ErrorBoundaryMixin:
    """
    Mixin class for widgets with error boundary functionality.

    Widgets can inherit from this to get automatic error handling.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._error_handler = get_error_handler()
        self._error_count = 0
        self._max_errors = 3

    def safe_operation(self, operation: Callable, operation_name: str = "operation"):
        """Execute an operation with error handling."""
        try:
            return operation()
        except Exception as e:
            self._error_count += 1

            if self._error_count <= self._max_errors:
                self._error_handler.handle_error(
                    e,
                    context={
                        'widget': type(self).__name__,
                        'operation': operation_name
                    }
                )
            else:
                # Too many errors, show degraded state
                self._show_error_state()

    def _show_error_state(self):
        """Show error state in the widget."""
        # This should be overridden by subclasses to show appropriate error UI
        pass

    def reset_error_state(self):
        """Reset error state."""
        self._error_count = 0


# Utility functions for common error scenarios
def safe_file_operation(file_path: str, operation: Callable, default_result: Any = None) -> Any:
    """
    Safely perform a file operation with error handling.

    Args:
        file_path: Path to the file being operated on
        operation: Function to execute
        default_result: Default result if operation fails

    Returns:
        Result of operation or default_result
    """
    handler = get_error_handler()

    with error_boundary(f"File operation on {file_path}", ErrorCategory.FILE_IO, {'file_path': file_path}):
        return operation()

    return default_result


def safe_parse_operation(data: str, parser: Callable, format_type: str, default_result: Any = None) -> Any:
    """
    Safely perform a parsing operation with error handling.

    Args:
        data: Data to parse
        parser: Parser function
        format_type: Type of format being parsed
        default_result: Default result if parsing fails

    Returns:
        Parsed result or default_result
    """
    handler = get_error_handler()

    with error_boundary(f"Parsing {format_type}", ErrorCategory.PARSING, {'format_type': format_type}):
        return parser(data)

    return default_result


def create_user_friendly_error_message(exception: Exception) -> str:
    """
    Create a user-friendly error message from an exception.

    Args:
        exception: The exception to convert

    Returns:
        User-friendly error message
    """
    error_messages = {
        FileNotFoundError: "The requested file could not be found. Please check the file path.",
        PermissionError: "You don't have permission to access this file. Please check file permissions.",
        ValueError: "The data format is invalid. Please verify the input format.",
        TypeError: "There's a data type mismatch. Please check the input values.",
        MemoryError: "Not enough memory to complete the operation. Please try with smaller data.",
        OSError: "An operating system error occurred. Please check system resources."
    }

    exception_type = type(exception)
    return error_messages.get(exception_type, f"An unexpected error occurred: {str(exception)}")
