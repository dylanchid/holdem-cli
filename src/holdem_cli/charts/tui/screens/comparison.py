"""
Comparison screen for the TUI application.

This screen provides functionality to compare multiple poker charts
side by side, highlighting differences and similarities.
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, Button, Label, Select, DataTable
from textual.screen import Screen
from textual.reactive import reactive
from textual import events
from textual.message import Message

from ..widgets import HandMatrixWidget
from ..widgets.matrix import create_sample_range
from ..core.state import ChartViewerState
from ..core.events import get_event_bus, EventType
from holdem_cli.services.charts.chart_service import get_chart_service
from typing import Dict, Optional, List, Tuple, Any


class ComparisonScreen(Screen):
    """
    Screen for comparing multiple poker charts.

    Features:
    - Side-by-side chart comparison
    - Difference highlighting
    - Statistical analysis
    - Export comparison results
    """

    CSS = """
    ComparisonScreen {
        layout: vertical;
    }

    .comparison-container {
        layout: vertical;
        height: 100%;
        padding: 1;
        margin: 0;
    }

    .chart-selection {
        height: 6;
        border: solid $primary;
        background: $surface;
        padding: 1;
        margin: 0 0 1 0;
    }

    .charts-display {
        height: 50%;
        layout: horizontal;
        border: solid $primary;
        background: $surface;
        padding: 1;
        margin: 0 0 1 0;
    }

    .chart-panel {
        width: 1fr;
        height: 100%;
        padding: 0 1;
        margin: 0 1 0 0;
    }

    .analysis-section {
        height: 30%;
        border: solid $primary;
        background: $surface;
        padding: 1;
        margin: 0 0 1 0;
    }

    .controls-section {
        height: 4;
        border: solid $primary;
        background: $surface;
        padding: 1;
        margin: 0 0 1 0;
    }

    .section-title {
        text-style: bold;
        color: $primary;
        margin: 0 0 1 0;
    }

    .difference-highlight {
        background: $warning;
        color: $text;
    }

    .similarity-highlight {
        background: $success;
        color: $text;
    }
    """

    # Reactive state
    left_chart_id: reactive[Optional[str]] = reactive(None)
    right_chart_id: reactive[Optional[str]] = reactive(None)
    comparison_results: reactive[Optional[Dict]] = reactive(None)
    view_mode: reactive[str] = reactive("range")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state = ChartViewerState()
        self.event_bus = get_event_bus()
        self.chart_service = get_chart_service()
        self._setup_event_handlers()

    def _setup_event_handlers(self):
        """Setup event handlers for reactive updates."""
        self.event_bus.subscribe(EventType.CHART_LOADED, self._on_chart_loaded)

    def _on_chart_loaded(self, event):
        """Handle chart loaded events."""
        self._update_chart_selectors()

    def compose(self) -> ComposeResult:
        """Compose the comparison screen layout."""
        yield Header()

        with Container(classes="comparison-container"):
            # Chart selection section
            with Vertical(classes="chart-selection"):
                yield Label("📊 Chart Comparison Tool", classes="section-title")
                with Horizontal():
                    yield Label("Left Chart:", classes="field-label")
                    yield Select(
                        self._get_chart_options(),
                        value=self.left_chart_id,
                        id="left_chart_select",
                        classes="chart-selector"
                    )
                    yield Label("Right Chart:", classes="field-label")
                    yield Select(
                        self._get_chart_options(),
                        value=self.right_chart_id,
                        id="right_chart_select",
                        classes="chart-selector"
                    )
                    yield Button("Compare", id="compare_btn", variant="primary")

            # Charts display section
            with Horizontal(classes="charts-display"):
                # Left chart panel
                with Vertical(classes="chart-panel"):
                    yield Label("Left Chart", classes="section-title", id="left_chart_title")
                    self._left_matrix = HandMatrixWidget(
                        self._get_chart_data(self.left_chart_id),
                        self._get_chart_name(self.left_chart_id),
                        id="left_matrix"
                    )
                    yield self._left_matrix

                # Right chart panel
                with Vertical(classes="chart-panel"):
                    yield Label("Right Chart", classes="section-title", id="right_chart_title")
                    self._right_matrix = HandMatrixWidget(
                        self._get_chart_data(self.right_chart_id),
                        self._get_chart_name(self.right_chart_id),
                        id="right_matrix"
                    )
                    yield self._right_matrix

            # Analysis section
            with Vertical(classes="analysis-section"):
                yield Label("📈 Comparison Analysis", classes="section-title")
                yield Static("", id="analysis_text")
                yield DataTable(id="differences_table")

            # Controls section
            with Vertical(classes="controls-section"):
                yield Label("🎮 Controls", classes="section-title")
                with Horizontal():
                    yield Button("Export Results", id="export_results", variant="default")
                    yield Button("Reset Comparison", id="reset_comparison", variant="warning")
                    yield Button("Back to Main", id="back_to_main", variant="primary")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the comparison screen."""
        self.title = "Holdem CLI - Chart Comparison"
        self.sub_title = "Compare poker strategies side by side"

        self._update_chart_selectors()
        self._setup_differences_table()

    def _get_chart_options(self) -> List[Tuple[str, str]]:
        """Get available chart options for selectors."""
        options = [("Select Chart", "")]
        for chart_id, chart in self.state.charts.items():
            options.append((chart.name, chart_id))
        return options

    def _get_chart_data(self, chart_id: Optional[str]) -> Dict:
        """Get chart data for a given chart ID."""
        if chart_id and chart_id in self.state.charts:
            return self.state.charts[chart_id].data
        return {}

    def _get_chart_name(self, chart_id: Optional[str]) -> str:
        """Get chart name for a given chart ID."""
        if chart_id and chart_id in self.state.charts:
            return self.state.charts[chart_id].name
        return "No Chart Selected"

    def _update_chart_selectors(self):
        """Update chart selector options."""
        try:
            left_select = self.query_one("#left_chart_select", Select)
            right_select = self.query_one("#right_chart_select", Select)

            current_left = left_select.value
            current_right = right_select.value

            options = self._get_chart_options()
            left_select.set_options(options)
            right_select.set_options(options)

            # Restore previous selections if still valid
            if current_left and current_left in [opt[1] for opt in options]:
                left_select.value = current_left
            if current_right and current_right in [opt[1] for opt in options]:
                right_select.value = current_right

        except:
            pass

    def _setup_differences_table(self):
        """Setup the differences data table."""
        try:
            table = self.query_one("#differences_table", DataTable)
            table.add_columns("Hand", "Left Action", "Right Action", "Difference")
        except:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id

        if button_id == "compare_btn":
            self._perform_comparison()
        elif button_id == "export_results":
            self._export_comparison()
        elif button_id == "reset_comparison":
            self._reset_comparison()
        elif button_id == "back_to_main":
            self._back_to_main()

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle selector change events."""
        if event.select.id == "left_chart_select":
            self.left_chart_id = event.value if isinstance(event.value, str) else None
            self._update_left_chart()
        elif event.select.id == "right_chart_select":
            self.right_chart_id = event.value if isinstance(event.value, str) else None
            self._update_right_chart()

    def _update_left_chart(self):
        """Update the left chart display."""
        if hasattr(self, '_left_matrix') and self.left_chart_id:
            chart_data = self._get_chart_data(self.left_chart_id)
            chart_name = self._get_chart_name(self.left_chart_id)
            self._left_matrix.update_actions(chart_data)

            try:
                title_widget = self.query_one("#left_chart_title", Label)
                title_widget.update(chart_name)
            except:
                pass

    def _update_right_chart(self):
        """Update the right chart display."""
        if hasattr(self, '_right_matrix') and self.right_chart_id:
            chart_data = self._get_chart_data(self.right_chart_id)
            chart_name = self._get_chart_name(self.right_chart_id)
            self._right_matrix.update_actions(chart_data)

            try:
                title_widget = self.query_one("#right_chart_title", Label)
                title_widget.update(chart_name)
            except:
                pass

    def _perform_comparison(self):
        """Perform the chart comparison."""
        if not self.left_chart_id or not self.right_chart_id:
            self.notify("⚠️ Please select two charts to compare", severity="warning")
            return

        if self.left_chart_id == self.right_chart_id:
            self.notify("⚠️ Please select different charts to compare", severity="warning")
            return

        try:
            # Perform comparison using chart service
            comparison = self.chart_service.compare_charts(self.left_chart_id, self.right_chart_id)
            self.comparison_results = comparison

            # Update analysis display
            self._update_analysis_display(comparison)

            # Update differences table
            self._update_differences_table(comparison)

            self.notify("✅ Comparison complete! Check analysis below.", severity="information")

        except Exception as e:
            self.notify(f"❌ Comparison failed: {e}", severity="error")

    def _update_analysis_display(self, comparison: Dict):
        """Update the analysis text display."""
        try:
            analysis_widget = self.query_one("#analysis_text", Static)

            chart1 = comparison["chart1"]
            chart2 = comparison["chart2"]
            differences = comparison["differences"]
            similarity = comparison["similarity"]
            analysis = comparison["analysis"]

            analysis_text = ".1f"".1f"".1f"".1f"f"""
📊 Comparison Results

Left Chart: {chart1['name']} ({chart1['total_hands']} hands)
Right Chart: {chart2['name']} ({chart2['total_hands']} hands)

🔍 Analysis: {analysis}

📈 Statistics:
• Total Differences: {differences['total_differences']}
• Similarity Score: {similarity:.1f}%
• Hands Only in Left: {len(differences['only_in_chart1'])}
• Hands Only in Right: {len(differences['only_in_chart2'])}
• Different Actions: {len(differences['different_actions'])}
            """.strip()

            analysis_widget.update(analysis_text)

        except:
            pass

    def _update_differences_table(self, comparison: Dict):
        """Update the differences data table."""
        try:
            table = self.query_one("#differences_table", DataTable)
            table.clear()

            differences = comparison["differences"]

            # Add different actions
            for diff in differences["different_actions"][:20]:  # Limit to 20 rows
                table.add_row(
                    diff["hand"],
                    diff["action1"],
                    diff["action2"],
                    "Different Actions"
                )

            # Add hands only in left chart
            for hand in differences["only_in_chart1"][:10]:
                left_action = self._get_action_for_hand(self.left_chart_id, hand) if self.left_chart_id else None
                table.add_row(hand, left_action or "No Action", "Not Present", "Only in Left")

            # Add hands only in right chart
            for hand in differences["only_in_chart2"][:10]:
                right_action = self._get_action_for_hand(self.right_chart_id, hand) if self.right_chart_id else None
                table.add_row(hand, "Not Present", right_action or "No Action", "Only in Right")

        except:
            pass

    def _get_action_for_hand(self, chart_id: str, hand: str) -> Optional[str]:
        """Get action for a specific hand in a chart."""
        chart_data = self._get_chart_data(chart_id)
        if hand in chart_data:
            return chart_data[hand].action.value
        return None

    def _export_comparison(self):
        """Export comparison results."""
        if not self.comparison_results:
            self.notify("⚠️ No comparison results to export", severity="warning")
            return

        try:
            # Export comparison results to file
            import json
            from datetime import datetime

            export_data = {
                "export_format": "holdem-cli-comparison-v1",
                "export_timestamp": datetime.now().isoformat(),
                "comparison": self.comparison_results
            }

            filename = f"chart_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)

            self.notify(f"✅ Comparison exported to: {filename}", severity="information")

        except Exception as e:
            self.notify(f"❌ Export failed: {e}", severity="error")

    def _reset_comparison(self):
        """Reset the comparison."""
        self.left_chart_id = None
        self.right_chart_id = None
        self.comparison_results = None

        try:
            # Clear displays
            analysis_widget = self.query_one("#analysis_text", Static)
            analysis_widget.update("")

            table = self.query_one("#differences_table", DataTable)
            table.clear()

            # Reset selectors
            left_select = self.query_one("#left_chart_select", Select)
            right_select = self.query_one("#right_chart_select", Select)
            left_select.value = ""
            right_select.value = ""

            # Reset matrices
            if hasattr(self, '_left_matrix'):
                self._left_matrix.update_actions({})
            if hasattr(self, '_right_matrix'):
                self._right_matrix.update_actions({})

        except:
            pass

        self.notify("🔄 Comparison reset", severity="information")

    def _back_to_main(self):
        """Go back to main screen."""
        # This will be handled by the main app
        self.notify("🏠 Returning to main screen...", severity="information")

    def on_key(self, event: events.Key) -> None:
        """Handle keyboard input."""
        if event.key == "f1":
            self._perform_comparison()
        elif event.key == "f2":
            self._export_comparison()
        elif event.key == "f3":
            self._reset_comparison()
        elif event.key == "escape":
            self._back_to_main()

    def get_screen_info(self) -> Dict[str, Any]:
        """Get information about the current comparison state."""
        return {
            "screen_type": "comparison",
            "left_chart_id": self.left_chart_id,
            "right_chart_id": self.right_chart_id,
            "has_comparison": self.comparison_results is not None,
            "chart_count": len(self.state.charts)
        }


# Screen factory function
def create_comparison_screen(**kwargs) -> ComparisonScreen:
    """Create a configured comparison screen."""
    return ComparisonScreen(**kwargs)
