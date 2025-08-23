"""
Quiz integration widget for TUI.

This widget provides integration between quiz functionality and the main
TUI interface, allowing users to launch quizzes from the main interface.
"""

from textual.widgets import Static, Button, Label, ProgressBar
from textual.containers import Vertical, Horizontal
from textual.reactive import reactive
from textual import on
from textual.message import Message
from typing import Dict, Optional, Any

from ..services.quiz_service import get_quiz_service, QuizMode, QuizDifficulty
from ..core.events import get_event_bus, EventType
from ..widgets.matrix import HandAction


class QuizLauncherWidget(Static):
    """
    Widget for launching quiz sessions from the main interface.

    Features:
    - Quick quiz launch buttons
    - Quiz mode selection
    - Difficulty selection
    - Recent quiz statistics
    """

    CSS = """
    QuizLauncherWidget {
        width: 100%;
        height: auto;
        border: solid $primary;
        background: $surface;
        padding: 1;
        margin: 0 0 1 0;
    }

    .quiz-section {
        margin: 0 0 1 0;
    }

    .quiz-button {
        width: 1fr;
        margin: 0 1 0 0;
    }

    .stats-section {
        background: $primary-lighten-3;
        padding: 1;
        margin: 1 0 0 0;
    }

    .stat-item {
        margin: 0 0 0.5 0;
    }
    """

    # Reactive state
    quiz_active: reactive[bool] = reactive(False)
    recent_accuracy: reactive[float] = reactive(0.0)

    def __init__(self, chart_data: Optional[Dict[str, HandAction]] = None, **kwargs):
        super().__init__(**kwargs)
        self.chart_data = chart_data
        self.quiz_service = get_quiz_service()
        self.event_bus = get_event_bus()
        self.current_session_id: Optional[str] = None
        self._setup_event_handlers()

    def _setup_event_handlers(self):
        """Setup event handlers for quiz integration."""
        self.event_bus.subscribe(EventType.QUIZ_STARTED, self._on_quiz_started)
        self.event_bus.subscribe(EventType.QUIZ_COMPLETED, self._on_quiz_completed)

    def _on_quiz_started(self, event):
        """Handle quiz started event."""
        if hasattr(event, 'data') and 'session_id' in event.data:
            self.current_session_id = event.data['session_id']
            self.quiz_active = True

    def _on_quiz_completed(self, event):
        """Handle quiz completed event."""
        self.quiz_active = False
        if hasattr(event, 'data'):
            accuracy = event.data.get('accuracy', 0)
            self.recent_accuracy = accuracy
            self.refresh()

    def compose(self):
        """Compose the quiz launcher widget."""
        with Vertical():
            yield Label("🎯 Quick Quiz Launch", classes="quiz-section")

            # Quiz mode buttons
            with Horizontal():
                yield Button("Flash Cards", id="flashcard_quiz", variant="primary", classes="quiz-button")
                yield Button("Multiple Choice", id="multiple_choice_quiz", variant="success", classes="quiz-button")

            with Horizontal():
                yield Button("Timed Quiz", id="timed_quiz", variant="warning", classes="quiz-button")
                yield Button("Custom Quiz", id="custom_quiz", variant="default", classes="quiz-button")

            # Recent statistics
            with Vertical(classes="stats-section"):
                yield Label("📊 Recent Performance", classes="stat-item")
                if self.recent_accuracy > 0:
                    yield Static(f"Last Quiz Accuracy: {self.recent_accuracy:.1%}", classes="stat-item")
                else:
                    yield Static("No recent quiz data", classes="stat-item")

                # Quick stats
                analytics = self.quiz_service.get_quiz_analytics()
                if analytics.get('total_sessions', 0) > 0:
                    yield Static(f"Total Sessions: {analytics['total_sessions']}", classes="stat-item")
                    yield Static(f"Overall Accuracy: {analytics.get('overall_accuracy', 0):.1%}", classes="stat-item")

    @on(Button.Pressed, "#flashcard_quiz")
    def launch_flashcard_quiz(self, event: Button.Pressed):
        """Launch flashcard quiz."""
        self._launch_quiz(QuizMode.FLASHCARD, QuizDifficulty.MEDIUM)

    @on(Button.Pressed, "#multiple_choice_quiz")
    def launch_multiple_choice_quiz(self, event: Button.Pressed):
        """Launch multiple choice quiz."""
        self._launch_quiz(QuizMode.MULTIPLE_CHOICE, QuizDifficulty.MEDIUM)

    @on(Button.Pressed, "#timed_quiz")
    def launch_timed_quiz(self, event: Button.Pressed):
        """Launch timed quiz."""
        self._launch_quiz(QuizMode.TIMED_MODE, QuizDifficulty.HARD)

    @on(Button.Pressed, "#custom_quiz")
    def launch_custom_quiz(self, event: Button.Pressed):
        """Launch custom quiz with settings."""
        # For now, use default settings
        self._launch_quiz(QuizMode.FLASHCARD, QuizDifficulty.MEDIUM)

    def _launch_quiz(self, mode: QuizMode, difficulty: QuizDifficulty):
        """Launch a quiz session."""
        try:
            # Create quiz session
            session_id = self.quiz_service.create_session(
                mode=mode,
                difficulty=difficulty,
                max_questions=10
            )

            # Notify parent app to switch to quiz screen
            self.post_message(QuizLaunched(session_id, mode, difficulty))

            # Update UI
            self.quiz_active = True
            self.refresh()

        except Exception as e:
            self.notify(f"Failed to start quiz: {e}", severity="error")

    def update_chart_data(self, chart_data: Dict[str, HandAction]):
        """Update the chart data for quiz generation."""
        self.chart_data = chart_data

    def get_quiz_status(self) -> Dict[str, Any]:
        """Get current quiz status."""
        if self.current_session_id:
            stats = self.quiz_service.get_session_stats(self.current_session_id)
            return stats or {}

        return {
            "active": self.quiz_active,
            "session_id": self.current_session_id
        }


class QuizProgressWidget(Static):
    """
    Widget for showing quiz progress and current question.

    This widget can be embedded in quiz screens to show:
    - Current question
    - Progress bar
    - Score
    - Time remaining (for timed quizzes)
    """

    CSS = """
    QuizProgressWidget {
        width: 100%;
        height: auto;
        border: solid $primary;
        background: $surface;
        padding: 1;
        margin: 0 0 1 0;
    }

    .progress-section {
        margin: 0 0 1 0;
    }

    .question-section {
        background: $primary-lighten-3;
        padding: 1;
        margin: 1 0 0 0;
    }

    .score-section {
        text-align: center;
        margin: 1 0 0 0;
    }
    """

    def __init__(self, session_id: str, **kwargs):
        super().__init__(**kwargs)
        self.session_id = session_id
        self.quiz_service = get_quiz_service()

    def compose(self):
        """Compose the quiz progress widget."""
        with Vertical():
            # Progress bar
            with Vertical(classes="progress-section"):
                yield Label("Progress:")
                yield ProgressBar(id="quiz_progress", total=10, show_eta=False)

            # Current question
            with Vertical(classes="question-section"):
                yield Label("Current Question:", id="question_label")

            # Score
            with Vertical(classes="score-section"):
                yield Static("Score: 0/0", id="score_display")

    def update_progress(self, current: int, total: int, score: int):
        """Update progress display."""
        try:
            # Update progress bar
            progress_bar = self.query_one("#quiz_progress", ProgressBar)
            progress_bar.progress = current
            progress_bar.total = total

            # Update score
            score_display = self.query_one("#score_display", Static)
            accuracy = (score / max(current, 1)) * 100
            score_display.update(f"Score: {score}/{current} ({accuracy:.1f}%)")

        except Exception as e:
            pass  # Widget might not be mounted yet

    def update_question(self, question_text: str):
        """Update current question display."""
        try:
            question_label = self.query_one("#question_label", Label)
            question_label.update(f"Current Question: {question_text}")
        except Exception:
            pass


class QuizResultsWidget(Static):
    """
    Widget for displaying quiz results and statistics.

    Shows:
    - Final score
    - Accuracy percentage
    - Performance breakdown
    - Recommendations
    """

    CSS = """
    QuizResultsWidget {
        width: 100%;
        height: auto;
        border: solid $success;
        background: $success-lighten-3;
        padding: 1;
        margin: 0 0 1 0;
    }

    .results-header {
        text-style: bold;
        color: $success;
        margin: 0 0 1 0;
    }

    .results-stat {
        margin: 0 0 0.5 0;
    }

    .results-recommendation {
        background: $primary-lighten-3;
        padding: 1;
        margin: 1 0 0 0;
    }
    """

    def __init__(self, session_stats: Dict[str, Any], **kwargs):
        super().__init__(**kwargs)
        self.session_stats = session_stats

    def compose(self):
        """Compose the quiz results widget."""
        with Vertical():
            yield Static("🎉 Quiz Complete!", classes="results-header")

            # Basic stats
            accuracy = self.session_stats.get('accuracy', 0) * 100
            score = self.session_stats.get('score', 0)
            total = self.session_stats.get('total_questions', 0)

            yield Static(f"Final Score: {score}/{total}", classes="results-stat")
            yield Static(f"Accuracy: {accuracy:.1f}%", classes="results-stat")

            # Performance rating
            rating = self._get_performance_rating(accuracy)
            yield Static(f"Performance: {rating}", classes="results-stat")

            # Recommendations
            with Vertical(classes="results-recommendation"):
                yield Static("💡 Recommendations:", classes="results-header")
                recommendations = self._generate_recommendations(accuracy)
                for rec in recommendations:
                    yield Static(f"• {rec}")

    def _get_performance_rating(self, accuracy: float) -> str:
        """Get performance rating based on accuracy."""
        if accuracy >= 90:
            return "Excellent! 🎯"
        elif accuracy >= 80:
            return "Great job! 👏"
        elif accuracy >= 70:
            return "Good work! 👍"
        elif accuracy >= 60:
            return "Keep practicing! 📚"
        else:
            return "More study needed! 📖"

    def _generate_recommendations(self, accuracy: float) -> list[str]:
        """Generate recommendations based on performance."""
        if accuracy >= 80:
            return [
                "Focus on edge cases and advanced scenarios",
                "Try harder difficulty levels",
                "Practice with different chart types"
            ]
        elif accuracy >= 60:
            return [
                "Review hands you got wrong",
                "Practice with similar hands more often",
                "Focus on position and stack size considerations"
            ]
        else:
            return [
                "Review basic hand rankings and ranges",
                "Start with easier quiz modes",
                "Focus on understanding action frequencies",
                "Practice with premium hands first"
            ]


# Message classes for quiz integration
class QuizLaunched(Message):
    """Message sent when a quiz is launched."""

    def __init__(self, session_id: str, mode: QuizMode, difficulty: QuizDifficulty):
        super().__init__()
        self.session_id = session_id
        self.mode = mode
        self.difficulty = difficulty


class QuizCompleted(Message):
    """Message sent when a quiz is completed."""

    def __init__(self, session_stats: Dict[str, Any]):
        super().__init__()
        self.session_stats = session_stats


# Quiz integration utilities
def create_quiz_launcher_for_chart(chart_data: Dict[str, HandAction]) -> QuizLauncherWidget:
    """Create a quiz launcher widget for a specific chart."""
    return QuizLauncherWidget(chart_data=chart_data)


def integrate_quiz_into_app(app):
    """
    Integrate quiz functionality into the main application.

    Args:
        app: Main application instance
    """
    quiz_service = get_quiz_service()

    # Add quiz methods to app
    app.quiz_service = quiz_service
    app.start_quiz_session = quiz_service.create_session
    app.get_quiz_question = quiz_service.get_current_question
    app.record_quiz_answer = quiz_service.record_answer

    # Handle quiz events
    def handle_quiz_event(event):
        if hasattr(app, 'current_screen'):
            screen = app.current_screen
            if hasattr(screen, 'handle_quiz_event'):
                screen.handle_quiz_event(event)

    # Setup event forwarding
    from ..core.events import get_event_bus
    event_bus = get_event_bus()
    event_bus.subscribe_all(handle_quiz_event)
