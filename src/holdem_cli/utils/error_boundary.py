"""
Error boundary system for TUI components.

This module provides error boundary widgets and decorators that can catch
and handle errors gracefully in the Textual interface, providing better
user experience when things go wrong.
"""

from typing import Callable, Any, Optional, Dict, List
from functools import wraps
import traceback
from contextlib import contextmanager

from textual.app import App
from textual.widget import Widget
from textual.screen import Screen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Button, Label, Static, TextArea
from textual.message import Message
from textual import events

from .error_handling import (
    HoldemError, ErrorContext, get_error_handler,
    create_user_friendly_error, log_error_and_continue
)
from .logging_utils import get_logger


class ErrorBoundary:
    """Error boundary for catching and handling errors in TUI components."""

    def __init__(self, app: Optional[App] = None, show_error_dialog: bool = True):
        """Initialize error boundary."""
        self.app = app
        self.show_error_dialog = show_error_dialog
        self._logger = get_logger()
        self._error_handler = get_error_handler()
        self._error_stack: List[Exception] = []

    @contextmanager
    def catch_errors(self, operation: str = "", **context):
        """Context manager for catching errors."""
        error_context = ErrorContext(operation=operation, parameters=context)

        try:
            yield
        except Exception as e:
            self.handle_error(e, error_context)

    def handle_error(self, error: Exception, context: Optional[ErrorContext] = None) -> None:
        """Handle an error with appropriate user feedback."""
        self._error_stack.append(error)

        # Log the error
        if context:
            self._error_handler.handle_error(error, context, re_raise=False)
        else:
            log_error_and_continue(error, "error_boundary")

        # Show user-friendly error dialog if enabled
        if self.show_error_dialog and self.app:
            self.show_error_dialog_to_user(error)

    def show_error_dialog_to_user(self, error: Exception) -> None:
        """Show error dialog to user."""
        if not self.app:
            return

        # Create error dialog
        dialog = ErrorDialog(error)
        self.app.push_screen(dialog)

    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of recent errors."""
        return {
            'error_count': len(self._error_stack),
            'recent_errors': [str(e) for e in self._error_stack[-5:]],
            'last_error': str(self._error_stack[-1]) if self._error_stack else None
        }


def error_boundary(
    operation: str = "",
    show_dialog: bool = True,
    fallback: Optional[Callable] = None
):
    """Decorator for adding error boundary to functions."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Try to get app instance from args (common in Textual)
            app = None
            for arg in args:
                if isinstance(arg, App):
                    app = arg
                    break

            boundary = ErrorBoundary(app=app, show_error_dialog=show_dialog)

            with boundary.catch_errors(operation=operation, **kwargs):
                return func(*args, **kwargs)

        return wrapper

    return decorator


class ErrorDialog(Screen):
    """Error dialog screen for displaying errors to users."""

    def __init__(self, error: Exception):
        """Initialize error dialog."""
        super().__init__()
        self.error = error
        self.user_message = create_user_friendly_error(error)
        self.technical_details = traceback.format_exc()

    def compose(self):
        """Compose the error dialog."""
        with Vertical(id="error-dialog"):
            yield Label("🚨 Error Occurred", id="error-title")
            yield Static(self.user_message, id="error-message")

            with Horizontal():
                yield Button("OK", id="error-ok", variant="primary")
                yield Button("Show Details", id="error-details", variant="default")

            # Hidden details area
            yield TextArea(self.technical_details, id="error-details-area", classes="hidden")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "error-ok":
            self.dismiss()
        elif event.button.id == "error-details":
            self.toggle_details()

    def toggle_details(self) -> None:
        """Toggle technical details visibility."""
        details_area = self.query_one("#error-details-area", TextArea)
        details_button = self.query_one("#error-details", Button)
        if "hidden" in details_area.classes:
            details_area.remove_class("hidden")
            details_button.label = "Hide Details"
        else:
            details_area.add_class("hidden")
            details_button.label = "Show Details"

    def dismiss(self) -> None:
        """Dismiss the error dialog."""
        # This would typically close the screen in Textual
        pass


class ErrorStatusWidget(Widget):
    """Widget for displaying error status and recent errors."""

    def __init__(self, error_boundary: ErrorBoundary, **kwargs):
        """Initialize error status widget."""
        super().__init__(**kwargs)
        self.error_boundary = error_boundary

    def compose(self):
        """Compose the error status widget."""
        with Container(id="error-status"):
            yield Label("Error Status", id="error-status-title")
            yield Static("No recent errors", id="error-status-message")
            yield Button("Clear Errors", id="clear-errors", variant="default")

    def update_status(self) -> None:
        """Update error status display."""
        summary = self.error_boundary.get_error_summary()

        if summary['error_count'] > 0:
            message = f"Recent Errors: {summary['error_count']}"
            if summary['last_error']:
                message += f"\nLast: {summary['last_error'][:100]}..."
        else:
            message = "No recent errors"

        self.query_one("#error-status-message", Static).update(message)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "clear-errors":
            self.clear_errors()

    def clear_errors(self) -> None:
        """Clear error history."""
        # This would clear the error stack in the boundary
        self.update_status()


class RecoverableErrorWidget(Widget):
    """Widget that can display errors and offer recovery options."""

    def __init__(self, operation: str = "", **kwargs):
        """Initialize recoverable error widget."""
        super().__init__(**kwargs)
        self.operation = operation
        self.current_error: Optional[Exception] = None

    def compose(self):
        """Compose the recoverable error widget."""
        with Container(id="recoverable-error", classes="hidden"):
            yield Label("⚠️ Error", id="recoverable-error-title")
            yield Static("", id="recoverable-error-message")
            yield Button("Retry", id="retry-operation", variant="primary")
            yield Button("Skip", id="skip-operation", variant="default")

    def show_error(self, error: Exception) -> None:
        """Show error with recovery options."""
        self.current_error = error
        self.query_one("#recoverable-error-message", Static).update(
            create_user_friendly_error(error)
        )
        self.remove_class("hidden")

    def hide_error(self) -> None:
        """Hide error display."""
        self.current_error = None
        self.add_class("hidden")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "retry-operation":
            self.retry_operation()
        elif event.button.id == "skip-operation":
            self.skip_operation()

    def retry_operation(self) -> None:
        """Retry the failed operation."""
        if self.current_error:
            # Emit retry message
            self.post_message(RetryOperation(self.operation, self.current_error))
            self.hide_error()

    def skip_operation(self) -> None:
        """Skip the failed operation."""
        if self.current_error:
            self.post_message(SkipOperation(self.operation, self.current_error))
            self.hide_error()


class RetryOperation(Message):
    """Message sent when user wants to retry an operation."""

    def __init__(self, operation: str, error: Exception):
        self.operation = operation
        self.error = error
        super().__init__()


class SkipOperation(Message):
    """Message sent when user wants to skip an operation."""

    def __init__(self, operation: str, error: Exception):
        self.operation = operation
        self.error = error
        super().__init__()


def safe_tui_operation(
    operation: str = "",
    fallback_widget: Optional[Widget] = None
):
    """Decorator for safe TUI operations with error recovery."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(widget: Widget, *args, **kwargs):
            try:
                return func(widget, *args, **kwargs)
            except Exception as e:
                # Log error
                context = ErrorContext(operation=operation)
                log_error_and_continue(e, operation)

                # Try to show error in a recoverable widget
                if hasattr(widget, 'query') and fallback_widget:
                    error_displays = widget.query(fallback_widget.__class__.__name__)
                    if error_displays:
                        error_display = error_displays.first()
                        if error_display and hasattr(error_display, 'show_error'):
                            # Type check: ensure it's a RecoverableErrorWidget
                            if isinstance(error_display, RecoverableErrorWidget):
                                error_display.show_error(e)
                                return

                # Fallback: show basic error message
                if hasattr(widget, 'notify'):
                    widget.notify(
                        create_user_friendly_error(e),
                        title="Error",
                        severity="error",
                        timeout=10
                    )

        return wrapper

    return decorator


def graceful_degradation(
    operation: str = "",
    degradation_message: str = "Service temporarily unavailable"
):
    """Decorator for graceful degradation when operations fail."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Log the error
                log_error_and_continue(e, operation)

                # Return degradation message or default
                if degradation_message:
                    return degradation_message

                # For widgets, return empty container
                for arg in args:
                    if hasattr(arg, 'compose'):
                        return Container()

                return None

        return wrapper

    return decorator


# CSS for error components
ERROR_DIALOG_CSS = """
ErrorDialog {
    align: center middle;
    padding: 2;
    width: 60;
    height: 40;
    background: $surface;
    border: solid $error;
}

#error-title {
    text-style: bold;
    color: $error;
    margin-bottom: 1;
}

#error-message {
    margin-bottom: 2;
    color: $text;
}

#error-details-area {
    height: 15;
    margin-top: 1;
}

#error-details-area.hidden {
    display: none;
}

ErrorStatusWidget {
    dock: bottom;
    height: 4;
    background: $background;
    border-top: solid $primary;
}

#clear-errors {
    dock: bottom;
    width: 20;
}

RecoverableErrorWidget {
    width: 100%;
    background: $warning;
    border: solid $warning;
    padding: 1;
    margin: 1 0;
}

#recoverable-error-title {
    color: $text;
    text-style: bold;
}

#retry-operation {
    margin-right: 1;
}
"""

# Initialize global error boundary
_global_error_boundary = ErrorBoundary()


def get_global_error_boundary() -> ErrorBoundary:
    """Get the global error boundary instance."""
    return _global_error_boundary
