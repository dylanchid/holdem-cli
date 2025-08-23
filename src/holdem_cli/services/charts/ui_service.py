"""
UI Service for managing user interface interactions and feedback.

This module provides services for handling UI interactions, user feedback,
notifications, and screen management for the TUI application.
"""

from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
from enum import Enum

from holdem_cli.charts.tui.core.error_handler import get_error_handler, ErrorCategory, ErrorSeverity
from holdem_cli.charts.tui.core.events import get_event_bus, EventType, UIEvent


class NotificationType(Enum):
    """Types of user notifications."""
    INFO = "information"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    PROGRESS = "progress"


class DialogType(Enum):
    """Types of dialogs."""
    HELP = "help"
    CONFIRMATION = "confirmation"
    INPUT = "input"
    MESSAGE = "message"
    PROGRESS = "progress"


@dataclass
class Notification:
    """User notification data."""
    message: str
    type: NotificationType = NotificationType.INFO
    timeout: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.now)
    dismissed: bool = False

    def dismiss(self):
        """Dismiss the notification."""
        self.dismissed = True


@dataclass
class Dialog:
    """Dialog configuration."""
    type: DialogType
    title: str
    content: str
    buttons: List[str] = field(default_factory=lambda: ["OK"])
    callback: Optional[Callable] = None
    modal: bool = False
    width: Optional[int] = None
    height: Optional[int] = None


class UIState:
    """State of the UI system."""

    def __init__(self):
        self.notifications: List[Notification] = []
        self.active_dialog: Optional[Dialog] = None
        self.loading: bool = False
        self.loading_message: str = ""
        self.status_message: str = ""
        self.progress: float = 0.0
        self.screen_stack: List[str] = []
        self.current_screen: str = "main"

    def add_notification(self, notification: Notification):
        """Add a notification."""
        self.notifications.append(notification)
        # Keep only last 10 notifications
        if len(self.notifications) > 10:
            self.notifications = self.notifications[-10:]

    def dismiss_notification(self, index: int):
        """Dismiss a notification by index."""
        if 0 <= index < len(self.notifications):
            self.notifications[index].dismiss()

    def clear_dismissed_notifications(self):
        """Remove dismissed notifications."""
        self.notifications = [n for n in self.notifications if not n.dismissed]

    def set_loading(self, loading: bool, message: str = ""):
        """Set loading state."""
        self.loading = loading
        self.loading_message = message

    def set_progress(self, progress: float, message: str = ""):
        """Set progress state."""
        self.progress = max(0.0, min(1.0, progress))
        if message:
            self.status_message = message


class UIService:
    """
    Service for managing user interface interactions and feedback.

    This service provides:
    - User notification management
    - Dialog management
    - Loading and progress indicators
    - Screen navigation and history
    - User feedback mechanisms
    - Accessibility features
    """

    def __init__(self):
        self.error_handler = get_error_handler()
        self.event_bus = get_event_bus()
        self.state = UIState()
        self._ui_handlers: Dict[str, Callable] = {}
        self._notification_handlers: Dict[NotificationType, Callable] = {}
        self._cleanup_task: Optional[asyncio.Task] = None

    def notify(self, message: str, type: NotificationType = NotificationType.INFO,
               timeout: Optional[float] = None) -> Notification:
        """
        Show a notification to the user.

        Args:
            message: Notification message
            type: Type of notification
            timeout: Auto-dismiss timeout in seconds

        Returns:
            Notification object
        """
        notification = Notification(
            message=message,
            type=type,
            timeout=timeout
        )

        self.state.add_notification(notification)

        # Emit event
        event = UIEvent(
            type=EventType.NOTIFICATION_SHOWN,
            data={
                'notification': notification,
                'type': type.value,
                'message': message
            }
        )
        self.event_bus.publish_sync(event)

        # Call type-specific handler
        if type in self._notification_handlers:
            try:
                self._notification_handlers[type](notification)
            except Exception as e:
                self.error_handler.handle_error(
                    e,
                    context={'operation': 'notification_handler', 'type': type.value},
                    category=ErrorCategory.UI_INTERACTION,
                    severity=ErrorSeverity.LOW
                )

        return notification

    def show_success(self, message: str, timeout: float = 3.0) -> Notification:
        """Show a success notification."""
        return self.notify(message, NotificationType.SUCCESS, timeout)

    def show_warning(self, message: str, timeout: float = 5.0) -> Notification:
        """Show a warning notification."""
        return self.notify(message, NotificationType.WARNING, timeout)

    def show_error(self, message: str, timeout: Optional[float] = None) -> Notification:
        """Show an error notification."""
        return self.notify(message, NotificationType.ERROR, timeout)

    def show_progress(self, message: str, progress: float) -> Notification:
        """Show a progress notification."""
        notification = self.notify(
            f"{message} ({progress:.1%})",
            NotificationType.PROGRESS
        )
        self.state.set_progress(progress, message)
        return notification

    def show_dialog(self, dialog: Dialog):
        """
        Show a dialog to the user.

        Args:
            dialog: Dialog configuration
        """
        self.state.active_dialog = dialog

        # Emit event
        event = UIEvent(
            type=EventType.DIALOG_SHOWN,
            data={'dialog': dialog}
        )
        self.event_bus.publish_sync(event)

    def show_confirmation_dialog(self, title: str, message: str,
                                on_confirm: Callable, on_cancel: Optional[Callable] = None):
        """
        Show a confirmation dialog.

        Args:
            title: Dialog title
            message: Confirmation message
            on_confirm: Callback for confirmation
            on_cancel: Callback for cancellation
        """
        def callback(button: str):
            if button == "Yes" and on_confirm:
                on_confirm()
            elif button == "No" and on_cancel:
                on_cancel()

        dialog = Dialog(
            type=DialogType.CONFIRMATION,
            title=title,
            content=message,
            buttons=["Yes", "No"],
            callback=callback
        )
        self.show_dialog(dialog)

    def show_help_dialog(self, content: Optional[str] = None):
        """Show the help dialog."""
        help_content = content or self._get_default_help_content()

        dialog = Dialog(
            type=DialogType.HELP,
            title="Help - Holdem CLI",
            content=help_content,
            modal=False,
            width=80,
            height=25
        )
        self.show_dialog(dialog)

    def _get_default_help_content(self) -> str:
        """Get default help content."""
        return """
[bold]🎯 Holdem CLI Chart Viewer Help[/bold]

[bold]Navigation:[/bold]
  [accent]↑↓←→ / WASD[/accent]      Navigate matrix
  [accent]Enter / Space[/accent]     Select hand & show details
  [accent]Tab / Shift+Tab[/accent]   Cycle between panels
  [accent]Escape[/accent]            Clear selection

[bold]View Controls:[/bold]
  [accent]F[/accent]                 Toggle frequency view
  [accent]V[/accent]                 Toggle EV view
  [accent]M[/accent]                 Cycle through view modes
  [accent]/[/accent]                 Search hands
  [accent]N[/accent]                 Next search result

[bold]Range Builder:[/bold]
  [accent]B[/accent]                 Toggle range builder mode
  [accent]A[/accent]                 Add hand to custom range
  [accent]D[/accent]                 Remove hand from custom range
  [accent]C[/accent]                 Clear custom range

[bold]Chart Operations:[/bold]
  [accent]Ctrl+L[/accent]            Load chart
  [accent]Ctrl+S[/accent]            Save chart
  [accent]Ctrl+E[/accent]            Export chart

[bold]General:[/bold]
  [accent]H[/accent]                 Show/hide this help
  [accent]Q[/accent]                 Quit application

[dim]Press H or Escape to close this help dialog[/dim]
"""

    def set_loading(self, loading: bool, message: str = "Loading..."):
        """
        Set loading state.

        Args:
            loading: Whether loading is active
            message: Loading message
        """
        self.state.set_loading(loading, message)

        # Emit event
        event = UIEvent(
            type=EventType.LOADING_STATE_CHANGED,
            data={'loading': loading, 'message': message}
        )
        self.event_bus.publish_sync(event)

    def update_progress(self, progress: float, message: str = ""):
        """
        Update progress indicator.

        Args:
            progress: Progress value (0.0 to 1.0)
            message: Progress message
        """
        self.state.set_progress(progress, message)

        # Emit event
        event = UIEvent(
            type=EventType.PROGRESS_UPDATED,
            data={'progress': progress, 'message': message}
        )
        self.event_bus.publish_sync(event)

    def set_status_message(self, message: str):
        """
        Set status message.

        Args:
            message: Status message
        """
        self.state.status_message = message

        # Emit event
        event = UIEvent(
            type=EventType.STATUS_MESSAGE_CHANGED,
            data={'message': message}
        )
        self.event_bus.publish_sync(event)

    def push_screen(self, screen_name: str):
        """
        Push a screen to the navigation stack.

        Args:
            screen_name: Name of the screen
        """
        self.state.screen_stack.append(self.state.current_screen)
        self.state.current_screen = screen_name

        # Emit event
        event = UIEvent(
            type=EventType.SCREEN_CHANGED,
            data={'screen': screen_name, 'pushed': True}
        )
        self.event_bus.publish_sync(event)

    def pop_screen(self) -> Optional[str]:
        """
        Pop a screen from the navigation stack.

        Returns:
            Name of the previous screen, or None if stack is empty
        """
        if not self.state.screen_stack:
            return None

        previous_screen = self.state.screen_stack.pop()
        self.state.current_screen = previous_screen

        # Emit event
        event = UIEvent(
            type=EventType.SCREEN_CHANGED,
            data={'screen': previous_screen, 'popped': True}
        )
        self.event_bus.publish_sync(event)

        return previous_screen

    def switch_to_screen(self, screen_name: str):
        """
        Switch to a specific screen.

        Args:
            screen_name: Name of the screen
        """
        self.state.current_screen = screen_name

        # Emit event
        event = UIEvent(
            type=EventType.SCREEN_CHANGED,
            data={'screen': screen_name, 'switched': True}
        )
        self.event_bus.publish_sync(event)

    def register_ui_handler(self, name: str, handler: Callable):
        """
        Register a UI event handler.

        Args:
            name: Handler name
            handler: Handler function
        """
        self._ui_handlers[name] = handler

    def register_notification_handler(self, type: NotificationType, handler: Callable):
        """
        Register a notification handler for a specific type.

        Args:
            type: Notification type
            handler: Handler function
        """
        self._notification_handlers[type] = handler

    def get_ui_handler(self, name: str) -> Optional[Callable]:
        """
        Get a UI handler by name.

        Args:
            name: Handler name

        Returns:
            Handler function or None
        """
        return self._ui_handlers.get(name)

    def dismiss_dialog(self):
        """Dismiss the active dialog."""
        if self.state.active_dialog:
            self.state.active_dialog = None

            # Emit event
            event = UIEvent(
                type=EventType.DIALOG_DISMISSED,
                data={}
            )
            self.event_bus.publish_sync(event)

    def dismiss_notification(self, index: int):
        """
        Dismiss a notification by index.

        Args:
            index: Notification index
        """
        self.state.dismiss_notification(index)

    def clear_all_notifications(self):
        """Clear all notifications."""
        self.state.notifications.clear()

    def get_active_notifications(self) -> List[Notification]:
        """Get list of active (non-dismissed) notifications."""
        return [n for n in self.state.notifications if not n.dismissed]

    def get_ui_state(self) -> Dict[str, Any]:
        """Get current UI state."""
        return {
            'current_screen': self.state.current_screen,
            'screen_stack': self.state.screen_stack.copy(),
            'loading': self.state.loading,
            'loading_message': self.state.loading_message,
            'status_message': self.state.status_message,
            'progress': self.state.progress,
            'active_dialog': self.state.active_dialog,
            'notification_count': len(self.get_active_notifications()),
            'registered_handlers': len(self._ui_handlers)
        }

    def start_auto_cleanup(self, interval: float = 30.0):
        """
        Start automatic cleanup of dismissed notifications and old state.

        Args:
            interval: Cleanup interval in seconds
        """
        async def cleanup():
            while True:
                await asyncio.sleep(interval)
                try:
                    self.state.clear_dismissed_notifications()
                except Exception as e:
                    self.error_handler.handle_error(
                        e,
                        context={'operation': 'auto_cleanup'},
                        category=ErrorCategory.UI_INTERACTION,
                        severity=ErrorSeverity.LOW
                    )

        self._cleanup_task = asyncio.create_task(cleanup())

    def stop_auto_cleanup(self):
        """Stop automatic cleanup."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            self._cleanup_task = None

    def create_feedback_message(self, action: str, success: bool,
                              details: Optional[str] = None) -> str:
        """
        Create a user-friendly feedback message.

        Args:
            action: Action that was performed
            success: Whether the action was successful
            details: Additional details

        Returns:
            Formatted feedback message
        """
        emoji = "✅" if success else "❌"
        status = "succeeded" if success else "failed"

        message = f"{emoji} {action} {status}"

        if details:
            message += f": {details}"

        return message

    def handle_error_feedback(self, error: Exception, operation: str,
                            user_message: Optional[str] = None) -> str:
        """
        Handle error feedback to user.

        Args:
            error: Exception that occurred
            operation: Operation that failed
            user_message: Custom user message

        Returns:
            User-friendly error message
        """
        if user_message:
            return f"❌ {user_message}"

        # Generate user-friendly message based on error type
        error_type = type(error).__name__

        if "PermissionError" in error_type:
            return f"❌ Permission denied: {operation}"
        elif "FileNotFoundError" in error_type:
            return f"❌ File not found: {operation}"
        elif "ValueError" in error_type:
            return f"❌ Invalid input: {operation}"
        else:
            return f"❌ {operation} failed: {str(error)}"


# Global service instance
_ui_service: Optional[UIService] = None


def get_ui_service() -> UIService:
    """Get or create the global UI service instance."""
    global _ui_service
    if _ui_service is None:
        _ui_service = UIService()
    return _ui_service


def reset_ui_service():
    """Reset the global UI service instance."""
    global _ui_service
    if _ui_service:
        _ui_service.stop_auto_cleanup()
    _ui_service = None
