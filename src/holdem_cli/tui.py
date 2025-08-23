#!/usr/bin/env python3
"""
TUI (Text User Interface) entry point for Holdem CLI.

This module provides the unified TUI application with mode selection interface.
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Button, Label, Static
from textual.screen import Screen
from textual import events
from textual.binding import Binding

from .storage import init_database
from .charts.app import ChartViewerApp
from .charts.tui.screens.quiz_menu import QuizMenuScreen
from .charts.tui.screens.quiz import QuizScreen
from .charts.tui.screens.equity_calculator import EquityCalculatorScreen
from .charts.tui.screens.simulator import SimulatorScreen
from .charts.tui.screens.profile_manager import ProfileManagerScreen
from .charts.tui.screens.chart_management import ChartManagementScreen
from .charts.tui.screens.comparison import ComparisonScreen


class ModeSelectionScreen(Screen):
    """Main menu screen for selecting application mode."""

    CSS = """
    ModeSelectionScreen {
        layout: vertical;
        align: center middle;
        padding: 2;
    }

    .title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 3;
        width: 100%;
    }

    .subtitle {
        text-align: center;
        color: $secondary;
        margin-bottom: 4;
        width: 100%;
    }

    .mode-grid {
        layout: grid;
        grid-size: 2 4;
        grid-gutter: 2;
        width: 60;
        height: 25;
        margin: 2;
        align: center middle;
    }

    .mode-button {
        width: 25;
        height: 6;
        background: $surface;
        border: solid $primary;
        padding: 1;
        text-align: center;
        content-align: center middle;
    }

    .mode-button:hover {
        background: $primary;
        color: $surface;
    }

    .mode-title {
        text-style: bold;
        margin-bottom: 1;
    }

    .mode-description {
        opacity: 0.8;
    }

    .footer-text {
        text-align: center;
        color: $text-muted;
        margin-top: 2;
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the mode selection screen."""
        yield Header()

        yield Label("🃏 Holdem CLI - Poker Training Tool", classes="title")
        yield Label("Choose your training mode", classes="subtitle")

        with Container(classes="mode-grid"):
            # Chart Analysis
            with Vertical(classes="mode-button"):
                yield Label("📊 Chart Analysis", classes="mode-title")
                yield Label("View and analyze GTO charts", classes="mode-description")
                yield Button("Enter Charts", id="charts", variant="primary")

            # Quiz Mode
            with Vertical(classes="mode-button"):
                yield Label("🎯 Quiz Mode", classes="mode-title")
                yield Label("Test your poker knowledge", classes="mode-description")
                yield Button("Start Quiz", id="quiz", variant="primary")

            # Equity Calculator
            with Vertical(classes="mode-button"):
                yield Label("🧮 Equity Calculator", classes="mode-title")
                yield Label("Calculate hand vs hand equity", classes="mode-description")
                yield Button("Calculate Equity", id="equity", variant="primary")

            # Simulator
            with Vertical(classes="mode-button"):
                yield Label("🎲 Simulator", classes="mode-title")
                yield Label("Practice against AI opponents", classes="mode-description")
                yield Button("Start Simulation", id="simulator", variant="primary")

            # Chart Quiz
            with Vertical(classes="mode-button"):
                yield Label("📈 Chart Quiz", classes="mode-title")
                yield Label("Test your chart knowledge", classes="mode-description")
                yield Button("Chart Quiz", id="chart-quiz", variant="primary")

            # Chart Comparison
            with Vertical(classes="mode-button"):
                yield Label("⚖️ Compare Charts", classes="mode-title")
                yield Label("Compare multiple charts side by side", classes="mode-description")
                yield Button("Compare Charts", id="comparison", variant="primary")

            # Profile Management
            with Vertical(classes="mode-button"):
                yield Label("👤 Profile", classes="mode-title")
                yield Label("Manage your training data", classes="mode-description")
                yield Button("Open Profile", id="profile", variant="primary")

        yield Static("Use arrow keys to navigate • Press Enter to select • Press Q to quit", classes="footer-text")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id

        if button_id == "charts":
            self.app.push_screen("chart_management")
        elif button_id == "quiz":
            self.app.push_screen("quiz_menu")
        elif button_id == "equity":
            self.app.push_screen("equity_calculator")
        elif button_id == "simulator":
            self.app.push_screen("simulator")
        elif button_id == "chart-quiz":
            self.app.push_screen("quiz")
        elif button_id == "comparison":
            self.app.push_screen("comparison")
        elif button_id == "profile":
            self.app.push_screen("profile_manager")

    def on_key(self, event: events.Key) -> None:
        """Handle keyboard input."""
        if event.key == "q":
            self.app.exit()


class HoldemApp(App):
    """Unified main application for Holdem CLI."""

    CSS = """
    HoldemApp {
        background: $background;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("escape", "quit", "Quit"),
    ]

    SCREENS = {
        "mode_selection": ModeSelectionScreen,
        "chart_management": ChartManagementScreen,
        "quiz_menu": QuizMenuScreen,
        "quiz": QuizScreen,  # Direct quiz screen for chart-specific quizzes
        "equity_calculator": EquityCalculatorScreen,
        "simulator": SimulatorScreen,
        "profile_manager": ProfileManagerScreen,
        "comparison": ComparisonScreen,  # Chart comparison functionality
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = init_database()

    def on_mount(self) -> None:
        """Initialize the application."""
        self.title = "Holdem CLI - Poker Training Tool"
        self.sub_title = "Unified Interface"

        # Push the mode selection screen
        self.push_screen("mode_selection")

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()


def launch_tui():
    """Launch the TUI application."""
    app = HoldemApp()
    app.run()
