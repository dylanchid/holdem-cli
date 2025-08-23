"""
Quiz application for chart training.

This module contains the ChartQuizApp class that provides an interactive
quiz interface for testing poker chart knowledge.
"""

import random
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Button, Label
from textual.message import Message
from textual.binding import BindingType

from typing import Dict, List, Optional, Tuple, Any, Sequence
from datetime import datetime

from .constants import QUIZ_BINDINGS, POSITIONS
from .messages import QuizAnswerSelected, QuizQuestionRequested
from holdem_cli.types import HandAction
# from holdem_cli.charts.tui.widgets.matrix import create_sample_range


class ChartQuizApp(App):
    """Interactive quiz application for chart training."""

    BINDINGS: Sequence[BindingType] = QUIZ_BINDINGS

    def __init__(self, chart_data: Dict[str, HandAction], **kwargs):
        super().__init__(**kwargs)
        self.chart_data = chart_data
        self.current_question = None
        self.score = 0
        self.total_questions = 0
        self.streak = 0

    def compose(self) -> ComposeResult:
        yield Header()

        with Vertical():
            yield Static("🎯 Chart Training Quiz", classes="header")
            yield Static("", id="question_display")
            yield Static("", id="score_display")

            with Horizontal():
                yield Button("Raise", id="raise", variant="error")
                yield Button("Call", id="call", variant="success")
                yield Button("Fold", id="fold", variant="default")
                yield Button("Mixed", id="mixed", variant="warning")

            yield Static("", id="feedback")
            yield Static("[dim]R: Next Question | S: Show Answer | Q: Quit[/dim]")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize quiz."""
        self.title = "Holdem CLI - Chart Quiz"
        self.sub_title = "Test your GTO knowledge"
        self._generate_question()
        self._update_score_display()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle answer selection."""
        if not self.current_question:
            return

        user_answer = event.button.id
        correct_answer = self.current_question["correct_action"]

        self.total_questions += 1

        if user_answer == correct_answer:
            self.score += 1
            self.streak += 1
            feedback = f"✅ Correct! {self.current_question['explanation']}"
            feedback_widget = self.query_one("#feedback", Static)
            feedback_widget.update(f"[green]{feedback}[/green]")
        else:
            self.streak = 0
            feedback = f"❌ Wrong. Correct answer: {correct_answer.title()}. {self.current_question['explanation']}"
            feedback_widget = self.query_one("#feedback", Static)
            feedback_widget.update(f"[red]{feedback}[/red]")

        self._update_score_display()

        # Auto-advance after 3 seconds
        self.set_timer(3.0, self._generate_question)

    def action_next_question(self) -> None:
        """Generate next question."""
        self._generate_question()

    def action_show_answer(self) -> None:
        """Show the correct answer."""
        if self.current_question:
            answer = self.current_question["correct_action"]
            explanation = self.current_question["explanation"]
            feedback_widget = self.query_one("#feedback", Static)
            feedback_widget.update(f"[blue]Answer: {answer.title()} - {explanation}[/blue]")

    def _generate_question(self) -> None:
        """Generate a new quiz question."""
        # Pick a random hand from the chart
        hands = list(self.chart_data.keys())
        if not hands:
            return

        hand = random.choice(hands)
        action = self.chart_data[hand]

        # Create question
        scenarios = [
            "You're on the button vs big blind 3-bet",
            "You're in the cutoff facing a raise",
            "You're under the gun in a cash game",
            "You're in the small blind vs button raise"
        ]

        scenario = random.choice(scenarios)

        self.current_question = {
            "hand": hand,
            "scenario": scenario,
            "correct_action": action.action.value,
            "explanation": f"GTO play is {action.action.value} with {action.frequency:.0%} frequency"
        }

        # Update display
        question_text = f"""
        Scenario: {scenario}
        Your hand: {hand}

        What's your action?
        """

        question_widget = self.query_one("#question_display", Static)
        question_widget.update(question_text)
        feedback_widget = self.query_one("#feedback", Static)
        feedback_widget.update("")  # Clear previous feedback

    def _update_score_display(self) -> None:
        """Update score display."""
        if self.total_questions > 0:
            accuracy = (self.score / self.total_questions) * 100
            score_text = f"Score: {self.score}/{self.total_questions} ({accuracy:.1f}%) | Streak: {self.streak}"
        else:
            score_text = "Score: 0/0 (0%) | Streak: 0"

        score_widget = self.query_one("#score_display", Static)
        score_widget.update(score_text)


# Quiz utilities and helper functions
def generate_quiz_scenario(hand: str, action: HandAction, position: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate a quiz scenario for a specific hand and action.

    Args:
        hand: The poker hand (e.g., 'AKs', 'QQ')
        action: The HandAction object
        position: Optional position override

    Returns:
        Dictionary containing scenario details
    """
    positions = [
        "under the gun",
        "middle position",
        "cutoff",
        "button",
        "small blind",
        "big blind"
    ]

    scenarios = [
        "facing a raise",
        "in a 3-bet pot",
        "on the flop",
        "facing multiple opponents",
        "in a tournament bubble",
        "in a cash game"
    ]

    selected_position = position or random.choice(positions)
    scenario = random.choice(scenarios)

    return {
        "hand": hand,
        "position": selected_position,
        "scenario": scenario,
        "correct_action": action.action.value,
        "frequency": action.frequency,
        "ev": action.ev,
        "question": f"You're {selected_position} {scenario} with {hand}. What's your action?",
        "explanation": f"GTO play is {action.action.value} with {action.frequency:.0%} frequency"
    }


def create_quiz_from_chart(chart_data: Dict[str, HandAction], num_questions: int = 10) -> List[Dict[str, Any]]:
    """
    Create a quiz from chart data.

    Args:
        chart_data: Dictionary of hand actions
        num_questions: Number of questions to generate

    Returns:
        List of quiz questions
    """
    hands = list(chart_data.keys())
    if len(hands) < num_questions:
        num_questions = len(hands)

    quiz_hands = random.sample(hands, num_questions)
    quiz = []

    for hand in quiz_hands:
        action = chart_data[hand]
        scenario = generate_quiz_scenario(hand, action)
        quiz.append(scenario)

    return quiz


def calculate_quiz_score(answers: List[str], correct_answers: List[str]) -> Dict[str, Any]:
    """
    Calculate quiz score and statistics.

    Args:
        answers: List of user answers
        correct_answers: List of correct answers

    Returns:
        Dictionary with score statistics
    """
    if len(answers) != len(correct_answers):
        raise ValueError("Answers and correct answers must have same length")

    correct = sum(1 for a, c in zip(answers, correct_answers) if a == c)
    total = len(answers)
    accuracy = (correct / total) * 100 if total > 0 else 0

    # Calculate streak
    max_streak = 0
    current_streak = 0

    for a, c in zip(answers, correct_answers):
        if a == c:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0

    return {
        "correct": correct,
        "total": total,
        "accuracy": accuracy,
        "max_streak": max_streak,
        "passed": accuracy >= 70  # Consider 70% passing
    }


def export_quiz_results(results: Dict[str, Any], filepath: str) -> None:
    """
    Export quiz results to a file.

    Args:
        results: Quiz results dictionary
        filepath: Path to export file
    """
    import json
    from pathlib import Path

    # Add timestamp
    results["timestamp"] = datetime.now().isoformat()
    results["export_format"] = "holdem-cli-quiz-v1"

    path = Path(filepath)
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)


def run_quiz_demo():
    """Run a demo of the quiz functionality."""
    print("Starting Chart Quiz Demo...")

    # Create sample chart
    sample_chart = create_sample_range()

    # Run quiz
    quiz_app = ChartQuizApp(sample_chart)
    quiz_app.run()
