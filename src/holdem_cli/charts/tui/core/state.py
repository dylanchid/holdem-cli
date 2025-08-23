"""
State management for the chart viewer application.

This module provides centralized state management with a clean, simple API
and integration with the event system for reactive updates.
"""

from typing import Dict, Tuple, Optional, List, Any
from dataclasses import dataclass, field
from datetime import datetime
from ..widgets.matrix import HandAction, ChartAction, create_sample_range
from ..core.events import get_event_bus, EventType, ChartEvent, UIEvent


@dataclass
class ChartState:
    """State for a single chart."""
    id: str
    name: str
    data: Dict[str, HandAction]
    view_mode: str = "range"
    selected_hand: Optional[str] = None
    selected_row: int = 0
    selected_col: int = 0
    last_modified: datetime = field(default_factory=datetime.now)
    is_dirty: bool = False

    def __hash__(self):
        return hash((self.id, self.name, self.last_modified))


class ChartViewerState:
    """
    Centralized state management for the chart viewer application.

    This class provides a clean, single source of truth for the application state
    with integration to the event system for reactive updates.
    """

    def __init__(self):
        self.charts: Dict[str, ChartState] = {}
        self.current_chart_id: str = "main"
        self.view_mode: str = "range"
        self.search_query: str = ""
        self.search_results: List[str] = []
        self.range_builder_mode: bool = False
        self.help_dialog_open: bool = False

        # Initialize with main chart
        self._initialize_main_chart()

        # Event system integration
        self._event_bus = get_event_bus()
        self._setup_event_handlers()

    def _initialize_main_chart(self):
        """Initialize the main chart."""
        main_chart = ChartState(
            id="main",
            name="Main Chart",
            data=create_sample_range()
        )
        self.charts["main"] = main_chart

    def _setup_event_handlers(self):
        """Setup event system integration."""
        # Subscribe to relevant events
        self._event_bus.subscribe(EventType.HAND_SELECTED, self._on_hand_selected)
        self._event_bus.subscribe(EventType.VIEW_MODE_CHANGED, self._on_view_mode_changed)
        self._event_bus.subscribe(EventType.CHART_LOADED, self._on_chart_loaded)

    def _on_hand_selected(self, event):
        """Handle hand selection event."""
        if hasattr(event, 'hand') and event.hand:
            self.set_selected_hand(event.hand)

    def _on_view_mode_changed(self, event):
        """Handle view mode change event."""
        if hasattr(event, 'data') and event.data:
            self.set_view_mode(event.data)

    def _on_chart_loaded(self, event):
        """Handle chart loaded event."""
        if hasattr(event, 'chart_id') and event.chart_id:
            self.switch_to_chart(event.chart_id)

    # Chart management methods
    def get_current_chart(self) -> Optional[ChartState]:
        """Get the currently active chart."""
        return self.charts.get(self.current_chart_id)

    def get_current_chart_data(self) -> Dict[str, HandAction]:
        """Get current chart data."""
        chart = self.get_current_chart()
        return chart.data if chart else {}

    def set_current_chart_data(self, chart_data: Dict[str, HandAction]) -> None:
        """Set current chart data."""
        if self.current_chart_id in self.charts:
            self.charts[self.current_chart_id].data = chart_data
            self.charts[self.current_chart_id].is_dirty = True
            self.charts[self.current_chart_id].last_modified = datetime.now()

    def add_chart(self, chart_id: str, name: str, data: Dict[str, HandAction]) -> None:
        """Add a new chart."""
        chart_state = ChartState(
            id=chart_id,
            name=name,
            data=data
        )
        self.charts[chart_id] = chart_state

        # Notify via event system
        event = ChartEvent(
            type=EventType.CHART_LOADED,
            chart_id=chart_id,
            chart_name=name
        )
        self._event_bus.publish_sync(event)

    def remove_chart(self, chart_id: str) -> bool:
        """Remove a chart."""
        if chart_id in self.charts and chart_id != "main":
            del self.charts[chart_id]
            # Switch to main if current chart was removed
            if self.current_chart_id == chart_id:
                self.current_chart_id = "main"
            return True
        return False

    def switch_to_chart(self, chart_id: str) -> bool:
        """Switch to a different chart."""
        if chart_id in self.charts:
            self.current_chart_id = chart_id
            return True
        return False

    def generate_chart_id(self) -> Tuple[str, str]:
        """Generate a new unique chart ID and name."""
        # Find next available ID
        next_id = 1
        while f"chart_{next_id}" in self.charts:
            next_id += 1

        chart_id = f"chart_{next_id}"
        chart_name = f"Chart {next_id}"
        return chart_id, chart_name

    # Navigation and selection methods
    def set_selected_hand(self, hand: str) -> None:
        """Set the selected hand."""
        if self.current_chart_id in self.charts:
            self.charts[self.current_chart_id].selected_hand = hand

    def set_selection_position(self, row: int, col: int) -> None:
        """Set the selection position."""
        if self.current_chart_id in self.charts:
            chart = self.charts[self.current_chart_id]
            chart.selected_row = row
            chart.selected_col = col

    def get_selection_info(self) -> Dict[str, Any]:
        """Get current selection information."""
        chart = self.get_current_chart()
        if not chart:
            return {}

        return {
            "chart_id": chart.id,
            "chart_name": chart.name,
            "selected_hand": chart.selected_hand,
            "selected_row": chart.selected_row,
            "selected_col": chart.selected_col,
            "view_mode": self.view_mode,
            "range_builder_mode": self.range_builder_mode
        }

    # View mode methods
    def set_view_mode(self, mode: str) -> None:
        """Set the view mode."""
        valid_modes = ["range", "frequency", "ev"]
        if mode in valid_modes:
            self.view_mode = mode

    def cycle_view_mode(self) -> str:
        """Cycle to the next view mode."""
        modes = ["range", "frequency", "ev"]
        current_index = modes.index(self.view_mode)
        next_index = (current_index + 1) % len(modes)
        next_mode = modes[next_index]
        self.set_view_mode(next_mode)
        return next_mode

    # Range builder methods
    def toggle_range_builder(self) -> None:
        """Toggle range builder mode."""
        self.range_builder_mode = not self.range_builder_mode

    # Search methods
    def set_search_query(self, query: str) -> None:
        """Set the search query."""
        self.search_query = query
        self.search_results = []

    def set_search_results(self, results: List[str]) -> None:
        """Set search results."""
        self.search_results = results

    # Help dialog methods
    def toggle_help_dialog(self) -> None:
        """Toggle help dialog visibility."""
        self.help_dialog_open = not self.help_dialog_open

    # Utility methods
    def get_chart_summary(self) -> Dict[str, Any]:
        """Get a summary of all charts."""
        return {
            "total_charts": len(self.charts),
            "current_chart": self.current_chart_id,
            "chart_names": {cid: chart.name for cid, chart in self.charts.items()},
            "view_mode": self.view_mode,
            "range_builder_mode": self.range_builder_mode,
            "search_active": bool(self.search_query)
        }

    def get_dirty_charts(self) -> List[str]:
        """Get list of charts that have unsaved changes."""
        return [cid for cid, chart in self.charts.items() if chart.is_dirty]

    def mark_chart_clean(self, chart_id: str) -> None:
        """Mark a chart as clean (no unsaved changes)."""
        if chart_id in self.charts:
            self.charts[chart_id].is_dirty = False

    def mark_chart_dirty(self, chart_id: str) -> None:
        """Mark a chart as dirty (has unsaved changes)."""
        if chart_id in self.charts:
            self.charts[chart_id].is_dirty = True

    # State persistence methods
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return {
            "current_chart_id": self.current_chart_id,
            "view_mode": self.view_mode,
            "search_query": self.search_query,
            "range_builder_mode": self.range_builder_mode,
            "help_dialog_open": self.help_dialog_open,
            "charts": {
                cid: {
                    "id": chart.id,
                    "name": chart.name,
                    "view_mode": chart.view_mode,
                    "selected_hand": chart.selected_hand,
                    "selected_row": chart.selected_row,
                    "selected_col": chart.selected_col,
                    "last_modified": chart.last_modified.isoformat(),
                    "is_dirty": chart.is_dirty
                }
                for cid, chart in self.charts.items()
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChartViewerState':
        """Create state from dictionary."""
        state = cls()

        # Restore basic state
        state.current_chart_id = data.get("current_chart_id", "main")
        state.view_mode = data.get("view_mode", "range")
        state.search_query = data.get("search_query", "")
        state.range_builder_mode = data.get("range_builder_mode", False)
        state.help_dialog_open = data.get("help_dialog_open", False)

        # Restore charts
        charts_data = data.get("charts", {})
        state.charts = {}

        for cid, chart_data in charts_data.items():
            # Note: We don't restore chart data here as it should be loaded separately
            # to avoid storing large amounts of data in state
            chart_state = ChartState(
                id=chart_data["id"],
                name=chart_data["name"],
                data={},  # Will be populated when chart is loaded
                view_mode=chart_data.get("view_mode", "range"),
                selected_hand=chart_data.get("selected_hand"),
                selected_row=chart_data.get("selected_row", 0),
                selected_col=chart_data.get("selected_col", 0),
                last_modified=datetime.fromisoformat(chart_data["last_modified"]),
                is_dirty=chart_data.get("is_dirty", False)
            )
            state.charts[cid] = chart_state

        # Ensure main chart exists
        if "main" not in state.charts:
            state._initialize_main_chart()

        return state


# Backward compatibility aliases
StateManager = ChartViewerState  # For backward compatibility