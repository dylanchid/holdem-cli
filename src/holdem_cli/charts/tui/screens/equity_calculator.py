"""
Equity calculator screen for hand vs hand analysis.

This screen provides an interactive interface for calculating poker hand equity,
migrating the CLI equity functionality to a user-friendly TUI.
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import Header, Footer, Button, Label, Input, Static, TextArea, DataTable
from textual.screen import Screen
from textual import events
from textual.binding import Binding
from datetime import datetime

from ....services.holdem_service import get_holdem_service
from ....services.state_manager import get_app_state
from ..widgets.help_dialog import HelpDialog


class EquityCalculatorScreen(Screen):
    """Interactive equity calculator screen."""

    CSS = """
    EquityCalculatorScreen {
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

    .input-section {
        width: 100%;
        margin: 1 0;
        border: solid $primary;
        padding: 1;
        background: $surface;
    }

    .input-row {
        layout: horizontal;
        margin: 1 0;
        align: center middle;
    }

    .input-label {
        width: 15;
        margin-right: 2;
    }

    .input-field {
        width: 20;
        margin-right: 2;
    }

    .calculate-button {
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
        height: 15;
    }

    .results-title {
        text-style: bold;
        color: $secondary;
        margin-bottom: 1;
    }

    .results-content {
        height: 10;
        overflow: auto;
    }

    .hand-equity {
        layout: horizontal;
        margin: 1 0;
        align: center middle;
    }

    .hand-label {
        width: 10;
        margin-right: 2;
    }

    .equity-bar {
        width: 60;
        height: 1;
        background: grey;
        margin: 0 1;
    }

    .equity-fill {
        height: 1;
        background: $primary;
    }

    .equity-text {
        width: 10;
        text-align: right;
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
        Binding("f1", "help", "Show Help"),
        Binding("f5", "calculate", "Calculate Equity"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app_state = get_app_state()
        self.hand1 = ""
        self.hand2 = ""
        self.board = ""
        self.iterations = 25000
        self.seed = None
        self.output_json = False
        self.last_result = None
        self.help_dialog = None

    def compose(self) -> ComposeResult:
        """Compose the equity calculator screen."""
        yield Header()

        yield Label("🧮 Equity Calculator", classes="title")

        # Input section
        with Vertical(classes="input-section"):
            yield Label("📝 Input", classes="input-title")

            # Hand 1 input
            with Horizontal(classes="input-row"):
                yield Label("Hand 1:", classes="input-label")
                yield Input(
                    placeholder="e.g., AsKs, AhAd",
                    value=self.hand1,
                    id="hand1_input",
                    classes="input-field"
                )
                yield Label("First player's hole cards", classes="input-help")

            # Hand 2 input
            with Horizontal(classes="input-row"):
                yield Label("Hand 2:", classes="input-label")
                yield Input(
                    placeholder="e.g., 7h7d, QcJd",
                    value=self.hand2,
                    id="hand2_input",
                    classes="input-field"
                )
                yield Label("Second player's hole cards", classes="input-help")

            # Board input
            with Horizontal(classes="input-row"):
                yield Label("Board:", classes="input-label")
                yield Input(
                    placeholder="e.g., 2c7s, 2c7s9h",
                    value=self.board,
                    id="board_input",
                    classes="input-field"
                )
                yield Label("Community cards (optional)", classes="input-help")

            # Iterations input
            with Horizontal(classes="input-row"):
                yield Label("Iterations:", classes="input-label")
                yield Input(
                    placeholder="25000",
                    value=str(self.iterations),
                    id="iterations_input",
                    classes="input-field"
                )
                yield Label("Monte Carlo simulation count", classes="input-help")

            # Random seed input
            with Horizontal(classes="input-row"):
                yield Label("Random Seed:", classes="input-label")
                yield Input(
                    placeholder="Random",
                    value="",
                    id="seed_input",
                    classes="input-field"
                )
                yield Label("Optional seed for deterministic results", classes="input-help")

            # Output format toggle
            with Horizontal(classes="input-row"):
                yield Label("Output Format:", classes="input-label")
                yield Button("📄 Human-readable", id="format_toggle", variant="primary", classes="input-field")
                yield Label("Click to toggle JSON output", classes="input-help")

            # Calculate button
            yield Button("🧮 Calculate Equity", id="calculate", variant="success", classes="calculate-button")

        # Results section
        with Vertical(classes="results-section"):
            yield Label("📊 Results", classes="results-title")
            yield Static("Enter hand details above and press Calculate", id="results_content", classes="results-content")

        yield Static("Press F1 for help • F5 to calculate • Escape to go back", classes="footer-text")

        # Help dialog
        self.help_dialog = HelpDialog(id="help_dialog", classes="help-dialog")
        self.help_dialog.set_context("equity_calculator")
        yield self.help_dialog

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        if button_id == "calculate":
            self._calculate_equity()
        elif button_id == "format_toggle":
            self._toggle_output_format()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes."""
        input_id = event.input.id
        value = event.value

        if input_id == "hand1_input":
            self.hand1 = value
        elif input_id == "hand2_input":
            self.hand2 = value
        elif input_id == "board_input":
            self.board = value
        elif input_id == "iterations_input":
            try:
                self.iterations = int(value) if value else 25000
            except ValueError:
                self.iterations = 25000
        elif input_id == "seed_input":
            try:
                self.seed = int(value) if value else None
            except ValueError:
                self.seed = None

    def action_calculate(self) -> None:
        """Calculate equity using keyboard shortcut."""
        self._calculate_equity()

    def action_help(self) -> None:
        """Show help dialog."""
        if self.help_dialog:
            self.help_dialog.toggle()

    def _toggle_output_format(self) -> None:
        """Toggle between human-readable and JSON output formats."""
        self.output_json = not self.output_json
        button = self.query_one("#format_toggle", Button)
        if self.output_json:
            button.label = "📋 JSON Format"
        else:
            button.label = "📄 Human-readable"
        button.refresh()

    def _calculate_equity(self) -> None:
        """Calculate equity between the two hands."""
        try:
            # Validate inputs
            if not self.hand1 or not self.hand2:
                self.notify("❌ Please enter both hands", severity="error")
                return

            # Validate hand format
            if not self._validate_hand_format(self.hand1):
                self.notify("❌ Invalid hand format for Hand 1. Use format like 'AsKs' or 'AhAd'", severity="error")
                return

            if not self._validate_hand_format(self.hand2):
                self.notify("❌ Invalid hand format for Hand 2. Use format like '7h7d' or 'QcJd'", severity="error")
                return

            if self.board and not self._validate_hand_format(self.board, allow_multiple=True):
                self.notify("❌ Invalid board format. Use format like '2c7s' or '2c7s9h'", severity="error")
                return

            # Show progress indicator
            self.notify("🔄 Calculating equity...", severity="information")

            with get_holdem_service() as service:
                result = service.calculate_equity(
                    self.hand1,
                    self.hand2,
                    self.board if self.board else None,
                    self.iterations
                )

                if result['success']:
                    self.last_result = result
                    self._display_results(result)

                    # Save to state for tracking
                    self.app_state.add_notification("✅ Equity calculation completed", "information")

                    # Track usage in state
                    equity_history = self.app_state.get('equity_history', [])
                    equity_history.append({
                        'timestamp': datetime.now(),
                        'hand1': result['hand1'],
                        'hand2': result['hand2'],
                        'board': result['board'],
                        'iterations': result['iterations'],
                        'equity': result['equity']
                    })
                    self.app_state.set('equity_history', equity_history[-50:])  # Keep last 50

                else:
                    self.app_state.add_notification(f"❌ {result['error']}", "error")

        except Exception as e:
            self.notify(f"❌ Error calculating equity: {e}", severity="error")

    def _validate_hand_format(self, hand: str, allow_multiple: bool = False) -> bool:
        """
        Validate poker hand format.

        Args:
            hand: The hand string to validate
            allow_multiple: Whether to allow multiple cards (for board)

        Returns:
            bool: True if format is valid
        """
        if allow_multiple:
            # For board, allow 0, 3, 4, or 5 cards
            cards = hand.split() if ' ' in hand else [hand[i:i+2] for i in range(0, len(hand), 2)]
            if len(cards) not in [3, 4, 5]:
                return False
        else:
            # For hole cards, expect exactly 2 cards
            if len(hand) != 4:
                return False
            cards = [hand[:2], hand[2:]]

        # Validate each card
        valid_ranks = set('23456789TJQKA')
        valid_suits = set('cdhs')

        for card in cards:
            if len(card) != 2:
                return False
            rank, suit = card[0].upper(), card[1].lower()
            if rank not in valid_ranks or suit not in valid_suits:
                return False

        # Check for duplicate cards
        card_set = set()
        for card in cards:
            if card.upper() in card_set:
                return False
            card_set.add(card.upper())

        return True

    def _display_results(self, result: dict) -> None:
        """Display equity calculation results."""
        try:
            if self.output_json:
                # JSON output format
                import json
                json_data = {
                    "hand1": result['hand1'],
                    "hand2": result['hand2'],
                    "board": result['board'] or "",
                    "iterations": result['iterations'],
                    "equity": result['equity']
                }
                json_output = json.dumps(json_data, indent=2)
                results_content = f"JSON Output:\\n{json_output}"
            else:
                # Human-readable output format (matching CLI)
                equity_data = result['equity']
                hand1_equity = equity_data['hand1_win']
                hand2_equity = equity_data['hand2_win']
                tie_rate = equity_data['hand1_tie']

                lines = [
                    f"\\nEquity calculation:",
                    f"Hand 1: {result['hand1']}",
                    f"Hand 2: {result['hand2']}",
                ]
                if result['board']:
                    lines.append(f"Board:  {result['board']}")
                lines.extend([
                    f"Iterations: {result['iterations']:,}",
                    "",
                    ".1f"                    ".1f"                    ".1f"
                ])

                results_content = "\\n".join(lines)

            # Update results display
            results_widget = self.query_one("#results_content", Static)
            results_widget.update(results_content)

        except Exception as e:
            self.notify(f"❌ Error displaying results: {e}", severity="error")

    def action_back(self) -> None:
        """Go back to the main menu."""
        self.app.pop_screen()

    def on_key(self, event: events.Key) -> None:
        """Handle keyboard input."""
        if event.key == "escape":
            self.action_back()
