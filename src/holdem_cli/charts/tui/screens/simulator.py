"""
Poker simulator screen for practice games.

This screen provides an interactive interface for running poker simulations
against AI opponents, migrating the CLI simulation functionality to TUI.
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import Header, Footer, Button, Label, Input, Static, Select, TextArea
from textual.screen import Screen
from textual import events
from textual.binding import Binding

from ....services.holdem_service import get_holdem_service


class SimulatorScreen(Screen):
    """Interactive poker simulator screen."""

    CSS = """
    SimulatorScreen {
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

    .config-section {
        width: 100%;
        margin: 1 0;
        border: solid $primary;
        padding: 1;
        background: $surface;
    }

    .config-row {
        layout: horizontal;
        margin: 1 0;
        align: center middle;
    }

    .config-label {
        width: 15;
        margin-right: 2;
    }

    .config-input {
        width: 25;
        margin-right: 2;
    }

    .simulate-button {
        width: 20;
        background: $success;
        color: $surface;
        margin: 1 auto;
    }

    .results-section {
        width: 100%;
        margin: 1 0;
        border: solid $secondary;
        padding: 1;
        background: $background;
        height: 20;
    }

    .results-title {
        text-style: bold;
        color: $secondary;
        margin-bottom: 1;
    }

    .results-content {
        height: 15;
        overflow: auto;
        background: $surface;
        padding: 1;
        border: solid grey;
    }

    .game-result {
        margin: 1 0;
        padding: 1;
        border: solid $primary;
        background: $background;
    }

    .winner-announcement {
        text-style: bold;
        color: $success;
        margin-bottom: 1;
    }

    .loser-announcement {
        color: $error;
        margin-bottom: 1;
    }

    .hand-info {
        layout: horizontal;
        margin: 1 0;
    }

    .hand-label {
        width: 10;
        margin-right: 2;
    }

    .cards {
        color: $primary;
        text-style: bold;
    }

    .board-cards {
        color: $secondary;
        margin: 1 0;
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
        Binding("f5", "simulate", "Run Simulation"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.profile_name = "default"
        self.ai_level = "easy"
        self.export_hand = None
        self.export_format = "json"
        self.last_result = None

    def compose(self) -> ComposeResult:
        """Compose the simulator screen."""
        yield Header()

        yield Label("🎲 Poker Simulator", classes="title")

        # Configuration section
        with Vertical(classes="config-section"):
            yield Label("⚙️ Configuration", classes="config-title")

            # Profile selection
            with Horizontal(classes="config-row"):
                yield Label("Profile:", classes="config-label")
                yield Input(
                    placeholder="Enter profile name",
                    value=self.profile_name,
                    id="profile_input",
                    classes="config-input"
                )

            # AI difficulty
            with Horizontal(classes="config-row"):
                yield Label("AI Level:", classes="config-label")
                yield Select(
                    options=[
                        ("easy", "Easy"),
                        ("medium", "Medium"),
                        ("hard", "Hard")
                    ],
                    value="easy",
                    id="ai_level_select",
                    classes="config-input"
                )

            # Export configuration
            with Horizontal(classes="config-row"):
                yield Label("Export File:", classes="config-label")
                yield Input(
                    placeholder="Optional export filename",
                    value="",
                    id="export_input",
                    classes="config-input"
                )

            # Export format
            with Horizontal(classes="config-row"):
                yield Label("Export Format:", classes="config-label")
                yield Select(
                    options=[
                        ("json", "JSON"),
                        ("txt", "Text")
                    ],
                    value="json",
                    id="format_select",
                    classes="config-input"
                )

            # Simulate button
            yield Button("🎯 Start Simulation", id="simulate", variant="success", classes="simulate-button")

        # Results section
        with Vertical(classes="results-section"):
            yield Label("🎮 Simulation Results", classes="results-title")
            yield Static("Press 'Start Simulation' to begin a practice hand", id="results_content", classes="results-content")

        yield Static("Press F5 to simulate • Press Escape to go back", classes="footer-text")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "simulate":
            self._run_simulation()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes."""
        if event.input.id == "profile_input":
            self.profile_name = event.value or "default"
        elif event.input.id == "export_input":
            self.export_hand = event.value if event.value else None

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle select changes."""
        if event.select.id == "ai_level_select":
            self.ai_level = event.value
        elif event.select.id == "format_select":
            self.export_format = event.value

    def action_simulate(self) -> None:
        """Run simulation using keyboard shortcut."""
        self._run_simulation()

    def _run_simulation(self) -> None:
        """Run a poker simulation against AI."""
        try:
            # Validate profile name
            if not self.profile_name or not self.profile_name.strip():
                self.notify("❌ Please enter a valid profile name", severity="error")
                return

            # Show progress indicator
            self.notify("🎲 Starting simulation...", severity="information")

            with get_holdem_service() as service:
                # Check if profile exists
                user = service.db.get_user(self.profile_name)
                if not user:
                    # Create profile if it doesn't exist
                    success, message = service.create_profile(self.profile_name)
                    if not success:
                        self.notify(f"❌ {message}", severity="error")
                        return
                    self.notify(f"👤 Created new profile: {self.profile_name}", severity="information")

                # Validate export filename if provided
                if self.export_hand and not self._validate_filename(self.export_hand):
                    self.notify("❌ Invalid export filename. Use only letters, numbers, and underscores", severity="error")
                    return

                # Run simulation with export parameters
                result = service.run_simulation(
                    self.profile_name,
                    self.ai_level,
                    self.export_hand,
                    self.export_format
                )

                if result['success']:
                    self.last_result = result
                    self._display_simulation_result(result['data'])

                    # Show export message if export was requested
                    if self.export_hand:
                        self.notify(f"✅ Simulation completed and exported to {self.export_hand}.{self.export_format}", severity="information")
                    else:
                        self.notify("✅ Simulation completed and saved", severity="information")
                else:
                    self.notify(f"❌ {result['error']}", severity="error")

        except Exception as e:
            self.notify(f"❌ Error running simulation: {e}", severity="error")

    def _validate_filename(self, filename: str) -> bool:
        """
        Validate filename for export.

        Args:
            filename: The filename to validate

        Returns:
            bool: True if filename is valid
        """
        import re
        # Allow only alphanumeric characters, underscores, and hyphens
        return bool(re.match(r'^[a-zA-Z0-9_-]+$', filename))

    def _display_simulation_result(self, data: dict) -> None:
        """Display simulation results in a user-friendly format."""
        try:
            winner = data['winner']
            pot_size = data['pot_size']
            player_cards = data['player_cards']
            ai_cards = data['ai_cards']
            board = data['board']
            action_history = data['action_history']
            final_hands = data['final_hands']

            # Create result content
            lines = []

            # Winner announcement
            if winner == "player":
                lines.append("🎉 YOU WIN!")
                lines.append(f"Pot: ${pot_size}")
            elif winner == "ai":
                lines.append("🤖 AI Wins")
                lines.append(f"Pot: ${pot_size}")
            else:
                lines.append("🤝 Split Pot!")
                lines.append(f"Pot: ${pot_size}")

            lines.extend([
                "",
                "🃏 Final Hands:",
                f"You: {' '.join(player_cards)}",
                f"AI: {' '.join(ai_cards)}",
            ])

            if board:
                lines.append(f"Board: {' '.join(board)}")

            lines.extend([
                "",
                "📊 Final Hand Values:",
            ])

            for player, hand_value in final_hands.items():
                lines.append(f"{player.title()}: {hand_value}")

            # Show action history if available
            if action_history:
                lines.extend([
                    "",
                    "🎯 Action History:",
                ])
                for action in action_history:
                    lines.append(f"• {action}")

            # Update results display
            results_widget = self.query_one("#results_content", Static)
            results_widget.update("\\n".join(lines))

        except Exception as e:
            self.notify(f"❌ Error displaying results: {e}", severity="error")

    def action_back(self) -> None:
        """Go back to the main menu."""
        self.app.pop_screen()

    def on_key(self, event: events.Key) -> None:
        """Handle keyboard input."""
        if event.key == "escape":
            self.action_back()
