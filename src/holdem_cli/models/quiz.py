"""
Quiz and learning data models for Holdem CLI.

This module defines standardized models for quiz questions, results,
and learning progress tracking.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from datetime import datetime
from .base import BaseModel, TimestampMixin, Identifiable


class QuizType(Enum):
    """Types of quizzes available in the system."""
    HAND_RANKING = "hand_ranking"
    POT_ODDS = "pot_odds"
    PREFLOP_RANGES = "preflop_ranges"
    EQUITY_CALCULATION = "equity_calculation"
    CHART_QUIZ = "chart_quiz"
    SIMULATION_REVIEW = "simulation_review"


class Difficulty(Enum):
    """Quiz difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    ADAPTIVE = "adaptive"


class QuestionType(Enum):
    """Types of quiz questions."""
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    NUMERIC_INPUT = "numeric_input"
    TEXT_INPUT = "text_input"
    RANGE_SELECTION = "range_selection"


@dataclass
class QuizQuestion(BaseModel, Identifiable):
    """Standardized quiz question model."""
    question_text: str
    question_type: QuestionType = QuestionType.MULTIPLE_CHOICE
    quiz_type: QuizType = QuizType.HAND_RANKING
    difficulty: Difficulty = Difficulty.MEDIUM

    # Question content
    options: List[str] = field(default_factory=list)  # For multiple choice
    correct_answer: Union[int, str, bool, float] = 0  # Index or value
    explanation: str = ""

    # Additional context
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Learning context
    prerequisite_skills: List[str] = field(default_factory=list)
    target_skills: List[str] = field(default_factory=list)

    def validate(self) -> List[str]:
        """Validate quiz question data."""
        issues = []

        if not self.question_text.strip():
            issues.append("Question text cannot be empty")

        if self.question_type == QuestionType.MULTIPLE_CHOICE and not self.options:
            issues.append("Multiple choice questions must have options")

        if self.question_type == QuestionType.MULTIPLE_CHOICE:
            if isinstance(self.correct_answer, int):
                if not (0 <= self.correct_answer < len(self.options)):
                    issues.append("Correct answer index out of range")
            else:
                issues.append("Multiple choice questions must have integer correct answer")

        if not self.explanation.strip():
            issues.append("Explanation cannot be empty")

        return issues

    def is_correct_answer(self, answer: Union[int, str, bool, float]) -> bool:
        """Check if the provided answer is correct."""
        if self.question_type == QuestionType.MULTIPLE_CHOICE:
            return isinstance(answer, int) and answer == self.correct_answer
        elif self.question_type == QuestionType.TRUE_FALSE:
            return isinstance(answer, bool) and answer == self.correct_answer
        elif self.question_type == QuestionType.NUMERIC_INPUT:
            return abs(float(answer) - float(self.correct_answer)) < 0.01
        else:
            return str(answer).strip().lower() == str(self.correct_answer).strip().lower()

    def get_formatted_question(self) -> str:
        """Get formatted question text with options."""
        formatted = self.question_text

        if self.question_type == QuestionType.MULTIPLE_CHOICE and self.options:
            formatted += "\n\nOptions:"
            for i, option in enumerate(self.options):
                formatted += f"\n{i + 1}. {option}"

        return formatted


@dataclass
class QuizAnswer(BaseModel):
    """Model for tracking user answers to quiz questions."""
    question_id: int
    user_answer: Union[int, str, bool, float]
    is_correct: bool = False
    time_to_answer_seconds: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    # Learning analytics
    confidence_level: Optional[int] = None  # 1-5 scale
    hints_used: int = 0
    mistakes_made: int = 0

    def calculate_score(self) -> float:
        """Calculate score for this answer (0.0 to 1.0)."""
        if self.is_correct:
            # Bonus for quick answers, penalty for hints
            time_bonus = max(0.0, 1.0 - (self.time_to_answer_seconds / 60.0))  # 1 minute max
            hint_penalty = min(0.5, self.hints_used * 0.1)
            return min(1.0, 0.8 + time_bonus * 0.2 - hint_penalty)

        # Penalty for mistakes and time taken
        mistake_penalty = min(0.5, self.mistakes_made * 0.1)
        return max(0.0, 0.2 - mistake_penalty)


@dataclass
class QuizResult(BaseModel, TimestampMixin):
    """Model for quiz results and analytics."""
    quiz_type: QuizType
    total_questions: int
    correct_answers: int
    total_time_seconds: float
    difficulty: Difficulty

    # Question and answer tracking
    questions: List[QuizQuestion] = field(default_factory=list)
    answers: List[QuizAnswer] = field(default_factory=list)

    # Performance metrics
    accuracy: float = 0.0
    average_time_per_question: float = 0.0
    streak_count: int = 0
    max_streak: int = 0

    # Learning progress
    skills_improved: List[str] = field(default_factory=list)
    skills_need_work: List[str] = field(default_factory=list)
    difficulty_recommendation: Optional[Difficulty] = None

    # Metadata
    session_metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Calculate derived metrics after initialization."""
        self._calculate_metrics()

    def _calculate_metrics(self) -> None:
        """Calculate performance metrics."""
        if self.total_questions > 0:
            self.accuracy = self.correct_answers / self.total_questions

        if self.total_questions > 0 and self.total_time_seconds > 0:
            self.average_time_per_question = self.total_time_seconds / self.total_questions

        # Calculate streak
        current_streak = 0
        self.max_streak = 0

        for answer in self.answers:
            if answer.is_correct:
                current_streak += 1
                self.max_streak = max(self.max_streak, current_streak)
            else:
                current_streak = 0

        self.streak_count = current_streak

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        return {
            'accuracy': self.accuracy,
            'total_questions': self.total_questions,
            'correct_answers': self.correct_answers,
            'total_time': self.total_time_seconds,
            'average_time_per_question': self.average_time_per_question,
            'streak_count': self.streak_count,
            'max_streak': self.max_streak,
            'quiz_type': self.quiz_type.value,
            'difficulty': self.difficulty.value
        }

    def get_learning_insights(self) -> Dict[str, Any]:
        """Get learning insights from quiz performance."""
        insights = {
            'skills_improved': self.skills_improved,
            'skills_need_work': self.skills_need_work,
            'difficulty_recommendation': self.difficulty_recommendation.value if self.difficulty_recommendation else None
        }

        # Analyze time patterns
        if self.answers:
            fast_answers = [a for a in self.answers if a.time_to_answer_seconds < 10]
            slow_answers = [a for a in self.answers if a.time_to_answer_seconds > 30]

            insights['fast_correct'] = len([a for a in fast_answers if a.is_correct])
            insights['slow_incorrect'] = len([a for a in slow_answers if not a.is_correct])

        return insights


@dataclass
class QuizSession(BaseModel, TimestampMixin, Identifiable):
    """Model for quiz session tracking."""
    user_id: int
    quiz_type: QuizType
    difficulty: Difficulty
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0

    # Session state
    is_completed: bool = False
    is_aborted: bool = False
    current_question_index: int = 0

    # Performance tracking
    questions_answered: int = 0
    questions_correct: int = 0

    # Session configuration
    question_count: int = 10
    time_limit_seconds: Optional[int] = None

    # Results
    result: Optional[QuizResult] = None

    def start(self) -> None:
        """Start the quiz session."""
        self.start_time = datetime.now()

    def end(self) -> None:
        """End the quiz session."""
        self.end_time = datetime.now()
        self.duration_seconds = (self.end_time - self.start_time).total_seconds()
        self.is_completed = True

    def abort(self) -> None:
        """Abort the quiz session."""
        self.end_time = datetime.now()
        self.duration_seconds = (self.end_time - self.start_time).total_seconds()
        self.is_aborted = True

    def record_answer(self, answer: QuizAnswer) -> None:
        """Record an answer for the current question."""
        self.questions_answered += 1
        if answer.is_correct:
            self.questions_correct += 1
        self.current_question_index += 1

    @property
    def progress_percentage(self) -> float:
        """Get session progress as percentage."""
        if self.question_count == 0:
            return 100.0
        return (self.current_question_index / self.question_count) * 100.0

    @property
    def accuracy_percentage(self) -> float:
        """Get current accuracy as percentage."""
        if self.questions_answered == 0:
            return 0.0
        return (self.questions_correct / self.questions_answered) * 100.0


@dataclass
class LearningProgress(BaseModel, TimestampMixin, Identifiable):
    """Model for tracking user learning progress over time."""
    user_id: int

    # Overall progress
    total_quizzes_completed: int = 0
    total_questions_answered: int = 0
    total_correct_answers: int = 0
    overall_accuracy: float = 0.0

    # Skill-specific progress
    skill_accuracy: Dict[str, float] = field(default_factory=dict)
    skill_attempts: Dict[str, int] = field(default_factory=dict)
    skill_improvement_rate: Dict[str, float] = field(default_factory=dict)

    # Learning patterns
    preferred_difficulty: Difficulty = Difficulty.MEDIUM
    average_session_duration: float = 0.0
    streak_data: Dict[str, int] = field(default_factory=dict)  # Current and max streaks

    # Adaptive learning
    recommended_difficulty: Difficulty = Difficulty.MEDIUM
    focus_skills: List[str] = field(default_factory=list)
    review_needed_skills: List[str] = field(default_factory=list)

    def update_skill_progress(self, skill: str, is_correct: bool) -> None:
        """Update progress for a specific skill."""
        if skill not in self.skill_attempts:
            self.skill_attempts[skill] = 0
            self.skill_accuracy[skill] = 0.0

        self.skill_attempts[skill] += 1

        # Calculate new accuracy
        current_correct = int(self.skill_accuracy[skill] * (self.skill_attempts[skill] - 1))
        if is_correct:
            current_correct += 1

        self.skill_accuracy[skill] = current_correct / self.skill_attempts[skill]

    def get_weakest_skills(self, limit: int = 5) -> List[str]:
        """Get the weakest skills that need improvement."""
        # Sort skills by accuracy (ascending)
        sorted_skills = sorted(
            self.skill_accuracy.items(),
            key=lambda x: x[1]
        )
        return [skill for skill, accuracy in sorted_skills[:limit]]

    def get_strongest_skills(self, limit: int = 5) -> List[str]:
        """Get the strongest skills."""
        # Sort skills by accuracy (descending)
        sorted_skills = sorted(
            self.skill_accuracy.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [skill for skill, accuracy in sorted_skills[:limit]]
