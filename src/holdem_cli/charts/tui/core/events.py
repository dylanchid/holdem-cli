"""
Event system for TUI components.

This module provides a comprehensive event system for component communication
in the TUI application, enabling loose coupling and reactive updates.
"""

from typing import Any, Dict, List, Optional, Callable, Union, Awaitable
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime
import asyncio
from weakref import WeakSet


class EventPriority(Enum):
    """Event processing priority levels."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class EventType(Enum):
    """Core event types for the TUI system."""
    # Chart events
    CHART_LOADED = auto()
    CHART_SAVED = auto()
    CHART_MODIFIED = auto()
    CHART_DELETED = auto()

    # UI interaction events
    HAND_SELECTED = auto()
    HAND_HOVERED = auto()
    MATRIX_NAVIGATED = auto()
    VIEW_MODE_CHANGED = auto()
    RANGE_BUILDER_TOGGLED = auto()
    HAND_RANGE_MODIFIED = auto()

    # Menu and dialog events
    MENU_OPENED = auto()
    DIALOG_OPENED = auto()
    DIALOG_CLOSED = auto()
    HELP_REQUESTED = auto()

    # Notification events
    NOTIFICATION_SHOWN = auto()
    NOTIFICATION_DISMISSED = auto()

    # UI state events
    LOADING_STATE_CHANGED = auto()
    PROGRESS_UPDATED = auto()
    STATUS_MESSAGE_CHANGED = auto()
    SCREEN_CHANGED = auto()

    # Search and filter events
    SEARCH_QUERY_CHANGED = auto()
    SEARCH_RESULTS_UPDATED = auto()
    FILTER_APPLIED = auto()

    # Quiz and training events
    QUIZ_STARTED = auto()
    QUIZ_COMPLETED = auto()
    QUIZ_ANSWER_SELECTED = auto()
    QUIZ_QUESTION_REQUESTED = auto()

    # Application lifecycle events
    APP_STARTED = auto()
    APP_STOPPED = auto()

    # Data and import/export events
    IMPORT_COMPLETED = auto()
    EXPORT_COMPLETED = auto()
    DATA_VALIDATED = auto()

    # Performance and caching events
    CACHE_HIT = auto()
    CACHE_MISS = auto()
    PERFORMANCE_METRIC = auto()

    # Error and logging events
    ERROR_OCCURRED = auto()
    WARNING_ISSUED = auto()
    INFO_MESSAGE = auto()


@dataclass
class Event:
    """
    Base event class.

    All events in the system should inherit from this class to ensure
    consistent structure and metadata.
    """
    type: EventType
    data: Any = None
    source: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    priority: EventPriority = EventPriority.NORMAL
    id: Optional[str] = None

    def __post_init__(self):
        if self.id is None:
            import uuid
            self.id = str(uuid.uuid4())[:8]


@dataclass
class ChartEvent(Event):
    """Chart-specific event."""
    chart_id: Optional[str] = None
    chart_name: Optional[str] = None


@dataclass
class UIEvent(Event):
    """UI interaction event."""
    widget_id: Optional[str] = None
    widget_type: Optional[str] = None
    coordinates: Optional[tuple] = None


@dataclass
class HandEvent(Event):
    """Hand-specific event."""
    hand: Optional[str] = None
    action: Optional[str] = None
    frequency: Optional[float] = None
    ev: Optional[float] = None


@dataclass
class QuizEvent(Event):
    """Quiz-specific event."""
    quiz_id: Optional[str] = None
    question_index: Optional[int] = None
    correct_answer: Optional[str] = None
    user_answer: Optional[str] = None
    score: Optional[float] = None


@dataclass
class ErrorEvent(Event):
    """Error event with exception details."""
    error_type: Optional[str] = None
    error_message: str = ""
    traceback: Optional[str] = None
    recoverable: bool = True


class EventBus:
    """
    Central event bus for the TUI application.

    This class manages event publishing, subscription, and delivery
    with support for async handlers and priority-based processing.
    """

    def __init__(self):
        self._subscribers: Dict[EventType, List[EventHandler]] = {}
        self._async_subscribers: Dict[EventType, List[AsyncEventHandler]] = {}
        self._global_subscribers: List[EventHandler] = []
        self._async_global_subscribers: List[AsyncEventHandler] = []
        self._event_history: List[Event] = []
        self._max_history = 1000
        self._lock = asyncio.Lock()
        self._running = False
        self._event_queue: asyncio.Queue = asyncio.Queue()

    async def start(self):
        """Start the event bus processing loop."""
        if self._running:
            return

        self._running = True
        asyncio.create_task(self._process_events())

    async def stop(self):
        """Stop the event bus processing loop."""
        self._running = False
        # Process remaining events
        while not self._event_queue.empty():
            await self._process_event(await self._event_queue.get())

    async def _process_events(self):
        """Main event processing loop."""
        while self._running:
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=0.1)
                await self._process_event(event)
                self._event_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Error processing events: {e}")

    async def _process_event(self, event: Event):
        """Process a single event."""
        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

        # Process event with appropriate handlers
        await self._deliver_event(event)

    async def _deliver_event(self, event: Event):
        """Deliver event to all relevant subscribers."""
        # Get specific subscribers for this event type
        specific_handlers = self._subscribers.get(event.type, [])
        specific_async_handlers = self._async_subscribers.get(event.type, [])

        # Combine all handlers
        all_handlers = specific_handlers + self._global_subscribers
        all_async_handlers = specific_async_handlers + self._async_global_subscribers

        # Deliver to sync handlers
        for handler in all_handlers:
            try:
                handler(event)
            except Exception as e:
                print(f"Error in event handler: {e}")

        # Deliver to async handlers
        for handler in all_async_handlers:
            try:
                await handler(event)
            except Exception as e:
                print(f"Error in async event handler: {e}")

    def subscribe(
        self,
        event_type: EventType,
        handler: Callable[[Event], Any],
        priority: EventPriority = EventPriority.NORMAL
    ):
        """
        Subscribe to events of a specific type.

        Args:
            event_type: Type of event to subscribe to
            handler: Event handler function
            priority: Handler priority (currently not used, reserved for future)

        Returns:
            Unsubscribe function
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        self._subscribers[event_type].append(handler)

        # Return unsubscribe function
        def unsubscribe():
            if event_type in self._subscribers and handler in self._subscribers[event_type]:
                self._subscribers[event_type].remove(handler)

        return unsubscribe

    def subscribe_async(
        self,
        event_type: EventType,
        handler: Callable[[Event], Awaitable[Any]],
        priority: EventPriority = EventPriority.NORMAL
    ):
        """
        Subscribe to events with async handler.

        Args:
            event_type: Type of event to subscribe to
            handler: Async event handler function
            priority: Handler priority

        Returns:
            Unsubscribe function
        """
        if event_type not in self._async_subscribers:
            self._async_subscribers[event_type] = []

        self._async_subscribers[event_type].append(handler)

        # Return unsubscribe function
        def unsubscribe():
            if event_type in self._async_subscribers and handler in self._async_subscribers[event_type]:
                self._async_subscribers[event_type].remove(handler)

        return unsubscribe

    def subscribe_all(self, handler: Callable[[Event], Any]):
        """
        Subscribe to all events.

        Args:
            handler: Event handler function

        Returns:
            Unsubscribe function
        """
        self._global_subscribers.append(handler)

        def unsubscribe():
            if handler in self._global_subscribers:
                self._global_subscribers.remove(handler)

        return unsubscribe

    def subscribe_all_async(self, handler: Callable[[Event], Awaitable[Any]]):
        """
        Subscribe to all events with async handler.

        Args:
            handler: Async event handler function

        Returns:
            Unsubscribe function
        """
        self._async_global_subscribers.append(handler)

        def unsubscribe():
            if handler in self._async_global_subscribers:
                self._async_global_subscribers.remove(handler)

        return unsubscribe

    async def publish(self, event: Event):
        """
        Publish an event to all subscribers.

        Args:
            event: Event to publish
        """
        if not self._running:
            await self.start()

        await self._event_queue.put(event)

    def publish_sync(self, event: Event):
        """
        Publish an event synchronously (for immediate processing).

        Args:
            event: Event to publish
        """
        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

        # Deliver immediately (synchronously)
        asyncio.create_task(self._deliver_event(event))

    def get_event_history(
        self,
        event_type: Optional[EventType] = None,
        limit: int = 100
    ) -> List[Event]:
        """
        Get event history.

        Args:
            event_type: Filter by event type
            limit: Maximum number of events to return

        Returns:
            List of events
        """
        if event_type is None:
            return self._event_history[-limit:]
        else:
            filtered = [e for e in self._event_history if e.type == event_type]
            return filtered[-limit:]

    def get_subscriber_count(self, event_type: Optional[EventType] = None) -> int:
        """
        Get number of subscribers for an event type.

        Args:
            event_type: Event type, or None for total subscribers

        Returns:
            Number of subscribers
        """
        if event_type is None:
            total = sum(len(handlers) for handlers in self._subscribers.values())
            total += len(self._global_subscribers)
            total += sum(len(handlers) for handlers in self._async_subscribers.values())
            total += len(self._async_global_subscribers)
            return total

        sync_count = len(self._subscribers.get(event_type, []))
        async_count = len(self._async_subscribers.get(event_type, []))
        return sync_count + async_count

    def clear_history(self):
        """Clear event history."""
        self._event_history.clear()

    def clear_subscribers(self, event_type: Optional[EventType] = None):
        """
        Clear subscribers.

        Args:
            event_type: Event type to clear, or None to clear all
        """
        if event_type is None:
            self._subscribers.clear()
            self._async_subscribers.clear()
            self._global_subscribers.clear()
            self._async_global_subscribers.clear()
        else:
            self._subscribers.pop(event_type, None)
            self._async_subscribers.pop(event_type, None)


# Type aliases for cleaner code
EventHandler = Callable[[Event], Any]
AsyncEventHandler = Callable[[Event], Awaitable[Any]]

# Global event bus instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get or create the global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def reset_event_bus():
    """Reset the global event bus instance."""
    global _event_bus
    if _event_bus:
        asyncio.create_task(_event_bus.stop())
    _event_bus = None


# Convenience functions for common events
def create_hand_selected_event(hand: str, source: str = None) -> HandEvent:
    """Create a hand selected event."""
    return HandEvent(
        type=EventType.HAND_SELECTED,
        hand=hand,
        source=source
    )


def create_view_mode_changed_event(mode: str, source: str = None) -> UIEvent:
    """Create a view mode changed event."""
    return UIEvent(
        type=EventType.VIEW_MODE_CHANGED,
        data=mode,
        source=source
    )


def create_chart_loaded_event(chart_id: str, chart_name: str, source: str = None) -> ChartEvent:
    """Create a chart loaded event."""
    return ChartEvent(
        type=EventType.CHART_LOADED,
        chart_id=chart_id,
        chart_name=chart_name,
        source=source
    )


def create_quiz_answer_event(
    user_answer: str,
    correct_answer: str,
    quiz_id: str = None,
    source: str = None
) -> QuizEvent:
    """Create a quiz answer event."""
    return QuizEvent(
        type=EventType.QUIZ_ANSWER_SELECTED,
        user_answer=user_answer,
        correct_answer=correct_answer,
        quiz_id=quiz_id,
        source=source
    )


def create_error_event(
    error_message: str,
    error_type: str = None,
    recoverable: bool = True,
    source: str = None
) -> ErrorEvent:
    """Create an error event."""
    return ErrorEvent(
        type=EventType.ERROR_OCCURRED,
        error_message=error_message,
        error_type=error_type,
        recoverable=recoverable,
        source=source
    )


# Event filtering and utility functions
def filter_events_by_type(events: List[Event], event_type: EventType) -> List[Event]:
    """Filter events by type."""
    return [e for e in events if e.type == event_type]


def filter_events_by_source(events: List[Event], source: str) -> List[Event]:
    """Filter events by source."""
    return [e for e in events if e.source == source]


def filter_events_by_time_range(
    events: List[Event],
    start_time: datetime,
    end_time: datetime
) -> List[Event]:
    """Filter events by time range."""
    return [e for e in events if start_time <= e.timestamp <= end_time]


def get_events_summary(events: List[Event]) -> Dict[str, int]:
    """Get a summary of event types in a list."""
    summary = {}
    for event in events:
        event_name = event.type.name
        summary[event_name] = summary.get(event_name, 0) + 1
    return summary
