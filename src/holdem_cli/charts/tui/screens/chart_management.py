"""
Unified chart management screen combining CLI and TUI functionality.

This screen provides a comprehensive interface for managing poker charts,
combining all CLI chart commands into a unified TUI experience.
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import TabbedContent, TabPane
from textual.widgets import Header, Footer, Button, Label, Input, Static, Select, DataTable, TextArea, ListView, ListItem
from textual.screen import Screen
from textual import events
from textual.binding import Binding

from ....services.holdem_service import get_holdem_service


class ChartManagementScreen(Screen):
    """Comprehensive chart management screen."""

    CSS = """
    ChartManagementScreen {
        layout: vertical;
        padding: 1;
    }

    .title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 2;
        width: 100%;
    }

    .management-section {
        width: 100%;
        margin: 1 0;
        border: solid $primary;
        padding: 1;
        background: $surface;
        height: 10;
    }

    .management-row {
        layout: horizontal;
        margin: 1 0;
        align: center middle;
    }

    .management-label {
        width: 15;
        margin-right: 2;
    }

    .management-input {
        width: 30;
        margin-right: 2;
    }

    .management-button {
        width: 15;
        margin: 0 1;
    }

    .content-section {
        width: 100%;
        margin: 1 0;
        border: solid $secondary;
        padding: 1;
        background: $background;
        height: 25;
    }

    .chart-list {
        height: 20;
        overflow: auto;
        background: $surface;
        padding: 1;
        border: solid grey;
    }

    .chart-item {
        layout: horizontal;
        margin: 1 0;
        align: center middle;
        padding: 1;
        border: solid grey;
        background: $background;
    }

    .chart-item:hover {
        background: $primary;
        color: $text;
    }

    .chart-name {
        width: 20;
        color: $primary;
        text-style: bold;
    }

    .chart-spot {
        width: 25;
        color: $secondary;
    }

    .chart-depth {
        width: 10;
        text-align: center;
    }

    .chart-action {
        width: 15;
        dock: right;
    }

    .chart-viewer {
        height: 20;
        overflow: auto;
        background: $surface;
        padding: 1;
        border: solid grey;
    }

    .footer-text {
        text-align: center;
        color: grey;
        margin-top: 1;
        width: 100%;
    }
    """

    BINDINGS = [
        Binding("escape", "back", "Back to Main Menu"),
        Binding("f5", "refresh", "Refresh Charts"),
        Binding("f6", "view_sample", "View Sample Chart"),
        Binding("up", "prev_chart", "Previous Chart"),
        Binding("down", "next_chart", "Next Chart"),
        Binding("enter", "select_chart", "Select Chart"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.charts_data = []
        self.current_chart = None
        self.selected_chart = None

    def compose(self) -> ComposeResult:
        """Compose the chart management screen."""
        yield Header()

        yield Label("📊 Chart Management", classes="title")

        # Management controls
        with Vertical(classes="management-section"):
            yield Label("⚙️ Chart Management", classes="section-title")

            # View chart
            with Horizontal(classes="management-row"):
                yield Label("View Chart:", classes="management-label")
                yield Input(
                    placeholder="Enter chart name or ID",
                    id="view_chart_input",
                    classes="management-input"
                )
                yield Button("View", id="view_chart", variant="primary", classes="management-button")

            # Create chart
            with Horizontal(classes="management-row"):
                yield Label("Create Chart:", classes="management-label")
                yield Input(
                    placeholder="New chart name",
                    id="create_chart_input",
                    classes="management-input"
                )
                yield Button("Create", id="create_chart", variant="primary", classes="management-button")

            # Import/Export
            with Horizontal(classes="management-row"):
                yield Label("Import/Export:", classes="management-label")
                yield Input(
                    placeholder="Filename",
                    id="import_export_input",
                    classes="management-input"
                )
                yield Button("Import", id="import_chart", variant="primary", classes="management-button")
                yield Button("Export", id="export_chart", variant="default", classes="management-button")

        # Main content with tabs
        with TabbedContent(id="chart_tabs", initial="tab_list"):
            # Chart list tab
            with TabPane("📋 Chart List", id="tab_list"):
                with Vertical(classes="content-section"):
                    yield Label("📊 Available Charts", classes="section-title")
                    yield Label("💡 Use arrow keys to select, Enter to view, or type chart name above", classes="help-text")
                    self.chart_list_view = ListView(id="chart_list_view")
                    yield self.chart_list_view

            # Chart viewer tab
            with TabPane("👁️ Chart Viewer", id="tab_viewer"):
                with Vertical(classes="content-section"):
                    yield Label("📊 Chart Viewer", classes="section-title")
                    yield Static("Select a chart to view", id="chart_viewer", classes="chart-viewer")

            # Chart analysis tab
            with TabPane("📈 Analysis", id="tab_analysis"):
                with Vertical(classes="content-section"):
                    yield Label("📈 Chart Analysis", classes="section-title")
                    yield Static("Select a chart to analyze", id="chart_analysis", classes="chart-viewer")

        yield Static("Press F5 to refresh • Press F6 for sample • Press Escape to go back", classes="footer-text")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the screen."""
        self._refresh_charts()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id

        if button_id == "view_chart":
            self._view_chart()
        elif button_id == "create_chart":
            self._create_chart()
        elif button_id == "import_chart":
            self._import_chart()
        elif button_id == "export_chart":
            self._export_chart()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes."""
        # Store input values for later use
        if event.input.id == "view_chart_input":
            self.view_chart_name = event.value
        elif event.input.id == "create_chart_input":
            self.create_chart_name = event.value
        elif event.input.id == "import_export_input":
            self.import_export_filename = event.value

    def action_refresh(self) -> None:
        """Refresh charts list."""
        self._refresh_charts()

    def action_view_sample(self) -> None:
        """View sample chart."""
        self._view_sample_chart()

    def action_prev_chart(self) -> None:
        """Select previous chart."""
        if hasattr(self, 'chart_list_view') and self.charts_data:
            current_index = self.chart_list_view.index or 0
            new_index = max(0, current_index - 1)
            self.chart_list_view.index = new_index

    def action_next_chart(self) -> None:
        """Select next chart."""
        if hasattr(self, 'chart_list_view') and self.charts_data:
            current_index = self.chart_list_view.index or 0
            new_index = min(len(self.charts_data) - 1, current_index + 1)
            self.chart_list_view.index = new_index

    def action_select_chart(self) -> None:
        """Select and view the currently highlighted chart."""
        if hasattr(self, 'chart_list_view') and self.charts_data:
            current_index = self.chart_list_view.index or 0
            if 0 <= current_index < len(self.charts_data):
                chart = self.charts_data[current_index]
                chart_name = chart.get('name', '')
                self._view_chart_by_name(chart_name)

    def _view_chart_by_name(self, chart_name: str) -> None:
        """View a chart by name directly."""
        try:
            with get_holdem_service() as service:
                chart = service.get_chart(chart_name)

                if chart:
                    self.current_chart = chart
                    self._display_chart_viewer(chart)
                    self._switch_to_tab("tab_viewer")
                    self.notify(f"✅ Loaded chart: {chart['name']}", severity="information")
                else:
                    self.notify(f"❌ Chart '{chart_name}' not found", severity="error")

        except Exception as e:
            self.notify(f"❌ Error viewing chart: {e}", severity="error")

    def _refresh_charts(self) -> None:
        """Refresh the charts list."""
        try:
            with get_holdem_service() as service:
                self.charts_data = service.list_charts()
                self._display_charts()
        except Exception as e:
            self.notify(f"❌ Error loading charts: {e}", severity="error")

    def _display_charts(self) -> None:
        """Display the list of charts in the ListView."""
        try:
            if hasattr(self, 'chart_list_view'):
                # Clear existing items
                self.chart_list_view.clear()

                if not self.charts_data:
                    self.chart_list_view.append(ListItem(Label("No charts found. Create or import some charts to get started.")))
                else:
                    for chart in self.charts_data:
                        name = chart.get('name', 'Unknown')
                        spot = chart.get('spot', 'Unknown')
                        depth = chart.get('stack_depth', 'Unknown')
                        chart_text = f"📊 {name} | {spot} | {depth}bb"
                        self.chart_list_view.append(ListItem(Label(chart_text)))

        except Exception as e:
            self.notify(f"❌ Error displaying charts: {e}", severity="error")

    def _view_chart(self) -> None:
        """View a specific chart."""
        try:
            chart_name = getattr(self, 'view_chart_name', '').strip()
            if not chart_name:
                self.notify("❌ Please enter a chart name", severity="error")
                return

            with get_holdem_service() as service:
                chart = service.get_chart(chart_name)

                if chart:
                    self.current_chart = chart
                    self._display_chart_viewer(chart)
                    self._switch_to_tab("tab_viewer")
                    self.notify(f"✅ Loaded chart: {chart['name']}", severity="information")
                else:
                    self.notify(f"❌ Chart '{chart_name}' not found", severity="error")

        except Exception as e:
            self.notify(f"❌ Error viewing chart: {e}", severity="error")

    def _view_sample_chart(self) -> None:
        """View the sample chart."""
        try:
            with get_holdem_service() as service:
                chart = service.get_chart("sample")

                if chart:
                    self.current_chart = chart
                    self._display_chart_viewer(chart)
                    self._switch_to_tab("tab_viewer")
                    self.notify(f"✅ Loaded sample chart", severity="information")
                else:
                    self.notify("❌ Sample chart not available", severity="error")

        except Exception as e:
            self.notify(f"❌ Error loading sample chart: {e}", severity="error")

    def _display_chart_viewer(self, chart: dict) -> None:
        """Display chart in the viewer tab."""
        try:
            lines = [
                f"📊 {chart['name']}",
                "=" * 50,
                f"Hands: {chart['hand_count']}",
                "",
                "Chart Matrix:"
            ]

            # Display chart actions in a grid format
            actions = chart['actions']
            hand_ranges = ['AA', 'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'A8s', 'A7s', 'A6s', 'A5s', 'A4s', 'A3s', 'A2s',
                          'AKo', 'KK', 'KQs', 'KJs', 'KTs', 'K9s', 'K8s', 'K7s', 'K6s', 'K5s', 'K4s', 'K3s', 'K2s']

            # Create a simple text matrix representation
            for i, hand in enumerate(hand_ranges[:20]):  # Show first 20 hands
                if hand in actions:
                    action = actions[hand]
                    action_str = f"{hand}: {action.action.value.title()}"
                    lines.append(action_str)

            content = "\\n".join(lines)

            chart_viewer = self.query_one("#chart_viewer", Static)
            chart_viewer.update(content)

        except Exception as e:
            self.notify(f"❌ Error displaying chart: {e}", severity="error")

    def _create_chart(self) -> None:
        """Create a new chart."""
        try:
            chart_name = getattr(self, 'create_chart_name', '').strip()
            if not chart_name:
                self.notify("❌ Please enter a chart name", severity="error")
                return

            # For now, create an empty chart - in a real implementation,
            # this would launch a chart builder interface
            with get_holdem_service() as service:
                from ...tui.widgets.matrix import create_sample_range
                actions = create_sample_range()

                success, message = service.save_chart(
                    
                    chart_name,
                    "Custom chart created via TUI",
                    actions,
                    100  # Default stack depth
                )

                if success:
                    self.notify(f"✅ {message}", severity="information")
                    # Clear input
                    create_input = self.query_one("#create_chart_input", Input)
                    create_input.value = ""
                    # Refresh charts list
                    self._refresh_charts()
                else:
                    self.notify(f"❌ {message}", severity="error")

        except Exception as e:
            self.notify(f"❌ Error creating chart: {e}", severity="error")

    def _import_chart(self) -> None:
        """Import a chart from file."""
        try:
            filename = getattr(self, 'import_export_filename', '').strip()
            if not filename:
                self.notify("❌ Please enter a filename", severity="error")
                return

            # This would need a proper file import implementation
            # For now, show a placeholder message
            self.notify(f"📁 Import functionality for '{filename}' coming soon", severity="information")

        except Exception as e:
            self.notify(f"❌ Error importing chart: {e}", severity="error")

    def _export_chart(self) -> None:
        """Export the current chart."""
        try:
            if not self.current_chart:
                self.notify("❌ No chart loaded to export", severity="error")
                return

            filename = getattr(self, 'import_export_filename', '').strip()
            if not filename:
                filename = self.current_chart['name']

            with get_holdem_service() as service:
                success, message = service.export_chart(
                    self.current_chart['name'],
                    format='json'  # Default to JSON
                )

                if success:
                    self.notify(f"✅ {message}", severity="information")
                else:
                    self.notify(f"❌ {message}", severity="error")

        except Exception as e:
            self.notify(f"❌ Error exporting chart: {e}", severity="error")

    def _switch_to_tab(self, tab_id: str) -> None:
        """Switch to a specific tab."""
        try:
            tabs = self.query_one("#chart_tabs", TabbedContent)
            tabs.active = tab_id
        except Exception as e:
            pass  # Tab switch is optional

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle ListView item selection."""
        if event.list_view.id == "chart_list_view" and self.charts_data:
            current_index = event.list_view.index or 0
            if 0 <= current_index < len(self.charts_data):
                chart = self.charts_data[current_index]
                chart_name = chart.get('name', '')
                self._view_chart_by_name(chart_name)

    def action_back(self) -> None:
        """Go back to the main menu."""
        self.app.pop_screen()

    def on_key(self, event: events.Key) -> None:
        """Handle keyboard input."""
        if event.key == "escape":
            self.action_back()
