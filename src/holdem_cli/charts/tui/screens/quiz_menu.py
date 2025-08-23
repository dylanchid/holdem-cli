"""
Quiz menu screen for selecting different quiz types.

This screen provides an interface for users to select and configure
different types of poker quizzes available in the application.
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import Header, Footer, Button, Label, Input, Select, Static, RadioSet, RadioButton
from textual.screen import Screen
from textual import events
from textual.binding import Binding

from ....services.holdem_service import get_holdem_service


class QuizMenuScreen(Screen):
    """Screen for selecting and configuring quizzes."""

    CSS = """
    QuizMenuScreen {
        layout: vertical;
        align: center middle;
        padding: 2;
    }

    .title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 2;
        width: 100%;
    }

    .quiz-grid {
        layout: grid;
        grid-size: 1;
        grid-gutter: 1;
        width: 50;
        margin: 2 auto;
    }

    .quiz-option {
        width: 100%;
        height: 8;
        background: $surface;
        border: solid $primary;
        padding: 1;
        margin: 1 0;
    }

    .quiz-option:hover {
        background: $primary;
        color: $surface;
    }

    .quiz-title {
        text-style: bold;
        margin-bottom: 1;
    }

    .quiz-description {
        font-size: 80%;
        opacity: 0.8;
        margin-bottom: 1;
    }

    .config-section {
        width: 50;
        margin: 2 auto;
        border: solid $secondary;
        padding: 1;
        background: $background;
    }

    .config-title {
        text-style: bold;
        color: $secondary;
        margin-bottom: 1;
    }

    .config-row {
        layout: horizontal;
        margin: 1 0;
        align: center middle;
    }

    .config-label {
        width: 20;
        margin-right: 2;
    }

    .config-input {
        width: 30;
    }

    .start-button {
        width: 20;
        margin: 2 auto;
        background: $success;
        color: $surface;
    }

    .footer-text {
        text-align: center;
        color: grey;
        margin-top: 2;
        width: 100%;
    }
    """

    BINDINGS = [
        Binding("escape", "back", "Back to Main Menu"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_quiz = "hand_ranking"
        self.profile_name = "default"
        self.question_count = 10
        self.difficulty = "adaptive"

    def compose(self) -> ComposeResult:
        """Compose the quiz menu screen."""
        yield Header()

        yield Label("🎯 Quiz Selection", classes="title")

        with Container(classes="quiz-grid"):
            # Hand Ranking Quiz
            with Vertical(classes="quiz-option"):
                yield Label("🃏 Hand Ranking Quiz", classes="quiz-title")
                yield Label("Test your knowledge of poker hand rankings", classes="quiz-description")
                yield Button("Select Hand Ranking", id="hand_ranking", variant="primary")

            # Pot Odds Quiz
            with Vertical(classes="quiz-option"):
                yield Label("💰 Pot Odds Quiz", classes="quiz-title")
                yield Label("Practice calculating pot odds and making decisions", classes="quiz-description")
                yield Button("Select Pot Odds", id="pot_odds", variant="primary")

        # Configuration section
        with Vertical(classes="config-section"):
            yield Label("⚙️ Quiz Configuration", classes="config-title")

            # Profile selection
            with Horizontal(classes="config-row"):
                yield Label("Profile:", classes="config-label")
                yield Input(
                    placeholder="Enter profile name",
                    value=self.profile_name,
                    id="profile_input",
                    classes="config-input"
                )

            # Question count
            with Horizontal(classes="config-row"):
                yield Label("Questions:", classes="config-label")
                yield Select(
                    options=[
                        ("5", "5"),
                        ("10", "10"),
                        ("20", "20"),
                        ("50", "50")
                    ],
                    value="10",
                    id="count_select",
                    classes="config-input"
                )

            # Difficulty level
            with Horizontal(classes="config-row"):
                yield Label("Difficulty:", classes="config-label")
                yield Select(
                    options=[
                        ("adaptive", "Adaptive"),
                        ("easy", "Easy"),
                        ("medium", "Medium"),
                        ("hard", "Hard")
                    ],
                    value="adaptive",
                    id="difficulty_select",
                    classes="config-input"
                )

            # Start button
            yield Button("🚀 Start Quiz", id="start_quiz", variant="success", classes="start-button")

        yield Static("Use arrow keys to navigate • Press Enter to select • Press Escape to go back", classes="footer-text")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id

        if button_id == "hand_ranking":
            self.selected_quiz = "hand_ranking"
            self._update_quiz_selection()
        elif button_id == "pot_odds":
            self.selected_quiz = "pot_odds"
            self._update_quiz_selection()
        elif button_id == "start_quiz":
            self._start_quiz()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes."""
        if event.input.id == "profile_input":
            self.profile_name = event.value or "default"

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle select changes."""
        if event.select.id == "count_select":
            self.question_count = int(event.value)
        elif event.select.id == "difficulty_select":
            self.difficulty = event.value

    def _update_quiz_selection(self) -> None:
        """Update the visual selection of quiz types."""
        # Remove selection styling from all quiz options
        for widget in self.query(".quiz-option"):
            widget.remove_class("selected")

        # Add selection styling to the selected quiz
        selected_option = self.query(f"#quiz_{self.selected_quiz}")
        if selected_option:
            selected_option.add_class("selected")

    def _start_quiz(self) -> None:
        """Start the selected quiz."""
        try:
            with get_holdem_service() as service:
                # Check if profile exists
                user = service.db.get_user(self.profile_name)
                if not user:
                    # Create profile if it doesn't exist
                    success, message = service.create_profile(self.profile_name)
                    if not success:
                        self.notify(f"❌ {message}", severity="error")
                        return

                # Start the appropriate quiz
                if self.selected_quiz == "hand_ranking":
                    result = service.run_hand_ranking_quiz(
                        self.profile_name,
                        self.question_count,
                        self.difficulty
                    )
                elif self.selected_quiz == "pot_odds":
                    result = service.run_pot_odds_quiz(
                        self.profile_name,
                        self.question_count,
                        self.difficulty
                    )
                else:
                    self.notify("❌ Unknown quiz type", severity="error")
                    return

                # Display results
                if result['success']:
                    score = result['score']
                    self.notify(
                        f"✅ Quiz completed! Score: {result['correct']}/{result['total']} ({score:.1f}%)",
                        severity="information",
                        timeout=5
                    )
                else:
                    self.notify(f"❌ Quiz failed: {result['error']}", severity="error")

        except Exception as e:
            self.notify(f"❌ Error starting quiz: {e}", severity="error")

    def action_back(self) -> None:
        """Go back to the main menu."""
        self.app.pop_screen()

    def on_key(self, event: events.Key) -> None:
        """Handle keyboard input."""
        if event.key == "escape":
            self.action_back()

