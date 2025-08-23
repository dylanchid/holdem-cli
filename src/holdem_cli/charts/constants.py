"""
Constants and configuration for the TUI components.

This module contains all shared constants, CSS styles, key bindings,
and configuration values used across the TUI application.
"""

from textual.binding import Binding

# Application Settings
DEFAULT_CHART_NAME = "Sample Chart"
DEFAULT_VIEW_MODE = "range"

# View Modes
VIEW_MODES = ["range", "frequency", "ev"]
VIEW_MODE_EMOJIS = {
    "range": "📊",
    "frequency": "📈",
    "ev": "💰"
}

# Position Mappings
POSITIONS = {
    "UTG": "Under the Gun",
    "MP": "Middle Position",
    "CO": "Cutoff",
    "BTN": "Button",
    "SB": "Small Blind",
    "BB": "Big Blind"
}

# CSS Constants
MAIN_CSS = """
.header {
    text-style: bold;
    background: $primary;
    color: $text;
    padding: 1 2;
    height: 3;
    text-align: center;
}

.container {
    layout: horizontal;
    padding: 0 1;
    height: 100%;
    margin: 0;
}

.main-panel {
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

.stats-section {
    height: 4;
    border: solid $secondary;
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

.details-section {
    height: 10;
    border: solid $accent;
    background: $surface;
    padding: 1;
    margin: 1 0;
}

.section-title {
    text-style: bold;
    color: $primary;
    margin: 0 0 1 0;
}

.help-dialog {
    display: none;
    dock: bottom;
    layer: overlay;
    offset-x: 70%;
    offset-y: -2;
    width: 60;
    height: 25;
    background: $surface;
    border: solid $primary;
    padding: 2;
}

.help-dialog.open {
    display: block;
}

Footer {
    background: $surface;
    border-top: solid $primary;
    height: 3;
    padding: 0 1;
}
"""

# Widget CSS
HAND_MATRIX_CSS = """
HandMatrixWidget {
    border: solid $primary;
    padding: 1;
    margin: 1;
}

HandMatrixWidget:focus {
    border: solid $accent;
}

.hand-cell {
    width: 4;
    height: 1;
    text-align: center;
}

.hand-cell-selected {
    background: $accent;
    color: $text;
}

.hand-cell-raise {
    background: red;
    color: white;
}

.hand-cell-call {
    background: green;
    color: white;
}

.hand-cell-fold {
    background: $surface;
    color: $text-muted;
}

.hand-cell-mixed {
    background: yellow;
    color: black;
}

.hand-cell-bluff {
    background: blue;
    color: white;
}
"""

HAND_DETAILS_CSS = """
HandDetailsWidget {
    border: solid $primary;
    padding: 1;
    margin: 1;
    height: 15;
    min-width: 30;
}
"""

CHART_CONTROLS_CSS = """
ChartControlsWidget {
    border: solid $primary;
    padding: 1;
    margin: 1;
    height: 10;
}
"""

HELP_DIALOG_CSS = """
HelpDialog {
    border: solid $primary;
    background: $surface;
    padding: 2;
    width: 80;
    height: 25;
    margin: 2;
}

.help-title {
    text-style: bold;
    color: $primary;
    margin: 0 0 1 0;
}

.help-section {
    margin: 0 0 1 0;
}

.help-key {
    color: $accent;
    text-style: bold;
}
"""

CHART_IMPORT_DIALOG_CSS = """
ChartImportDialog {
    border: solid $primary;
    background: $surface;
    padding: 2;
    margin: 2;
    width: 60;
    height: 20;
}
"""

# Key Bindings
NAVIGATION_BINDINGS = [
    Binding("up", "navigate_matrix('up')", "Up"),
    Binding("down", "navigate_matrix('down')", "Down"),
    Binding("left", "navigate_matrix('left')", "Left"),
    Binding("right", "navigate_matrix('right')", "Right"),
    Binding("enter", "select_hand", "Select Hand"),
    Binding("space", "select_hand", "Select Hand"),
]

POSITION_BINDINGS = [
    Binding("1", "jump_position('UTG')", "UTG"),
    Binding("2", "jump_position('MP')", "MP"),
    Binding("3", "jump_position('CO')", "CO"),
    Binding("4", "jump_position('BTN')", "BTN"),
    Binding("5", "jump_position('SB')", "SB"),
    Binding("6", "jump_position('BB')", "BB"),
]

CHART_OPERATION_BINDINGS = [
    Binding("ctrl+l", "load_chart", "Load Chart"),
    Binding("ctrl+s", "save_chart", "Save Chart"),
    Binding("ctrl+c", "compare_charts", "Compare Charts"),
    Binding("ctrl+e", "export_chart", "Export Chart"),
]

VIEW_CONTROL_BINDINGS = [
    Binding("r", "reset_view", "Reset View"),
    Binding("f", "toggle_frequency", "Toggle Frequency"),
    Binding("v", "toggle_ev_view", "Toggle EV View"),
    Binding("m", "cycle_view_mode", "Cycle View Mode"),
    Binding("/", "search_hands", "Search Hands"),
    Binding("n", "next_search_result", "Next Result"),
    Binding("shift+n", "prev_search_result", "Previous Result"),
]

RANGE_BUILDER_BINDINGS = [
    Binding("b", "toggle_range_builder", "Toggle Range Builder"),
    Binding("a", "add_hand_to_range", "Add Hand"),
    Binding("d", "remove_hand_from_range", "Remove Hand"),
    Binding("c", "clear_custom_range", "Clear Range"),
]

QUICK_ACTION_BINDINGS = [
    Binding("ctrl+r", "refresh_data", "Refresh"),
    Binding("ctrl+z", "undo_action", "Undo"),
    Binding("escape", "close_help_or_clear", "Close Help/Clear Selection"),
]

TAB_NAVIGATION_BINDINGS = [
    Binding("ctrl+t", "new_chart_tab", "New Chart Tab"),
    Binding("ctrl+w", "close_current_tab", "Close Tab"),
    Binding("ctrl+1", "switch_to_tab('main')", "Main Tab"),
    Binding("ctrl+2", "switch_to_tab('stats')", "Stats Tab"),
    Binding("ctrl+3", "switch_to_tab('notes')", "Notes Tab"),
]

BASIC_BINDINGS = [
    Binding("q", "quit", "Quit"),
    Binding("h", "help", "Help"),
    Binding("tab", "cycle_focus", "Next Panel"),
    Binding("shift+tab", "cycle_focus", "Previous Panel"),
]

QUIZ_BINDINGS = [
    Binding("q", "quit", "Quit"),
    Binding("r", "next_question", "Next Question"),
    Binding("s", "show_answer", "Show Answer"),
]

# All bindings combined for main app
ALL_BINDINGS = (
    BASIC_BINDINGS +
    NAVIGATION_BINDINGS +
    POSITION_BINDINGS +
    CHART_OPERATION_BINDINGS +
    VIEW_CONTROL_BINDINGS +
    RANGE_BUILDER_BINDINGS +
    QUICK_ACTION_BINDINGS +
    TAB_NAVIGATION_BINDINGS
)

# Help Content
HELP_CONTENT = [
    "[bold]🎯 Holdem CLI Chart Viewer Help[/bold]",
    "=" * 40,
    "",
    "[bold]Navigation:[/bold]",
    "  [accent]↑↓←→ / WASD[/accent]      Navigate matrix",
    "  [accent]Enter / Space[/accent]     Select hand & show details",
    "  [accent]Tab / Shift+Tab[/accent]   Cycle between panels",
    "  [accent]Escape[/accent]            Clear selection",
    "  [accent]R[/accent]                 Reset view to top-left",
    "",
    "[bold]View Controls:[/bold]",
    "  [accent]F[/accent]                 Toggle frequency view",
    "  [accent]V[/accent]                 Toggle EV view",
    "  [accent]M[/accent]                 Cycle through view modes",
    "  [accent]/[/accent]                 Search hands",
    "  [accent]N[/accent]                 Next search result",
    "  [accent]Shift+N[/accent]           Previous search result",
    "",
    "[bold]Range Builder:[/bold]",
    "  [accent]B[/accent]                 Toggle range builder mode",
    "  [accent]A[/accent]                 Add hand to custom range",
    "  [accent]D[/accent]                 Remove hand from custom range",
    "  [accent]C[/accent]                 Clear custom range",
    "",
    "[bold]Chart Operations:[/bold]",
    "  [accent]Ctrl+L[/accent]            Load chart",
    "  [accent]Ctrl+S[/accent]            Save chart",
    "  [accent]Ctrl+C[/accent]            Compare charts",
    "  [accent]Ctrl+E[/accent]            Export chart",
    "  [accent]Ctrl+R[/accent]            Refresh data",
    "",
    "[bold]Position Shortcuts:[/bold]",
    "  [accent]1[/accent] UTG   [accent]4[/accent] BTN",
    "  [accent]2[/accent] MP    [accent]5[/accent] SB",
    "  [accent]3[/accent] CO    [accent]6[/accent] BB",
    "",
    "[bold]Tab Navigation:[/bold]",
    "  [accent]Ctrl+T[/accent]            New chart tab",
    "  [accent]Ctrl+W[/accent]            Close current tab",
    "  [accent]Ctrl+1[/accent]            Switch to main chart",
    "  [accent]Ctrl+2[/accent]            Switch to statistics",
    "  [accent]Ctrl+3[/accent]            Switch to notes",
    "",
    "[bold]General:[/bold]",
    "  [accent]H[/accent]                 Show/hide this help",
    "  [accent]Q[/accent]                 Quit application",
    "",
    "[dim]Press H or Escape to close this help dialog[/dim]"
]

# Export Formats
SUPPORTED_EXPORT_FORMATS = ["json", "csv", "txt"]
SUPPORTED_IMPORT_FORMATS = ["json", "simple", "pio", "gto_wizard"]

# UI Dimensions
DEFAULT_DIALOG_WIDTH = 60
DEFAULT_DIALOG_HEIGHT = 25
HELP_DIALOG_WIDTH = 80
HELP_DIALOG_HEIGHT = 25

# Performance Settings
RENDER_CACHE_SIZE = 100
STATS_CACHE_SIZE = 50
SEARCH_CACHE_SIZE = 20

# File Extensions
CHART_EXTENSIONS = {
    "json": ".json",
    "csv": ".csv",
    "txt": ".txt"
}

# Color Schemes
ACTION_COLORS = {
    "raise": ("red", "bright_red"),
    "call": ("green", "bright_green"),
    "fold": ("dim white", "bright_black"),
    "mixed": ("yellow", "bright_yellow"),
    "bluff": ("blue", "bright_blue")
}

FREQUENCY_COLORS = [
    (80, "green"),
    (60, "yellow"),
    (40, "red")
]

EV_COLORS = [
    (1.0, "green"),
    (0, "yellow")
]
