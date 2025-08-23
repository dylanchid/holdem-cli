"""
Refactored Chart Viewer Application.

This module contains the refactored ChartViewerApp that uses the new service-based
architecture for better separation of concerns and maintainability.
"""

import asyncio
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, DataTable, Button, Input, Select, Label, Collapsible, Pretty, TextArea, TabbedContent, TabPane
from textual.binding import Binding, BindingType
from typing import List, Sequence, Generator, Any
from textual.coordinate import Coordinate
from textual.message import Message
from textual.reactive import reactive
from textual import events

from typing import Dict, List, Optional, Tuple, Any, Callable
import json
from pathlib import Path
from datetime import datetime
import random
from functools import wraps

from .constants import MAIN_CSS, ALL_BINDINGS, DEFAULT_CHART_NAME, DEFAULT_VIEW_MODE, VIEW_MODES
from .tui.core.error_handler import get_error_handler, handle_errors, ErrorCategory, ErrorSeverity
from .messages import HandSelected, LoadChartRequested, SaveChartRequested, CompareChartsRequested, ExportChartRequested, ViewModeChanged, SearchQueryEntered, RangeBuilderToggled, HandRangeModified, ChartDataUpdated, QuizAnswerSelected, QuizQuestionRequested
from .tui.widgets import HelpDialog, HandMatrixWidget, HandDetailsWidget, ChartControlsWidget
from .tui.widgets.matrix import HandMatrix, HandAction, ChartAction, create_sample_range
from .tui.core.state import ChartViewerState
from holdem_cli.storage import Database, init_database

# Import new services
# from holdem_cli.services.charts.chart_service import get_chart_service, ChartService
# from holdem_cli.services.charts.navigation_service import get_navigation_service, NavigationService, Direction
# from holdem_cli.services.charts.ui_service import get_ui_service, UIService, NotificationType


class ChartViewerApp(App):
    """
    Refactored main chart viewer application using service-based architecture.

    This version separates concerns into focused services:
    - ChartService: Chart business logic and data operations
    - NavigationService: Navigation and user interaction logic
    - UIService: UI feedback and user notifications
    """

    CSS = MAIN_CSS
    BINDINGS: Sequence[BindingType] = ALL_BINDINGS

    def __init__(self, chart_name: str = DEFAULT_CHART_NAME, **kwargs):
        super().__init__(**kwargs)
        self.chart_name = chart_name

        # Initialize services
        self.chart_service = get_chart_service()
        self.navigation_service = get_navigation_service()
        self.ui_service = get_ui_service()

        # Initialize state
        self.state = ChartViewerState()
        self.db = init_database()
        self.error_handler = get_error_handler()

        # Setup error notification callback
        self.error_handler.set_notification_callback(self._show_error_notification)

        # Performance tracking
        self._stats_cache = {}
        self._last_chart_hash = None

        # Initialize with main chart
        try:
            self.state.add_chart("main", chart_name, create_sample_range())
        except Exception as e:
            self.error_handler.handle_error(
                e,
                context={'operation': 'chart_initialization', 'chart_name': chart_name},
                notify_user=True
            )

    @property
    def charts(self):
        """Backward compatibility property for charts."""
        return self.state.charts

    @property
    def current_chart(self):
        """Backward compatibility property for current_chart."""
        return self.state.get_current_chart_data()

    @property
    def current_view_mode(self):
        """Backward compatibility property for current_view_mode."""
        return self.state.view_mode

    def _get_chart_hash(self) -> str:
        """Get a hash of the current chart for caching purposes."""
        import hashlib
        chart_str = str(sorted(self.current_chart.items()))
        return hashlib.md5(chart_str.encode()).hexdigest()

    def _clear_cache(self) -> None:
        """Clear all caches when chart data changes."""
        self._stats_cache.clear()
        self._last_chart_hash = None

    def compose(self) -> ComposeResult:
        """Create the application layout with tabs."""
        yield Header()

        # Main tabbed interface
        with TabbedContent(id="chart_tabs", initial="tab_main"):
            # Main chart tab
            with TabPane("📊 Main Chart", id="tab_main"):
                with Container(classes="container"):
                    # Main panel with chart matrix
                    with Vertical(classes="main-panel"):
                        yield HandMatrixWidget(
                            self.current_chart,
                            self.chart_name,
                            id="matrix"
                        )

                    # Side panel with organized sections
                    with Vertical(classes="side-panel"):
                        # Hand details section
                        with Vertical(classes="details-section"):
                            yield Label("🃏 Hand Details", classes="section-title")
                            yield HandDetailsWidget(id="hand_details")

                        # Controls section
                        with Vertical(classes="controls-section"):
                            yield Label("🎮 Controls", classes="section-title")
                            yield ChartControlsWidget(id="controls")

            # Statistics tab
            with TabPane("📈 Statistics", id="tab_stats"):
                with Container(classes="container"):
                    with Vertical(classes="main-panel"):
                        yield Label("📊 Chart Statistics", classes="section-title")
                        stats_content = self._get_statistics_content()
                        yield Static(stats_content, classes="stats-content")

            # Notes tab
            with TabPane("📝 Notes", id="tab_notes"):
                with Container(classes="container"):
                    with Vertical(classes="main-panel"):
                        yield Label("📝 Strategy Notes", classes="section-title")
                        notes_content = self._get_notes_content()
                        yield Static(notes_content, classes="notes-content")

        # Help dialog (hidden by default)
        yield HelpDialog(id="help_dialog", classes="help-dialog")

        yield Footer()

    def _get_statistics_content(self) -> str:
        """Get formatted statistics content."""
        if not self.current_chart:
            return "No chart data available"

        stats = self.chart_service.analyze_chart_statistics(self.current_chart)

        lines = [
            "📊 Chart Statistics",
            "=" * 40,
            f"Total Hands: {stats['total_hands']}",
            f"Hands Defined: {stats['total_hands']}/169 ({stats['total_hands']/169*100:.1f}%)",
            "",
            "Action Distribution:"
        ]

        for action, count in stats['action_distribution'].items():
            percentage = (count / stats['total_hands']) * 100
            lines.append(f"• {action.title()}: {count} ({percentage:.1f}%)")

        if stats['range_analysis']:
            lines.extend([
                "",
                "Range Analysis:",
                f"• Range Size: {stats['range_analysis']['range_percentage']:.1f}%",
                f"• Tightness: {stats['range_analysis']['tightness']}",
                f"• Recommendation: {stats['range_analysis']['recommendation']}"
            ])

        lines.extend([
            "",
            "Press 'Tab' to switch to other views",
            "Press 'q' to quit"
        ])

        return "\n".join(lines)

    def _get_notes_content(self) -> str:
        """Get formatted notes content."""
        stats = self.chart_service.analyze_chart_statistics(self.current_chart)

        lines = [
            f"Chart: {self.chart_name}",
            "",
            "Current Range Notes:",
            f"• Total hands: {stats['total_hands']}",
            f"• Range tightness: {stats['range_analysis']['tightness']}",
            "• Consider position and stack sizes",
            "• Adapt to opponent tendencies",
            "",
            "Key Concepts:",
            "• Raise premium hands aggressively",
            "• Call with marginal hands",
            "• Fold weak holdings",
            "",
            "Use arrow keys to navigate the matrix in Main Chart tab",
            "Press 'Tab' to switch between tabs",
            "Press 'q' to quit"
        ]

        return "\n".join(lines)

    def _show_error_notification(self, message: str, severity: ErrorSeverity):
        """Show error notification to user."""
        notification_type = {
            ErrorSeverity.LOW: NotificationType.INFO,
            ErrorSeverity.MEDIUM: NotificationType.WARNING,
            ErrorSeverity.HIGH: NotificationType.ERROR,
            ErrorSeverity.CRITICAL: NotificationType.ERROR
        }.get(severity, NotificationType.WARNING)

        self.ui_service.notify(message, notification_type)

    @handle_errors(ErrorCategory.UI_RENDERING, ErrorSeverity.HIGH)
    def on_mount(self) -> None:
        """Initialize the application."""
        self.title = f"Holdem CLI - {self.chart_name}"
        self.sub_title = "Interactive Poker Chart Viewer"

        # Focus the matrix initially
        try:
            matrix = self.query_one("#matrix", HandMatrixWidget)
            matrix.focus()
        except Exception as e:
            self.ui_service.show_error(f"Failed to initialize focus: {e}")

    @handle_errors(ErrorCategory.UI_RENDERING, ErrorSeverity.MEDIUM)
    def on_unmount(self) -> None:
        """Clean up when the application closes."""
        try:
            # Clear all caches
            self._clear_cache()

            # Clear render caches for all widgets
            self._clear_widget_caches()

            # Clear search results and state
            self.navigation_service.state.reset_search()

            # Clear database connection
            self._cleanup_database()

            # Log successful shutdown
            print("TUI closed successfully")
        except Exception as e:
            print(f"Error during TUI cleanup: {e}")

    def _clear_widget_caches(self) -> None:
        """Clear render caches for all matrix widgets."""
        try:
            for widget in self.query("HandMatrixWidget"):
                # Use proper Textual refresh instead of clearing internal cache
                widget.refresh()

                # Clear custom render cache if it exists
                if hasattr(widget, '_custom_render_cache'):
                    custom_cache = getattr(widget, '_custom_render_cache')
                    if hasattr(custom_cache, 'clear'):
                        custom_cache.clear()

                # Reset last actions hash if it exists
                if hasattr(widget, '_last_actions_hash'):
                    setattr(widget, '_last_actions_hash', None)
        except Exception as e:
            print(f"Warning: Could not clear widget caches: {e}")

    def _cleanup_database(self) -> None:
        """Clean up database connections."""
        try:
            if hasattr(self.db, 'close'):
                self.db.close()
        except Exception as e:
            print(f"Warning: Could not close database connection: {e}")

    def on_hand_selected(self, message: HandSelected) -> None:
        """Handle hand selection."""
        try:
            hand_details = self.query_one("#hand_details", HandDetailsWidget)
            matrix = self.query_one("#matrix", HandMatrixWidget)

            action = matrix.actions.get(message.hand)
            hand_details.update_hand(message.hand, action)

            # Update navigation state
            current_chart = self.state.get_current_chart()
            if current_chart:
                current_chart.selected_hand = message.hand

        except Exception as e:
            self.ui_service.show_error(f"Error selecting hand: {e}")

    def on_load_chart_requested(self, message: LoadChartRequested) -> None:
        """Handle load chart request."""
        try:
            # Create a sample tight range for demonstration
            tight_range = self._create_tight_range()

            # Update chart data
            current_chart_id = self.state.current_chart_id
            self.state.set_current_chart_data(tight_range)

            # Update matrix widget
            self._update_matrix()

            self.ui_service.show_success("✅ Tight range loaded successfully")

        except Exception as e:
            self.ui_service.show_error(f"❌ Failed to load chart: {e}")

    def on_save_chart_requested(self, message: SaveChartRequested) -> None:
        """Handle save chart request."""
        try:
            if not self.current_chart:
                self.ui_service.show_warning("⚠️ No chart data to save")
                return

            # Use chart service to save
            chart_id = self.state.current_chart_id
            metadata = self.chart_service.create_chart_metadata(
                name=self.chart_name,
                description=f"Saved from TUI on {datetime.now().isoformat()}"
            )

            success = self.chart_service.save_chart(
                chart_id=chart_id,
                name=self.chart_name,
                actions=self.current_chart,
                metadata=metadata
            )

            if success:
                self.ui_service.show_success(f"✅ Chart saved successfully! ({len(self.current_chart)} hands)")
            else:
                self.ui_service.show_error("❌ Failed to save chart")

        except Exception as e:
            self.ui_service.show_error(f"❌ Error saving chart: {e}")

    def on_compare_charts_requested(self, message: CompareChartsRequested) -> None:
        """Handle compare charts request."""
        try:
            # Create a comparison range (loose range for demo)
            comparison_range = self._create_loose_range()

            # Use chart service to compare
            comparison = self.chart_service.compare_charts(
                self.current_chart,
                comparison_range
            )

            # Display comparison results
            self._show_comparison_results(comparison)

        except Exception as e:
            self.ui_service.show_error(f"❌ Comparison failed: {e}")

    def _show_comparison_results(self, comparison: Dict[str, Any]) -> None:
        """Display comparison results in a user-friendly format."""
        lines = [
            "📊 Chart Comparison Results",
            "=" * 40,
            f"Chart 1: {comparison['chart1']['total_hands']} hands",
            f"Chart 2: {comparison['chart2']['total_hands']} hands",
            "",
            "🔍 Analysis:"
        ]

        # Show differences
        diff_analysis = comparison['differences']
        if diff_analysis['only_in_chart1']:
            lines.append(f"✅ Only in Chart 1: {len(diff_analysis['only_in_chart1'])} hands")

        if diff_analysis['only_in_chart2']:
            lines.append(f"✅ Only in Chart 2: {len(diff_analysis['only_in_chart2'])} hands")

        if diff_analysis['different_actions']:
            lines.append(f"⚖️ Different actions: {len(diff_analysis['different_actions'])} hands")

        if diff_analysis['same_actions']:
            lines.append(f"🤝 Same actions: {len(diff_analysis['same_actions'])} hands")

        # Show summary
        total_differences = diff_analysis['total_differences']
        lines.extend([
            "",
            "📈 Summary:",
            f"Total differences: {total_differences}",
            ".1f"
        ])

        self.ui_service.notify("\n".join(lines), timeout=15)

    def on_export_chart_requested(self, message: ExportChartRequested) -> None:
        """Handle export chart request."""
        try:
            if not self.current_chart:
                self.ui_service.show_warning("⚠️ No chart data to export")
                return

            # Use chart service to export
            metadata = self.chart_service.create_chart_metadata(
                name=self.chart_name,
                description="Exported from TUI"
            )

            # Export in multiple formats
            exported_files = self._export_chart_in_multiple_formats(metadata)

            if exported_files:
                file_list = "\n   ".join(f"📄 {path}" for path in exported_files)
                self.ui_service.show_success(f"✅ Chart exported in {len(exported_files)} formats:\n   {file_list}\n   ({len(self.current_chart)} hands)")
            else:
                self.ui_service.show_error("❌ No files were exported")

        except PermissionError:
            self.ui_service.show_error("❌ Permission denied. Cannot write to file")
        except OSError as e:
            self.ui_service.show_error(f"❌ File system error: {e}")
        except Exception as e:
            self.ui_service.show_error(f"❌ Error exporting chart: {e}")

    def _export_chart_in_multiple_formats(self, metadata) -> List[str]:
        """Export chart in multiple formats and return list of exported file paths."""
        base_name = self.chart_name.lower().replace(' ', '_')
        exported_files = []

        # Export to JSON
        json_path = f"{base_name}.json"
        if self.chart_service.export_chart(self.current_chart, 'json', json_path, metadata):
            exported_files.append(json_path)

        # Export to CSV
        csv_path = f"{base_name}.csv"
        if self.chart_service.export_chart(self.current_chart, 'csv', csv_path, metadata):
            exported_files.append(csv_path)

        # Export to TXT
        txt_path = f"{base_name}.txt"
        if self.chart_service.export_chart(self.current_chart, 'txt', txt_path, metadata):
            exported_files.append(txt_path)

        return exported_files

    def action_new_chart_tab(self) -> None:
        """Create a new chart tab."""
        try:
            tab_id, tab_name = self.state.generate_chart_id()

            # Create new chart data
            self.state.add_chart_tab(tab_id, tab_name)

            # Create and setup the tab UI
            tab_pane = self._create_tab_pane(tab_id, tab_name)
            self._setup_tab_content(tab_pane, tab_id, tab_name)

            # Switch to the new tab
            self._switch_to_new_tab(tab_id, tab_name)

            self.ui_service.show_success(f"✅ Created new chart tab: {tab_name}")

        except Exception as e:
            self.ui_service.show_error(f"❌ Failed to create new tab: {e}")

    def _create_tab_pane(self, tab_id: str, tab_name: str) -> TabPane:
        """Create and add new tab pane to the tabbed content."""
        tabs = self.query_one("#chart_tabs", TabbedContent)
        tab_pane = TabPane(f"📊 {tab_name}", id=f"tab_{tab_id}")
        tabs.add_pane(tab_pane)
        return tab_pane

    def _setup_tab_content(self, tab_pane: TabPane, tab_id: str, tab_name: str) -> None:
        """Setup the content and widgets for the new tab."""
        new_container = Container(classes="container")

        # Main panel with chart matrix
        main_panel = Vertical(classes="main-panel")
        main_panel.mount(HandMatrixWidget(
            self.charts[tab_id]["chart"],
            tab_name,
            id=f"matrix_{tab_id}"
        ))
        new_container.mount(main_panel)

        # Side panel with organized sections
        side_panel = Vertical(classes="side-panel")

        # Hand details section
        details_section = Vertical(classes="details-section")
        details_section.mount(Label("🃏 Hand Details", classes="section-title"))
        details_section.mount(HandDetailsWidget(id=f"hand_details_{tab_id}"))
        side_panel.mount(details_section)

        # Controls section
        controls_section = Vertical(classes="controls-section")
        controls_section.mount(Label("🎮 Controls", classes="section-title"))
        controls_section.mount(ChartControlsWidget(id=f"controls_{tab_id}"))
        side_panel.mount(controls_section)

        new_container.mount(side_panel)
        tab_pane.mount(new_container)

    def _switch_to_new_tab(self, tab_id: str, tab_name: str) -> None:
        """Switch to the newly created tab and notify user."""
        tabs = self.query_one("#chart_tabs", TabbedContent)
        tabs.active = f"tab_{tab_id}"
        self.state.switch_to_chart(tab_id)

    def action_close_current_tab(self) -> None:
        """Close the current tab."""
        if self.state.current_chart_id == "main":
            self.ui_service.show_warning("⚠️ Cannot close the main chart tab")
            return

        try:
            self._close_tab(self.state.current_chart_id)
            self._switch_to_main_tab()
            self.ui_service.show_success("✅ Tab closed")

        except Exception as e:
            self.ui_service.show_error(f"❌ Failed to close tab: {e}")

    def _close_tab(self, tab_id: str) -> None:
        """Remove a specific tab and its data."""
        tabs = self.query_one("#chart_tabs", TabbedContent)
        tab_pane_id = f"tab_{tab_id}"
        tabs.remove_pane(tab_pane_id)
        self.state.remove_chart_tab(tab_id)

    def _switch_to_main_tab(self) -> None:
        """Switch back to the main tab."""
        tabs = self.query_one("#chart_tabs", TabbedContent)
        self.state.switch_to_chart("main")
        tabs.active = "tab_main"

    def on_view_mode_changed(self, message: ViewModeChanged) -> None:
        """Handle view mode change."""
        old_mode = self.current_view_mode
        self.state.set_view_mode(message.mode)

        # Update the matrix widget with new view mode
        try:
            matrix = self.query_one("#matrix", HandMatrixWidget)
            matrix.view_mode = message.mode
            matrix.refresh()
            self.ui_service.show_success(f"✅ Switched to {message.mode.title()} view")
        except Exception as e:
            self.ui_service.show_error(f"❌ Failed to switch view mode: {e}")
            self.state.set_view_mode(old_mode)

    def action_help(self) -> None:
        """Toggle help dialog."""
        try:
            help_dialog = self.query_one("#help_dialog", HelpDialog)

            if self.state.help_dialog_open:
                # Close help dialog
                help_dialog.remove_class("open")
                self.state.help_dialog_open = False
                self.ui_service.notify("Help closed", timeout=2)
            else:
                # Open help dialog
                help_dialog.add_class("open")
                self.state.help_dialog_open = True
                self.ui_service.notify("Press H or Escape to close help", timeout=3)
        except Exception as e:
            self.ui_service.show_error(f"Error toggling help: {e}")

    def action_navigate_matrix(self, direction: str) -> None:
        """Navigate the matrix in the specified direction with enhanced feedback."""
        try:
            matrix = self.query_one("#matrix", HandMatrixWidget)

            # Store old position for feedback
            old_row, old_col = matrix.selected_row, matrix.selected_col
            old_hand = matrix.get_selected_hand()

            # Navigate to new position
            direction_map = {
                "up": Direction.UP,
                "down": Direction.DOWN,
                "left": Direction.LEFT,
                "right": Direction.RIGHT
            }

            if direction in direction_map:
                new_row, new_col = self.navigation_service.navigate_matrix(
                    direction_map[direction],
                    old_row,
                    old_col
                )

                matrix.selected_row = new_row
                matrix.selected_col = new_col

                # Get new position info
                new_hand = matrix.get_selected_hand()
                new_action = matrix.actions.get(new_hand)

                # Update hand details
                hand_details = self.query_one("#hand_details", HandDetailsWidget)
                hand_details.update_hand(new_hand, new_action)

                # Provide navigation feedback
                feedback = self.navigation_service.get_movement_feedback(
                    (old_row, old_col),
                    (new_row, new_col),
                    new_hand,
                    new_action
                )
                self.ui_service.notify(feedback, timeout=1)

        except Exception as e:
            self.ui_service.show_error(f"❌ Navigation error: {e}")

    def action_select_hand(self) -> None:
        """Select the currently highlighted hand."""
        try:
            matrix = self.query_one("#matrix", HandMatrixWidget)
            hand = matrix.get_selected_hand()
            self.on_hand_selected(HandSelected(hand))
        except Exception as e:
            self.ui_service.show_error(f"❌ Error selecting hand: {e}")

    def action_search_hands(self) -> None:
        """Search for hands in the chart."""
        self.ui_service.notify("🔍 Enter search query (e.g., 'AK', 'suited', 'raise')")

        # In a real implementation, you'd get this from user input
        # For now, we'll simulate with a predefined example
        example_queries = ["AK", "suited", "raise", "JJ"]
        example_query = example_queries[len(self.navigation_service.state.search_results) % len(example_queries)]

        results = self.navigation_service.perform_search(
            example_query,
            self.current_chart,
            self.query_one("#matrix", HandMatrixWidget)
        )

        if results:
            self.ui_service.show_success(f"🔍 Found {len(results)} hands matching '{example_query}'")
        else:
            self.ui_service.show_warning(f"❌ No hands found matching '{example_query}'")

    def action_next_search_result(self) -> None:
        """Navigate to next search result."""
        if not self.navigation_service.state.search_results:
            self.ui_service.show_warning("No search results to navigate")
            return

        result = self.navigation_service.next_search_result()
        if result:
            self.ui_service.notify(f"Next result: {result}", timeout=1)

    def action_prev_search_result(self) -> None:
        """Navigate to previous search result."""
        if not self.navigation_service.state.search_results:
            self.ui_service.show_warning("No search results to navigate")
            return

        result = self.navigation_service.previous_search_result()
        if result:
            self.ui_service.notify(f"Previous result: {result}", timeout=1)

    def action_cycle_view_mode(self) -> None:
        """Cycle through different view modes."""
        new_mode = self.navigation_service.cycle_view_mode()
        self.on_view_mode_changed(ViewModeChanged(new_mode))

    def action_load_chart(self) -> None:
        """Load chart action."""
        self.on_load_chart_requested(LoadChartRequested())

    def action_save_chart(self) -> None:
        """Save chart action."""
        self.on_save_chart_requested(SaveChartRequested())

    def action_compare_charts(self) -> None:
        """Compare charts action."""
        self.on_compare_charts_requested(CompareChartsRequested())

    def action_export_chart(self) -> None:
        """Export chart action."""
        self.on_export_chart_requested(ExportChartRequested())

    def _update_matrix(self) -> None:
        """Update the matrix widget with new chart data."""
        try:
            current_hash = self._get_chart_hash()

            # Only update if chart has changed
            if current_hash != self._last_chart_hash:
                matrix = self.query_one("#matrix", HandMatrixWidget)
                matrix.actions = self.current_chart
                matrix.matrix = HandMatrix(self.current_chart, self.chart_name)
                matrix._last_actions_hash = current_hash

                # Clear custom render cache instead of internal _render_cache
                if hasattr(matrix, '_custom_render_cache'):
                    matrix._custom_render_cache.clear()

                matrix.refresh()

                # Update our cache
                self._last_chart_hash = current_hash
                self._clear_cache()
            else:
                # Just refresh the display
                matrix = self.query_one("#matrix", HandMatrixWidget)
                matrix.refresh()
        except Exception as e:
            self.ui_service.show_error(f"❌ Failed to update matrix: {e}")

    def _create_tight_range(self) -> Dict[str, HandAction]:
        """Create a tight playing range for demonstration."""
        tight_range = {}

        # Very premium hands only
        premium = ["AA", "KK", "QQ", "JJ", "AKs", "AKo"]
        for hand in premium:
            tight_range[hand] = HandAction(ChartAction.RAISE, frequency=1.0, ev=3.0)

        # Some medium pairs
        medium = ["TT", "99"]
        for hand in medium:
            tight_range[hand] = HandAction(ChartAction.CALL, frequency=1.0, ev=1.0)

        return tight_range

    def _create_loose_range(self) -> Dict[str, HandAction]:
        """Create a loose playing range for demonstration."""
        loose_range = {}

        # Many more hands
        raise_hands = ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77",
                      "AKs", "AKo", "AQs", "AQo", "AJs", "AJo", "ATs"]
        for hand in raise_hands:
            loose_range[hand] = HandAction(ChartAction.RAISE, frequency=0.8, ev=1.5)

        call_hands = ["66", "55", "44", "33", "22", "KQs", "KQo", "KJs",
                     "QJs", "JTs", "A9s", "A8s", "A7s", "A6s", "A5s"]
        for hand in call_hands:
            loose_range[hand] = HandAction(ChartAction.CALL, frequency=1.0, ev=0.5)

        return loose_range
