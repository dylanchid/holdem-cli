"""
Main screen for the TUI chart viewer application.

This screen provides the primary interface for viewing and interacting
with poker charts, including the matrix display, controls, and navigation.
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, Label
from textual.screen import Screen
from textual.reactive import reactive
from textual import events
from textual.message import Message

from ..widgets import HandMatrixWidget, HandDetailsWidget, ChartControlsWidget, HelpDialog
from ..widgets.matrix import create_sample_range
from ..core.state import ChartViewerState
from ..core.events import get_event_bus, EventType
from typing import Dict, Optional


class MainScreen(Screen):
    """
    Main screen for chart viewing and editing.

    This screen provides the primary interface for:
    - Viewing poker hand matrices
    - Interacting with chart controls
    - Navigation between different chart views
    - Real-time chart updates
    """

    CSS = """
    MainScreen {
        layout: vertical;
    }

    .main-container {
        layout: horizontal;
        height: 100%;
        padding: 0 1;
        margin: 0;
    }

    .chart-panel {
        width: 3fr;
        height: 100%;
        padding: 0 1;
        margin: 0;
    }

    .side-panel {
        width: 1fr;
        height: 100%;
        layout: vertical;
        padding: 0 1;
        margin: 0;
    }

    .details-section {
        height: 10;
        border: solid $primary;
        background: $surface;
        padding: 1;
        margin: 1 0;
    }

    .controls-section {
        height: 8;
        border: solid $primary;
        background: $surface;
        padding: 1;
        margin: 1 0;
    }

    .section-title {
        text-style: bold;
        color: $primary;
        margin: 0 0 1 0;
    }
    """

    # Reactive state
    current_chart_id: reactive[str] = reactive("main")
    view_mode: reactive[str] = reactive("range")
    range_builder_mode: reactive[bool] = reactive(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state = ChartViewerState()
        self.event_bus = get_event_bus()
        self._setup_event_handlers()

    def _setup_event_handlers(self):
        """Setup event handlers for reactive updates."""
        self.event_bus.subscribe(EventType.HAND_SELECTED, self._on_hand_selected)
        self.event_bus.subscribe(EventType.VIEW_MODE_CHANGED, self._on_view_mode_changed)
        self.event_bus.subscribe(EventType.CHART_LOADED, self._on_chart_loaded)

    def _on_hand_selected(self, event):
        """Handle hand selection events."""
        if hasattr(self, '_hand_details_widget') and hasattr(event, 'hand'):
            action = self.state.get_current_chart_data().get(event.hand)
            self._hand_details_widget.update_hand(event.hand, action)

    def _on_view_mode_changed(self, event):
        """Handle view mode change events."""
        if hasattr(self, '_matrix_widget') and hasattr(event, 'data'):
            self._matrix_widget.set_view_mode(event.data)
            self.view_mode = event.data

    def _on_chart_loaded(self, event):
        """Handle chart loaded events."""
        if hasattr(self, '_matrix_widget') and hasattr(event, 'chart_id'):
            chart = self.state.get_current_chart()
            if chart:
                self._matrix_widget.update_actions(chart.data)
                self.current_chart_id = event.chart_id

    def compose(self) -> ComposeResult:
        """Compose the main screen layout."""
        yield Header()

        with Container(classes="main-container"):
            # Main chart panel
            with Vertical(classes="chart-panel"):
                yield Label("📊 Poker Chart Viewer", classes="section-title")
                self._matrix_widget = HandMatrixWidget(
                    self.state.get_current_chart_data(),
                    self.state.get_current_chart().name if self.state.get_current_chart() else "Chart",
                    id="matrix"
                )
                yield self._matrix_widget

            # Side panel with details and controls
            with Vertical(classes="side-panel"):
                # Hand details section
                with Vertical(classes="details-section"):
                    yield Label("🃏 Hand Details", classes="section-title")
                    self._hand_details_widget = HandDetailsWidget(id="hand_details")
                    yield self._hand_details_widget

                # Controls section
                with Vertical(classes="controls-section"):
                    yield Label("🎮 Controls", classes="section-title")
                    self._controls_widget = ChartControlsWidget(id="controls")
                    yield self._controls_widget

        # Help dialog (hidden by default)
        self._help_dialog = HelpDialog(id="help_dialog", classes="help-dialog")
        yield self._help_dialog

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the screen when mounted."""
        self.title = "Holdem CLI - Chart Viewer"
        self.sub_title = "Interactive Poker Chart Analysis"

        # Focus the matrix widget initially
        if hasattr(self, '_matrix_widget'):
            self._matrix_widget.focus()

        # Set initial state
        self._update_controls_state()

    def _update_controls_state(self):
        """Update controls widget with current state."""
        if hasattr(self, '_controls_widget'):
            self._controls_widget.update_state(
                view_mode=self.view_mode,
                range_builder=self.range_builder_mode
            )

    def action_toggle_help(self) -> None:
        """Toggle help dialog visibility."""
        if hasattr(self, '_help_dialog'):
            self._help_dialog.toggle()

    def action_new_chart(self) -> None:
        """Create a new chart."""
        chart_id, chart_name = self.state.generate_chart_id()
        sample_data = create_sample_range()
        self.state.add_chart(chart_id, chart_name, sample_data)

        # Switch to the new chart
        self.state.switch_to_chart(chart_id)
        self.current_chart_id = chart_id

        # Update UI
        if hasattr(self, '_matrix_widget'):
            self._matrix_widget.update_actions(sample_data)

        self.notify(f"✅ Created new chart: {chart_name}", severity="information")

    def action_save_chart(self) -> None:
        """Save the current chart."""
        current_chart = self.state.get_current_chart()
        if current_chart:
            # Mark as clean (no unsaved changes)
            self.state.mark_chart_clean(current_chart.id)
            self.notify(f"✅ Chart saved: {current_chart.name}", severity="information")
        else:
            self.notify("⚠️ No chart to save", severity="warning")

    def action_load_chart(self) -> None:
        """Load a chart (placeholder for now)."""
        self.notify("📁 Load chart functionality coming soon", severity="information")

    def action_export_chart(self) -> None:
        """Export the current chart."""
        current_chart = self.state.get_current_chart()
        if current_chart:
            self.notify(f"📤 Export functionality for: {current_chart.name}", severity="information")
        else:
            self.notify("⚠️ No chart to export", severity="warning")

    def action_cycle_view_mode(self) -> None:
        """Cycle through view modes."""
        new_mode = self.state.cycle_view_mode()
        self.view_mode = new_mode

        if hasattr(self, '_matrix_widget'):
            self._matrix_widget.set_view_mode(new_mode)

        self.notify(f"✅ Switched to {new_mode.title()} view", severity="information")

    def action_toggle_range_builder(self) -> None:
        """Toggle range builder mode."""
        self.state.toggle_range_builder()
        self.range_builder_mode = self.state.range_builder_mode

        if hasattr(self, '_matrix_widget'):
            self._matrix_widget.toggle_range_builder()

        status = "enabled" if self.range_builder_mode else "disabled"
        self.notify(f"🔧 Range builder {status}", severity="information")

    def action_reset_view(self) -> None:
        """Reset view to default state."""
        self.state.set_view_mode("range")
        self.view_mode = "range"

        # Reset selection
        if hasattr(self, '_matrix_widget'):
            self._matrix_widget.set_view_mode("range")

        if hasattr(self, '_hand_details_widget'):
            self._hand_details_widget.clear_details()

        self.notify("🔄 View reset to default", severity="information")

    def action_search_hands(self) -> None:
        """Search for hands in the chart."""
        self.notify("🔍 Search functionality coming soon", severity="information")

    def action_show_statistics(self) -> None:
        """Show chart statistics."""
        current_chart = self.state.get_current_chart()
        if current_chart:
            summary = self.state.get_chart_summary()
            stats_text = f"""
Chart: {current_chart.name}
Total Hands: {summary['total_charts']}
Current Chart ID: {summary['current_chart']}
View Mode: {summary['view_mode']}
Range Builder: {'ON' if summary['range_builder_mode'] else 'OFF'}
            """.strip()
            self.notify(stats_text, timeout=5)
        else:
            self.notify("⚠️ No chart data available", severity="warning")

    def on_key(self, event: events.Key) -> None:
        """Handle keyboard input at screen level."""
        # Handle screen-level shortcuts that aren't handled by widgets
        if event.key == "f1":
            self.action_toggle_help()
        elif event.key == "f2":
            self.action_new_chart()
        elif event.key == "f3":
            self.action_save_chart()
        elif event.key == "f4":
            self.action_load_chart()
        elif event.key == "f5":
            self.action_export_chart()
        elif event.key == "f6":
            self.action_cycle_view_mode()
        elif event.key == "f7":
            self.action_toggle_range_builder()
        elif event.key == "f8":
            self.action_reset_view()
        elif event.key == "f9":
            self.action_search_hands()
        elif event.key == "f10":
            self.action_show_statistics()

    def get_screen_info(self) -> Dict[str, any]:
        """Get information about the current screen state."""
        return {
            "screen_type": "main",
            "current_chart_id": self.current_chart_id,
            "view_mode": self.view_mode,
            "range_builder_mode": self.range_builder_mode,
            "chart_count": len(self.state.charts),
            "dirty_charts": len(self.state.get_dirty_charts())
        }


# Screen factory function
def create_main_screen(**kwargs) -> MainScreen:
    """Create a configured main screen."""
    return MainScreen(**kwargs)
