"""
Error boundary widget for TUI components.

This widget provides error boundaries that can catch and handle errors
in child widgets, providing graceful degradation and recovery options.
"""

from textual.widgets import Static, Button, Label
from textual.containers import Vertical, Horizontal
from textual.widget import Widget
from textual.message import Message
from textual import events, on
from textual.reactive import reactive
from typing import Optional, Dict, Any, Callable
from datetime import datetime

from ...tui.core.error_handler import get_error_handler, ErrorBoundaryMixin, TUIError, ErrorSeverity


class ErrorBoundaryWidget(Widget, ErrorBoundaryMixin):
    """
    Error boundary widget that wraps child widgets and handles errors gracefully.

    Features:
    - Catches exceptions from child operations
    - Displays user-friendly error messages
    - Provides recovery options
    - Logs errors for debugging
    - Graceful degradation
    """

    CSS = """
    ErrorBoundaryWidget {
        width: 100%;
        height: auto;
        border: solid $error;
        background: $surface;
        padding: 1;
    }

    ErrorBoundaryWidget.error {
        border: solid $error;
        background: $error-lighten-3;
    }

    ErrorBoundaryWidget.recovering {
        border: solid $warning;
        background: $warning-lighten-3;
    }

    .error-header {
        text-style: bold;
        color: $error;
        margin: 0 0 1 0;
    }

    .error-message {
        color: $text;
        margin: 0 0 1 0;
    }

    .recovery-options {
        margin: 1 0 0 0;
    }

    .recovery-button {
        margin: 0 1 0 0;
    }
    """

    # Reactive state
    has_error: reactive[bool] = reactive(False)
    is_recovering: reactive[bool] = reactive(False)
    error_message: reactive[str] = reactive("")
    recovery_attempts: reactive[int] = reactive(0)

    def __init__(self, child_widget: Optional[Widget] = None, **kwargs):
        super().__init__(**kwargs)
        self.child_widget = child_widget
        self.last_error: Optional[TUIError] = None
        self.error_timestamp: Optional[datetime] = None
        self.max_recovery_attempts = 3

    def compose(self):
        """Compose the error boundary layout."""
        if self.has_error:
            yield self._compose_error_state()
        elif self.is_recovering:
            yield self._compose_recovering_state()
        else:
            yield self._compose_normal_state()

    def _compose_error_state(self):
        """Compose error state display."""
        with Vertical():
            yield Label("⚠️ Error Boundary", classes="error-header")
            yield Static(self.error_message, classes="error-message")

            with Horizontal(classes="recovery-options"):
                if self.recovery_attempts < self.max_recovery_attempts:
                    yield Button("Retry", id="retry_button", variant="primary", classes="recovery-button")
                    yield Button("Reset", id="reset_button", variant="warning", classes="recovery-button")

                yield Button("Details", id="details_button", variant="default", classes="recovery-button")

    def _compose_recovering_state(self):
        """Compose recovery state display."""
        with Vertical():
            yield Label("🔄 Recovering...", classes="error-header")
            yield Static("Attempting to restore functionality...", classes="error-message")

    def _compose_normal_state(self):
        """Compose normal state with child widget."""
        if self.child_widget:
            yield self.child_widget
        else:
            yield Static("No content loaded")

    @on(Button.Pressed, "#retry_button")
    def handle_retry(self, event: Button.Pressed):
        """Handle retry button press."""
        self._attempt_recovery()

    @on(Button.Pressed, "#reset_button")
    def handle_reset(self, event: Button.Pressed):
        """Handle reset button press."""
        self._reset_to_safe_state()

    @on(Button.Pressed, "#details_button")
    def handle_show_details(self, event: Button.Pressed):
        """Handle show details button press."""
        self._show_error_details()

    def safe_operation(self, operation: Callable, operation_name: str = "operation"):
        """Execute an operation with error handling."""
        if self.has_error and not self.is_recovering:
            return None

        try:
            result = operation()
            # Operation succeeded, clear any previous errors
            if self.has_error:
                self._clear_error_state()
            return result
        except Exception as e:
            self._handle_operation_error(e, operation_name)
            return None

    def _handle_operation_error(self, exception: Exception, operation_name: str):
        """Handle an error from a child operation."""
        # Create TUI error
        context = {
            'widget': type(self.child_widget).__name__ if self.child_widget else 'Unknown',
            'operation': operation_name,
            'error_boundary': type(self).__name__
        }

        self.last_error = self._error_handler.handle_error(
            exception,
            context=context,
            notify_user=False  # We handle user notification
        )

        self.error_timestamp = datetime.now()
        self.has_error = True
        self.error_message = self.last_error.user_message

        # Add error class for styling
        self.add_class("error")

        # Refresh display
        self.refresh()

    def _attempt_recovery(self):
        """Attempt to recover from error state."""
        if not self.last_error or self.recovery_attempts >= self.max_recovery_attempts:
            return

        self.recovery_attempts += 1
        self.is_recovering = True
        self.remove_class("error")
        self.add_class("recovering")

        # Try to reinitialize child widget
        try:
            if self.child_widget and hasattr(self.child_widget, 'reset_error_state'):
                self.child_widget.reset_error_state()

            # Simulate recovery time
            import asyncio
            asyncio.create_task(self._complete_recovery())

        except Exception as e:
            self._handle_recovery_error(e)

    async def _complete_recovery(self):
        """Complete the recovery process."""
        import asyncio
        await asyncio.sleep(1)  # Simulate recovery time

        # Recovery successful
        self.is_recovering = False
        self._clear_error_state()
        self.refresh()

    def _handle_recovery_error(self, exception: Exception):
        """Handle error during recovery."""
        self.is_recovering = False
        self.has_error = True
        self.error_message = f"Recovery failed: {exception}"
        self.add_class("error")
        self.refresh()

    def _reset_to_safe_state(self):
        """Reset to a safe, minimal state."""
        self._clear_error_state()

        # Create a safe placeholder widget
        self.child_widget = Static("Component temporarily unavailable. Please restart the application.")
        self.refresh()

    def _clear_error_state(self):
        """Clear error state."""
        self.has_error = False
        self.is_recovering = False
        self.error_message = ""
        self.recovery_attempts = 0
        self.remove_class("error")
        self.remove_class("recovering")

    def _show_error_details(self):
        """Show detailed error information."""
        if not self.last_error:
            return

        # Create detailed error message
        details = f"""
Error ID: {self.last_error.error_id}
Category: {self.last_error.category.name}
Severity: {self.last_error.severity.name}
Time: {self.last_error.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

Message: {self.last_error.message}

Context: {self.last_error.context}
        """.strip()

        # In a real implementation, this might open a dialog or log the details
        self.notify(f"Error Details:\n{details}", timeout=10)

    def mount_child(self, child: Widget):
        """Mount a child widget with error boundary protection."""
        self.child_widget = child
        self.refresh()

    def get_error_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the current error state."""
        if not self.has_error or not self.last_error:
            return None

        return {
            "error_id": self.last_error.error_id,
            "message": self.last_error.message,
            "category": self.last_error.category.name,
            "severity": self.last_error.severity.name,
            "timestamp": self.last_error.timestamp.isoformat(),
            "recovery_attempts": self.recovery_attempts
        }


class ErrorNotificationWidget(Static):
    """
    Widget for displaying error notifications to users.

    This widget can show temporary error messages and provide
    options for user actions.
    """

    CSS = """
    ErrorNotificationWidget {
        width: 100%;
        height: auto;
        border: solid $error;
        background: $error-lighten-3;
        padding: 1;
        margin: 0 0 1 0;
        display: none;
    }

    ErrorNotificationWidget.visible {
        display: block;
    }

    .notification-header {
        text-style: bold;
        color: $error;
        margin: 0 0 1 0;
    }

    .notification-message {
        color: $text;
        margin: 0 0 1 0;
    }

    .notification-actions {
        margin: 1 0 0 0;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_message = ""
        self.current_severity = ErrorSeverity.MEDIUM

    def show_error(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM, duration: float = 5.0):
        """Show an error notification."""
        self.current_message = message
        self.current_severity = severity

        # Update display
        self.update(self._format_message())
        self.add_class("visible")

        # Auto-hide after duration
        import asyncio
        asyncio.create_task(self._hide_after(duration))

    def hide(self):
        """Hide the notification."""
        self.remove_class("visible")
        self.current_message = ""

    async def _hide_after(self, duration: float):
        """Hide notification after specified duration."""
        import asyncio
        await asyncio.sleep(duration)
        self.hide()

    def _format_message(self) -> str:
        """Format the error message for display."""
        severity_icon = {
            ErrorSeverity.LOW: "ℹ️",
            ErrorSeverity.MEDIUM: "⚠️",
            ErrorSeverity.HIGH: "🚨",
            ErrorSeverity.CRITICAL: "💥"
        }

        icon = severity_icon.get(self.current_severity, "⚠️")

        return f"""[bold]{icon} Error Notification[/bold]

{self.current_message}

[dim]This notification will auto-hide in a few seconds.[/dim]"""


# Error boundary decorator for functions
def with_error_boundary(
    category: str = "Unknown",
    notify_user: bool = True,
    fallback_return: Any = None
):
    """
    Decorator to add error boundary to functions.

    Args:
        category: Error category
        notify_user: Whether to notify user of errors
        fallback_return: Value to return on error

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handler = get_error_handler()

                context = {
                    'function': func.__name__,
                    'category': category,
                    'args_count': len(args),
                    'kwargs_count': len(kwargs)
                }

                handler.handle_error(e, context, notify_user)
                return fallback_return

        return wrapper
    return decorator


# Utility function to create error boundary for any widget
def create_error_boundary(child_widget: Widget, name: str = "Component") -> ErrorBoundaryWidget:
    """
    Create an error boundary wrapper for a widget.

    Args:
        child_widget: Widget to wrap
        name: Name for the error boundary

    Returns:
        ErrorBoundaryWidget instance
    """
    boundary = ErrorBoundaryWidget(child_widget=child_widget)
    boundary.border_title = f"Error Boundary: {name}"
    return boundary


# Integration with existing error handler
def setup_error_notification_integration(notification_widget: ErrorNotificationWidget):
    """
    Setup integration between error handler and notification widget.

    Args:
        notification_widget: Widget to receive error notifications
    """
    handler = get_error_handler()

    def notify_user(message: str, severity: ErrorSeverity):
        notification_widget.show_error(message, severity)

    handler.set_notification_callback(notify_user)
