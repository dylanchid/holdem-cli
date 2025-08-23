"""
Quiz screen for the TUI application.

This screen provides an interactive quiz interface for testing
poker chart knowledge with different question types and scoring.
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Button, Label, ProgressBar
from textual.screen import Screen
from textual.reactive import reactive
from textual import events
from textual.message import Message
from textual.timer import Timer

from ...quiz import ChartQuizApp
from ...tui.widgets.matrix import create_sample_range
from ...tui.core.state import ChartViewerState
from ...tui.core.events import get_event_bus, EventType, create_quiz_answer_event
from typing import Dict, Optional, List, Any
import random


class QuizScreen(Screen):
    """
    Interactive quiz screen for chart training.

    Features:
    - Multiple quiz modes (flashcard, multiple choice, input)
    - Real-time scoring and progress tracking
    - Question generation from chart data
    - Performance analytics
    """

    CSS = """
    QuizScreen {
        layout: vertical;
    }

    .quiz-container {
        layout: vertical;
        height: 100%;
        padding: 1;
        margin: 0;
    }

    .quiz-header {
        height: 4;
        border: solid $primary;
        background: $surface;
        padding: 1;
        margin: 0 0 1 0;
    }

    .question-section {
        height: 6;
        border: solid $primary;
        background: $surface;
        padding: 1;
        margin: 0 0 1 0;
    }

    .answer-section {
        height: 8;
        border: solid $primary;
        background: $surface;
        padding: 1;
        margin: 0 0 1 0;
    }

    .results-section {
        height: 6;
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

    .quiz-button {
        width: 1fr;
        margin: 0 1;
    }

    .quiz-button.correct {
        background: $success;
        color: $text;
    }

    .quiz-button.incorrect {
        background: $error;
        color: $text;
    }

    .section-title {
        text-style: bold;
        color: $primary;
        margin: 0 0 1 0;
    }

    .progress-container {
        width: 100%;
        margin: 1 0;
    }
    """

    # Reactive state
    quiz_mode: reactive[str] = reactive("flashcard")
    current_question: reactive[Optional[Dict]] = reactive(None)
    score: reactive[int] = reactive(0)
    total_questions: reactive[int] = reactive(0)
    current_streak: reactive[int] = reactive(0)
    is_answering: reactive[bool] = reactive(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state = ChartViewerState()
        self.event_bus = get_event_bus()
        self.chart_data = create_sample_range()  # Default chart data
        self.question_history: List[Dict] = []
        self._auto_advance_timer: Optional[Timer] = None
        self._setup_event_handlers()

    def _setup_event_handlers(self):
        """Setup event handlers for the quiz."""
        self.event_bus.subscribe(EventType.QUIZ_ANSWER_SELECTED, self._on_answer_selected)
        self.event_bus.subscribe(EventType.QUIZ_QUESTION_REQUESTED, self._on_question_requested)

    def _on_answer_selected(self, event):
        """Handle answer selection events."""
        if hasattr(event, 'user_answer') and hasattr(event, 'correct_answer'):
            self._process_answer(event.user_answer, event.correct_answer)

    def _on_question_requested(self, event):
        """Handle new question requests."""
        self._generate_question()

    def compose(self) -> ComposeResult:
        """Compose the quiz screen layout."""
        yield Header()

        with Container(classes="quiz-container"):
            # Quiz header with progress and score
            with Vertical(classes="quiz-header"):
                yield Label("🎯 Poker Chart Quiz", classes="section-title")
                with Horizontal():
                    yield Static("", id="quiz_progress")
                    yield Static("", id="quiz_score")
                yield ProgressBar(id="progress_bar", total=10, show_eta=False, classes="progress-container")

            # Question section
            with Vertical(classes="question-section"):
                yield Label("Question:", classes="section-title")
                yield Static("", id="question_text")

            # Answer section
            with Vertical(classes="answer-section"):
                yield Label("Select Action:", classes="section-title")
                with Horizontal():
                    yield Button("Raise", id="raise_btn", variant="error", classes="quiz-button", disabled=True)
                    yield Button("Call", id="call_btn", variant="success", classes="quiz-button", disabled=True)
                    yield Button("Fold", id="fold_btn", variant="default", classes="quiz-button", disabled=True)
                    yield Button("Mixed", id="mixed_btn", variant="warning", classes="quiz-button", disabled=True)

            # Results section
            with Vertical(classes="results-section"):
                yield Label("Feedback:", classes="section-title")
                yield Static("", id="feedback_text")

            # Controls section
            with Vertical(classes="controls-section"):
                yield Label("Controls:", classes="section-title")
                with Horizontal():
                    yield Button("Start Quiz", id="start_quiz", variant="primary")
                    yield Button("Next Question", id="next_question", variant="default", disabled=True)
                    yield Button("Show Answer", id="show_answer", variant="warning", disabled=True)
                    yield Button("End Quiz", id="end_quiz", variant="error", disabled=True)

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the quiz screen."""
        self.title = "Holdem CLI - Chart Quiz"
        self.sub_title = "Test your poker knowledge"

        self._update_display()

    def _update_display(self):
        """Update all display elements."""
        self._update_progress()
        self._update_score()
        self._update_question()
        self._update_buttons()

    def _update_progress(self):
        """Update progress display."""
        progress_text = f"Progress: {self.total_questions}/10 questions"
        try:
            progress_widget = self.query_one("#quiz_progress", Static)
            progress_widget.update(progress_text)

            # Update progress bar
            progress_bar = self.query_one("#progress_bar", ProgressBar)
            progress_bar.progress = self.total_questions
        except:
            pass

    def _update_score(self):
        """Update score display."""
        accuracy = (self.score / max(self.total_questions, 1)) * 100
        score_text = f"Score: {self.score}/{self.total_questions} ({accuracy:.1f}%) | Streak: {self.current_streak}"
        try:
            score_widget = self.query_one("#quiz_score", Static)
            score_widget.update(score_text)
        except:
            pass

    def _update_question(self):
        """Update question display."""
        if self.current_question:
            scenario = self.current_question.get("scenario", "Unknown scenario")
            hand = self.current_question.get("hand", "Unknown hand")
            question_text = f"Scenario: {scenario}\nYour hand: {hand}\n\nWhat's your action?"
        else:
            question_text = "Press 'Start Quiz' to begin testing your knowledge!"

        try:
            question_widget = self.query_one("#question_text", Static)
            question_widget.update(question_text)
        except:
            pass

    def _update_buttons(self):
        """Update button states."""
        has_question = self.current_question is not None
        is_answering = self.is_answering

        try:
            # Answer buttons
            for btn_id in ["raise_btn", "call_btn", "fold_btn", "mixed_btn"]:
                button = self.query_one(f"#{btn_id}", Button)
                button.disabled = not has_question or not is_answering

            # Control buttons
            self.query_one("#start_quiz", Button).disabled = has_question
            self.query_one("#next_question", Button).disabled = is_answering or not has_question
            self.query_one("#show_answer", Button).disabled = not has_question or not is_answering
            self.query_one("#end_quiz", Button).disabled = not has_question

        except:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id

        if button_id == "start_quiz":
            self._start_quiz()
        elif button_id == "next_question":
            self._generate_question()
        elif button_id == "show_answer":
            self._show_answer()
        elif button_id == "end_quiz":
            self._end_quiz()
        elif button_id in ["raise_btn", "call_btn", "fold_btn", "mixed_btn"]:
            if self.is_answering:
                self._handle_answer(button_id.replace("_btn", ""))

    def _start_quiz(self):
        """Start a new quiz session."""
        self.score = 0
        self.total_questions = 0
        self.current_streak = 0
        self.question_history.clear()
        self.is_answering = False

        # Generate first question
        self._generate_question()

        self.notify("🧠 Quiz started! Select the correct action for each scenario.", severity="information")

    def _generate_question(self):
        """Generate a new quiz question."""
        if self.total_questions >= 10:
            self._end_quiz()
            return

        # Pick a random hand from the chart
        hands = list(self.chart_data.keys())
        if not hands:
            return

        hand = random.choice(hands)
        action = self.chart_data[hand]

        # Create question scenario
        scenarios = [
            "You're on the button vs big blind 3-bet",
            "You're in the cutoff facing a raise",
            "You're under the gun in a cash game",
            "You're in the small blind vs button raise",
            "You're in the big blind facing a raise",
            "You're in middle position with multiple limpers"
        ]

        scenario = random.choice(scenarios)

        self.current_question = {
            "hand": hand,
            "scenario": scenario,
            "correct_action": action.action.value,
            "explanation": f"GTO play is {action.action.value} with {action.frequency:.0%} frequency"
        }

        self.is_answering = True
        self._clear_feedback()
        self._update_display()

    def _handle_answer(self, user_answer: str):
        """Handle user answer selection."""
        if not self.current_question or not self.is_answering:
            return

        correct_answer = self.current_question["correct_action"]
        is_correct = user_answer == correct_answer

        # Update score
        self.total_questions += 1
        if is_correct:
            self.score += 1
            self.current_streak += 1
            feedback = f"✅ Correct! {self.current_question['explanation']}"
        else:
            self.current_streak = 0
            feedback = f"❌ Wrong. Correct answer: {correct_answer.title()}. {self.current_question['explanation']}"

        # Store question in history
        self.question_history.append({
            "question": self.current_question,
            "user_answer": user_answer,
            "correct": is_correct
        })

        # Update UI
        self.is_answering = False
        self._show_feedback(feedback, is_correct)

        # Auto-advance after delay
        self._schedule_auto_advance()

    def _show_feedback(self, feedback: str, is_correct: bool):
        """Show answer feedback."""
        try:
            feedback_widget = self.query_one("#feedback_text", Static)
            feedback_widget.update(feedback)

            # Highlight the correct button
            correct_action = self.current_question["correct_action"] if self.current_question else None
            if correct_action:
                correct_btn_id = f"{correct_action}_btn"
                try:
                    correct_button = self.query_one(f"#{correct_btn_id}", Button)
                    correct_button.add_class("correct")
                except:
                    pass

        except:
            pass

    def _clear_feedback(self):
        """Clear feedback display."""
        try:
            feedback_widget = self.query_one("#feedback_text", Static)
            feedback_widget.update("")

            # Remove button highlighting
            for btn_id in ["raise_btn", "call_btn", "fold_btn", "mixed_btn"]:
                try:
                    button = self.query_one(f"#{btn_id}", Button)
                    button.remove_class("correct")
                    button.remove_class("incorrect")
                except:
                    pass
        except:
            pass

    def _show_answer(self):
        """Show the correct answer without scoring."""
        if self.current_question:
            correct_answer = self.current_question["correct_action"]
            explanation = self.current_question["explanation"]
            feedback = f"💡 The correct answer is: {correct_answer.title()}\n{explanation}"
            self._show_feedback(feedback, True)

            self.is_answering = False
            self._schedule_auto_advance()

    def _schedule_auto_advance(self):
        """Schedule automatic advancement to next question."""
        if self._auto_advance_timer:
            self._auto_advance_timer.stop()

        self._auto_advance_timer = self.set_timer(3.0, self._generate_question)

    def _end_quiz(self):
        """End the current quiz session."""
        if self._auto_advance_timer:
            self._auto_advance_timer.stop()

        if self.total_questions > 0:
            accuracy = (self.score / self.total_questions) * 100
            max_streak = max([q.get("streak", 0) for q in self.question_history], default=0)

            results_text = ".1f"".1f"".1f"".1f"f"""
🎯 Quiz Complete!

Final Score: {self.score}/{self.total_questions} ({accuracy:.1f}%)
Max Streak: {max(self.current_streak, max_streak)}

Press 'Start Quiz' to try again!
            """.strip()

            self.notify(results_text, timeout=8)

        self.current_question = None
        self.is_answering = False
        self._clear_feedback()
        self._update_display()

    def _process_answer(self, user_answer: str, correct_answer: str):
        """Process an answer from event system (for integration)."""
        self._handle_answer(user_answer)

    def action_start_quiz(self):
        """Action to start quiz (keyboard shortcut)."""
        self._start_quiz()

    def action_next_question(self):
        """Action to advance to next question."""
        if not self.is_answering:
            self._generate_question()

    def action_show_answer(self):
        """Action to show correct answer."""
        if self.is_answering:
            self._show_answer()

    def action_end_quiz(self):
        """Action to end quiz."""
        self._end_quiz()

    def on_key(self, event: events.Key) -> None:
        """Handle keyboard input."""
        if event.key == "r":
            self.action_start_quiz()
        elif event.key == "n":
            self.action_next_question()
        elif event.key == "s":
            self.action_show_answer()
        elif event.key == "q":
            self.action_end_quiz()

    def get_screen_info(self) -> Dict[str, Any]:
        """Get information about the current quiz state."""
        return {
            "screen_type": "quiz",
            "quiz_mode": self.quiz_mode,
            "score": self.score,
            "total_questions": self.total_questions,
            "current_streak": self.current_streak,
            "has_active_question": self.current_question is not None,
            "is_answering": self.is_answering
        }


# Screen factory function
def create_quiz_screen(chart_data: Optional[Dict] = None, **kwargs) -> QuizScreen:
    """Create a configured quiz screen."""
    screen = QuizScreen(**kwargs)
    if chart_data:
        screen.chart_data = chart_data
    return screen
