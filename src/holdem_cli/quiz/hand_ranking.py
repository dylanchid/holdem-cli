"""Hand ranking quiz implementation."""

from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass
from pathlib import Path

from ..engine.cards import Card, Deck, HandEvaluator, HandRank, HandStrength
from ..utils.random_utils import get_global_random


@dataclass
class QuizQuestion:
    """A single quiz question with correct answer."""
    question_text: str
    hands: List[List[Card]]
    hand_descriptions: List[str]
    correct_answer: int  # Index of the stronger hand
    explanation: str


@dataclass
class QuizResult:
    """Results from a completed quiz."""
    total_questions: int
    correct_answers: int
    questions: List[QuizQuestion]
    user_answers: List[int]
    accuracy: float


class HandRankingQuiz:
    """Quiz for testing poker hand ranking knowledge."""

    def __init__(self, difficulty: str = 'adaptive', seed: Optional[int] = None,
                 db_path: Optional[Path] = None, user_id: Optional[int] = None):
        """Initialize quiz with difficulty and optional seed for testing."""
        self.difficulty = difficulty
        self.adaptive_mode = difficulty == 'adaptive'
        self.evaluator = HandEvaluator()
        self.db_path = db_path
        self.user_id = user_id
        self._random = get_global_random()
        if seed is not None:
            self._random.seed(seed)

    def _get_adaptive_difficulty(self) -> str:
        """Determine adaptive difficulty based on user performance."""
        if not self.adaptive_mode or not self.db_path or not self.user_id:
            return self.difficulty

        try:
            # Import database module here to avoid circular imports
            from ..storage.database import Database
            db = Database(self.db_path)

            # Get recent quiz performance
            stats = db.get_user_quiz_stats(self.user_id)

            # Analyze performance across quiz types
            if 'hand-ranking' in stats['by_type']:
                hr_stats = stats['by_type']['hand-ranking']

                # Adaptive logic based on recent performance
                recent_accuracy = hr_stats['avg_accuracy']

                if recent_accuracy >= 90:
                    return 'hard'
                elif recent_accuracy >= 75:
                    return 'medium'
                elif recent_accuracy >= 60:
                    return 'easy'
                else:
                    return 'easy'  # Stay easy if struggling

            # Default to medium if no history
            return 'medium'

        except Exception:
            # Fallback to medium if database issues
            return 'medium'

    def _generate_random_hand(self, deck: Deck, size: int = 5) -> List[Card]:
        """Generate a random poker hand of specified size."""
        return deck.deal(size)
    
    def _get_difficulty_constraints(self) -> Dict[str, Any]:
        """Get constraints based on difficulty level."""
        if self.difficulty == 'easy':
            return {
                'allow_close_ranks': False,  # No close hand rankings
                'min_rank_difference': 3,    # At least 3 ranks apart
                'prefer_obvious': True       # Prefer obvious differences
            }
        elif self.difficulty == 'medium':
            return {
                'allow_close_ranks': True,
                'min_rank_difference': 1,
                'prefer_obvious': False
            }
        else:  # hard
            return {
                'allow_close_ranks': True,
                'min_rank_difference': 0,    # Can be same rank
                'prefer_obvious': False,
                'allow_kicker_battles': True  # Include kicker comparisons
            }
    
    def _meets_difficulty_constraints(self, strength1: HandStrength,
                                    strength2: HandStrength, difficulty: str) -> bool:
        """Check if two hands meet the difficulty constraints."""
        # Temporarily set difficulty for constraint calculation
        original_difficulty = self.difficulty
        self.difficulty = difficulty
        constraints = self._get_difficulty_constraints()
        self.difficulty = original_difficulty  # Restore original

        rank_diff = abs(strength1.rank.numeric_value - strength2.rank.numeric_value)
        
        if not constraints['allow_close_ranks'] and rank_diff < constraints['min_rank_difference']:
            return False
        
        # For hard difficulty, sometimes include same rank hands (kicker battles)
        if (self.difficulty == 'hard' and 
            constraints.get('allow_kicker_battles') and 
            strength1.rank == strength2.rank):
            return True
            
        return rank_diff >= constraints['min_rank_difference']
    
    def generate_question(self) -> QuizQuestion:
        """Generate a single hand comparison question."""
        # Get current difficulty for adaptive mode
        current_difficulty = self._get_adaptive_difficulty() if self.adaptive_mode else self.difficulty

        max_attempts = 100
        deck = Deck()
        deck.shuffle()

        for _ in range(max_attempts):
            # Generate two 5-card hands
            hand1 = self._generate_random_hand(deck, 5)
            hand2 = self._generate_random_hand(deck, 5)
            
            # Evaluate both hands
            strength1 = self.evaluator.evaluate_hand(hand1)
            strength2 = self.evaluator.evaluate_hand(hand2)
            
            # Check if hands meet difficulty constraints
            if not self._meets_difficulty_constraints(strength1, strength2, current_difficulty):
                # Reset deck and try again
                deck = Deck()
                deck.shuffle()
                continue
            
            # Determine which hand is stronger
            if strength1 > strength2:
                stronger_hand_idx = 0
                explanation = f"Hand 1 ({strength1.description}) beats Hand 2 ({strength2.description})"
            elif strength2 > strength1:
                stronger_hand_idx = 1
                explanation = f"Hand 2 ({strength2.description}) beats Hand 1 ({strength1.description})"
            else:
                # Tie - for most quiz purposes, we'll regenerate
                deck = Deck()
                deck.shuffle()
                continue
            
            # Format hand descriptions
            hand1_desc = f"{strength1.description} ({', '.join(str(c) for c in hand1)})"
            hand2_desc = f"{strength2.description} ({', '.join(str(c) for c in hand2)})"
            
            return QuizQuestion(
                question_text="Which hand is stronger?",
                hands=[hand1, hand2],
                hand_descriptions=[hand1_desc, hand2_desc],
                correct_answer=stronger_hand_idx,
                explanation=explanation
            )
        
        raise RuntimeError("Could not generate suitable question after maximum attempts")
    
    def run_interactive_quiz(self, count: int) -> QuizResult:
        """Run an interactive quiz session."""
        import click
        
        questions = []
        user_answers = []
        correct_count = 0
        
        current_difficulty = self._get_adaptive_difficulty() if self.adaptive_mode else self.difficulty
        difficulty_display = f"Adaptive ({current_difficulty.title()})" if self.adaptive_mode else f"{self.difficulty.title()}"

        click.echo(f"\n🃏 Hand Ranking Quiz ({difficulty_display} Difficulty)")
        click.echo(f"Compare poker hands and choose the stronger one.")
        click.echo(f"Questions: {count}\n")
        
        for i in range(count):
            question = self.generate_question()
            questions.append(question)
            
            click.echo(f"Question {i+1}/{count}:")
            click.echo(f"  Hand 1: {question.hand_descriptions[0]}")
            click.echo(f"  Hand 2: {question.hand_descriptions[1]}")
            click.echo()
            
            # Get user input
            while True:
                try:
                    answer = click.prompt("Which hand is stronger? (1 or 2)", type=int)
                    if answer in [1, 2]:
                        user_answer = answer - 1  # Convert to 0-based index
                        break
                    else:
                        click.echo("Please enter 1 or 2")
                except click.Abort:
                    click.echo("\nQuiz cancelled.")
                    return QuizResult(i, correct_count, questions[:i], user_answers, 0.0)
            
            user_answers.append(user_answer)
            
            # Check answer
            if user_answer == question.correct_answer:
                click.echo("✅ Correct!")
                correct_count += 1
            else:
                click.echo("❌ Incorrect.")
                click.echo(f"   {question.explanation}")
            
            click.echo()
        
        accuracy = (correct_count / count) * 100
        
        # Show final results
        click.echo("="*50)
        click.echo(f"Quiz Complete!")
        click.echo(f"Score: {correct_count}/{count} ({accuracy:.1f}%)")
        
        if accuracy >= 90:
            click.echo("🏆 Excellent! You have a strong understanding of hand rankings.")
        elif accuracy >= 75:
            click.echo("👍 Good job! You understand most hand rankings well.")
        elif accuracy >= 60:
            click.echo("📚 Not bad, but there's room for improvement.")
        else:
            click.echo("🤔 Consider reviewing poker hand rankings and try again.")
        
        return QuizResult(count, correct_count, questions, user_answers, accuracy)
    
    def run_quiz(self, count: int, profile: str) -> QuizResult:
        """Run a complete quiz session (can be extended for non-interactive use)."""
        return self.run_interactive_quiz(count)
