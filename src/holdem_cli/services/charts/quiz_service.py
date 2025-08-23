"""
Quiz service for TUI quiz functionality.

This module provides a service layer for quiz operations including:
- Quiz session management
- Question generation and scoring
- Progress tracking
- Statistics and analytics
- Integration with chart data
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import random
from dataclasses import dataclass, field
from enum import Enum, auto

from holdem_cli.types import HandAction, ChartAction
from holdem_cli.charts.tui.core.events import get_event_bus, EventType, create_quiz_answer_event
# from holdem_cli.charts.tui.core.cache import SmartCache


class QuizMode(Enum):
    """Quiz modes available."""
    FLASHCARD = auto()
    MULTIPLE_CHOICE = auto()
    INPUT_MODE = auto()
    TIMED_MODE = auto()


class QuizDifficulty(Enum):
    """Quiz difficulty levels."""
    EASY = auto()      # Basic actions, common hands
    MEDIUM = auto()    # Mixed strategies, broader range
    HARD = auto()      # Complex situations, edge cases
    EXPERT = auto()    # Advanced concepts, rare hands


@dataclass
class QuizQuestion:
    """A single quiz question."""
    id: str
    hand: str
    scenario: str
    correct_action: ChartAction
    frequency: float
    explanation: str
    difficulty: QuizDifficulty = QuizDifficulty.MEDIUM
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.id:
            import uuid
            self.id = str(uuid.uuid4())[:8]


@dataclass
class QuizSession:
    """A complete quiz session."""
    id: str
    mode: QuizMode
    difficulty: QuizDifficulty
    chart_id: Optional[str]
    questions: List[QuizQuestion] = field(default_factory=list)
    answers: List[Tuple[str, bool, float]] = field(default_factory=list)  # (answer, correct, response_time)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    score: int = 0
    current_question_index: int = 0
    max_questions: int = 10

    @property
    def is_completed(self) -> bool:
        return self.completed_at is not None or len(self.answers) >= self.max_questions

    @property
    def accuracy(self) -> float:
        if not self.answers:
            return 0.0
        correct_answers = sum(1 for _, correct, _ in self.answers if correct)
        return correct_answers / len(self.answers)

    @property
    def average_response_time(self) -> float:
        if not self.answers:
            return 0.0
        return sum(time for _, _, time in self.answers) / len(self.answers)


class QuizService:
    """
    Service for managing quiz functionality.

    Features:
    - Question generation from chart data
    - Session management and progress tracking
    - Scoring and analytics
    - Difficulty adaptation
    - Performance statistics
    """

    def __init__(self):
        self.active_sessions: Dict[str, QuizSession] = {}
        self.question_cache = SmartCache(max_size=100)
        self.session_cache = SmartCache(max_size=50)
        self.event_bus = get_event_bus()
        self._setup_event_handlers()

    def _setup_event_handlers(self):
        """Setup event system integration."""
        self.event_bus.subscribe(EventType.QUIZ_ANSWER_SELECTED, self._on_answer_selected)

    def _on_answer_selected(self, event):
        """Handle quiz answer events."""
        if hasattr(event, 'quiz_id') and event.quiz_id in self.active_sessions:
            session = self.active_sessions[event.quiz_id]
            if hasattr(event, 'user_answer') and hasattr(event, 'correct_answer'):
                self.record_answer(
                    event.quiz_id,
                    event.user_answer,
                    event.correct_answer
                )

    def create_session(
        self,
        mode: QuizMode = QuizMode.FLASHCARD,
        difficulty: QuizDifficulty = QuizDifficulty.MEDIUM,
        chart_id: Optional[str] = None,
        max_questions: int = 10
    ) -> str:
        """
        Create a new quiz session.

        Args:
            mode: Quiz mode
            difficulty: Difficulty level
            chart_id: Associated chart ID
            max_questions: Maximum number of questions

        Returns:
            Session ID
        """
        import uuid
        session_id = str(uuid.uuid4())[:8]

        session = QuizSession(
            id=session_id,
            mode=mode,
            difficulty=difficulty,
            chart_id=chart_id,
            max_questions=max_questions
        )

        self.active_sessions[session_id] = session
        self.session_cache.set(f"session_{session_id}", session)

        # Publish session created event
        self.event_bus.publish_sync(self.event_bus.create_event(
            EventType.QUIZ_STARTED,
            data={"session_id": session_id, "mode": mode.name}
        ))

        return session_id

    def generate_question(
        self,
        session_id: str,
        chart_data: Dict[str, HandAction]
    ) -> Optional[QuizQuestion]:
        """
        Generate a question for the quiz session.

        Args:
            session_id: Session ID
            chart_data: Chart data to generate questions from

        Returns:
            Generated question or None if session is complete
        """
        if session_id not in self.active_sessions:
            return None

        session = self.active_sessions[session_id]
        if session.is_completed:
            return None

        # Generate question based on mode and difficulty
        if session.mode == QuizMode.FLASHCARD:
            return self._generate_flashcard_question(session, chart_data)
        elif session.mode == QuizMode.MULTIPLE_CHOICE:
            return self._generate_multiple_choice_question(session, chart_data)
        elif session.mode == QuizMode.TIMED_MODE:
            return self._generate_timed_question(session, chart_data)
        else:
            return self._generate_flashcard_question(session, chart_data)

    def _generate_flashcard_question(
        self,
        session: QuizSession,
        chart_data: Dict[str, HandAction]
    ) -> QuizQuestion:
        """Generate a flashcard-style question."""
        # Get available hands
        available_hands = list(chart_data.keys())
        if not available_hands:
            return None

        # Avoid repeating recent questions
        recent_hands = {q.hand for q in session.questions[-5:]}
        available_hands = [h for h in available_hands if h not in recent_hands]

        if not available_hands:
            available_hands = list(chart_data.keys())

        hand = random.choice(available_hands)
        action = chart_data[hand]

        # Generate scenario based on difficulty
        scenario = self._generate_scenario(hand, action, session.difficulty)

        return QuizQuestion(
            id="",
            hand=hand,
            scenario=scenario,
            correct_action=action.action,
            frequency=action.frequency,
            explanation=self._generate_explanation(action),
            difficulty=session.difficulty
        )

    def _generate_multiple_choice_question(
        self,
        session: QuizSession,
        chart_data: Dict[str, HandAction]
    ) -> QuizQuestion:
        """Generate a multiple choice question."""
        # Similar to flashcard but with options
        question = self._generate_flashcard_question(session, chart_data)
        if question:
            # Add multiple choice options to the explanation
            question.explanation += "\n\nOptions: Raise, Call, Fold, Mixed"
        return question

    def _generate_timed_question(
        self,
        session: QuizSession,
        chart_data: Dict[str, HandAction]
    ) -> QuizQuestion:
        """Generate a timed question."""
        question = self._generate_flashcard_question(session, chart_data)
        if question:
            question.explanation += " (Answer quickly!)"
        return question

    def _generate_scenario(
        self,
        hand: str,
        action: HandAction,
        difficulty: QuizDifficulty
    ) -> str:
        """Generate a scenario description based on difficulty."""
        scenarios = {
            QuizDifficulty.EASY: [
                "You're playing in a basic cash game",
                "Standard tournament situation",
                "You have a decent stack",
                "Position is not critical"
            ],
            QuizDifficulty.MEDIUM: [
                "You're on the button vs big blind 3-bet",
                "You're in the cutoff facing a raise",
                "You're under the gun in a cash game",
                "You're in the small blind vs button raise"
            ],
            QuizDifficulty.HARD: [
                "You're in the big blind vs late position squeeze",
                "You're facing a 4-bet after 3-betting",
                "You're in a tournament bubble with a short stack",
                "You're playing against a tight-aggressive opponent"
            ],
            QuizDifficulty.EXPERT: [
                "You're facing a light 3-bet from a recreational player",
                "You're in a high-stakes cash game with aggressive opponents",
                "You're playing a tournament final table",
                "You're facing a complex mixed strategy situation"
            ]
        }

        return random.choice(scenarios.get(difficulty, scenarios[QuizDifficulty.MEDIUM]))

    def _generate_explanation(self, action: HandAction) -> str:
        """Generate explanation for the correct action."""
        frequency_pct = action.frequency * 100

        explanations = {
            ChartAction.RAISE: f"Raise with {frequency_pct:.0f}% frequency. This is a premium hand that plays well in most situations.",
            ChartAction.CALL: f"Call with {frequency_pct:.0f}% frequency. This hand is marginal but worth defending in position.",
            ChartAction.FOLD: f"Fold with {frequency_pct:.0f}% frequency. This hand doesn't have enough equity to continue.",
            ChartAction.MIXED: f"Mixed strategy with {frequency_pct:.0f}% frequency. Balance between raising and calling based on opponent tendencies.",
            ChartAction.BLUFF: f"Bluff with {frequency_pct:.0f}% frequency. This hand has blocker value and fold equity."
        }

        return explanations.get(action.action, f"Play {action.action.value} with {frequency_pct:.0f}% frequency")

    def record_answer(
        self,
        session_id: str,
        user_answer: str,
        correct_answer: str,
        response_time: float = 0.0
    ) -> bool:
        """
        Record an answer for a quiz session.

        Args:
            session_id: Session ID
            user_answer: User's answer
            correct_answer: Correct answer
            response_time: Time taken to answer

        Returns:
            True if answer was correct
        """
        if session_id not in self.active_sessions:
            return False

        session = self.active_sessions[session_id]
        is_correct = user_answer.lower() == correct_answer.lower()

        if is_correct:
            session.score += 1

        # Record answer
        session.answers.append((user_answer, is_correct, response_time))

        # Check if quiz is complete
        if len(session.answers) >= session.max_questions:
            session.completed_at = datetime.now()
            self._finalize_session(session)

        return is_correct

    def _finalize_session(self, session: QuizSession):
        """Finalize a completed quiz session."""
        # Publish completion event
        self.event_bus.publish_sync(self.event_bus.create_event(
            EventType.QUIZ_COMPLETED,
            data={
                "session_id": session.id,
                "score": session.score,
                "accuracy": session.accuracy,
                "total_questions": len(session.answers)
            }
        ))

    def get_current_question(self, session_id: str) -> Optional[QuizQuestion]:
        """Get the current question for a session."""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            if session.current_question_index < len(session.questions):
                return session.questions[session.current_question_index]
        return None

    def get_session_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a quiz session."""
        if session_id not in self.active_sessions:
            return None

        session = self.active_sessions[session_id]

        return {
            "session_id": session.id,
            "mode": session.mode.name,
            "difficulty": session.difficulty.name,
            "score": session.score,
            "total_questions": len(session.answers),
            "accuracy": session.accuracy,
            "average_response_time": session.average_response_time,
            "is_completed": session.is_completed,
            "duration": (datetime.now() - session.started_at).total_seconds() if not session.completed_at else (session.completed_at - session.started_at).total_seconds()
        }

    def get_quiz_analytics(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get quiz analytics."""
        if session_id:
            return self.get_session_stats(session_id) or {}

        # Aggregate analytics for all sessions
        all_sessions = list(self.active_sessions.values())
        if not all_sessions:
            return {}

        total_sessions = len(all_sessions)
        completed_sessions = [s for s in all_sessions if s.is_completed]
        total_score = sum(s.score for s in completed_sessions)
        total_questions = sum(len(s.answers) for s in completed_sessions)

        return {
            "total_sessions": total_sessions,
            "completed_sessions": len(completed_sessions),
            "total_questions_answered": total_questions,
            "total_correct_answers": total_score,
            "overall_accuracy": total_score / max(total_questions, 1),
            "average_session_score": sum(len(s.answers) for s in completed_sessions) / max(len(completed_sessions), 1),
            "most_common_difficulty": self._get_most_common_difficulty(all_sessions)
        }

    def _get_most_common_difficulty(self, sessions: List[QuizSession]) -> str:
        """Get the most common difficulty level."""
        difficulties = [s.difficulty.name for s in sessions]
        if not difficulties:
            return "UNKNOWN"

        from collections import Counter
        most_common = Counter(difficulties).most_common(1)[0][0]
        return most_common

    def cleanup_session(self, session_id: str):
        """Clean up a quiz session."""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            self.session_cache.clear()

    def get_available_scenarios(self, difficulty: QuizDifficulty) -> List[str]:
        """Get available scenarios for a difficulty level."""
        scenarios = {
            QuizDifficulty.EASY: [
                "Basic cash game situation",
                "Standard tournament play",
                "You have average stack size",
                "Position doesn't matter much"
            ],
            QuizDifficulty.MEDIUM: [
                "You're on the button vs big blind 3-bet",
                "You're in the cutoff facing a raise",
                "You're under the gun in a cash game",
                "You're in the small blind vs button raise",
                "You're in the big blind facing a raise"
            ],
            QuizDifficulty.HARD: [
                "You're in the big blind vs late position squeeze",
                "You're facing a 4-bet after 3-betting",
                "You're in a tournament bubble with a short stack",
                "You're playing against a tight-aggressive opponent",
                "You're facing multiple opponents"
            ],
            QuizDifficulty.EXPERT: [
                "You're facing a light 3-bet from a recreational player",
                "You're in a high-stakes cash game with aggressive opponents",
                "You're playing a tournament final table",
                "You're facing a complex mixed strategy situation",
                "You're playing against a solver-based opponent"
            ]
        }

        return scenarios.get(difficulty, scenarios[QuizDifficulty.MEDIUM])


# Global quiz service instance
_quiz_service: Optional[QuizService] = None


def get_quiz_service() -> QuizService:
    """Get or create the global quiz service instance."""
    global _quiz_service
    if _quiz_service is None:
        _quiz_service = QuizService()
    return _quiz_service


def reset_quiz_service():
    """Reset the global quiz service instance."""
    global _quiz_service
    _quiz_service = None


# Quiz integration utilities
def integrate_quiz_with_app(app, quiz_service: QuizService):
    """
    Integrate quiz service with the main application.

    Args:
        app: Main application instance
        quiz_service: Quiz service instance
    """
    # Add quiz methods to app
    app.start_quiz_session = quiz_service.create_session
    app.get_current_quiz_question = quiz_service.get_current_question
    app.record_quiz_answer = quiz_service.record_answer
    app.get_quiz_stats = quiz_service.get_session_stats

    # Setup event forwarding
    def forward_quiz_events(event):
        if hasattr(app, 'handle_quiz_event'):
            app.handle_quiz_event(event)

    quiz_service.event_bus.subscribe_all(forward_quiz_events)


def create_quiz_summary(session: QuizSession) -> Dict[str, Any]:
    """
    Create a summary of a quiz session.

    Args:
        session: Quiz session

    Returns:
        Session summary
    """
    if not session.is_completed:
        return {"status": "incomplete"}

    correct_answers = sum(1 for _, correct, _ in session.answers if correct)

    return {
        "status": "completed",
        "session_id": session.id,
        "mode": session.mode.name,
        "difficulty": session.difficulty.name,
        "score": session.score,
        "total_questions": len(session.answers),
        "correct_answers": correct_answers,
        "accuracy": session.accuracy,
        "average_response_time": session.average_response_time,
        "duration_seconds": (session.completed_at - session.started_at).total_seconds() if session.completed_at else 0,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None
    }
