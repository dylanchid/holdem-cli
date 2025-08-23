"""Pot odds quiz implementation."""

from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
import math

from ..utils.random_utils import get_global_random


@dataclass
class PotOddsQuestion:
    """A single pot odds question."""
    pot_size: int
    bet_to_call: int
    outs: int
    question_text: str
    correct_pot_odds: float
    correct_card_odds: float
    correct_percentage: float
    should_call: bool
    explanation: str


@dataclass
class PotOddsResult:
    """Results from a pot odds quiz."""
    total_questions: int
    correct_answers: int
    questions: List[PotOddsQuestion]
    user_answers: List[bool]
    accuracy: float


class PotOddsQuiz:
    """Quiz for testing pot odds calculation knowledge."""

    def __init__(self, difficulty: str = 'adaptive', seed: Optional[int] = None,
                 db_path: Optional[Path] = None, user_id: Optional[int] = None):
        """Initialize quiz with difficulty and optional seed for testing."""
        self.difficulty = difficulty
        self.adaptive_mode = difficulty == 'adaptive'
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
            if 'pot-odds' in stats['by_type']:
                po_stats = stats['by_type']['pot-odds']

                # Adaptive logic based on recent performance
                recent_accuracy = po_stats['avg_accuracy']

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
    
    def _calculate_pot_odds(self, pot_size: int, bet_to_call: int) -> float:
        """Calculate pot odds as a ratio."""
        total_pot = pot_size + bet_to_call
        return bet_to_call / total_pot
    
    def _calculate_card_odds(self, outs: int, cards_remaining: int = 47) -> float:
        """Calculate odds of hitting outs."""
        return outs / cards_remaining
    
    def _should_call(self, pot_odds: float, card_odds: float) -> bool:
        """Determine if call is profitable based on odds."""
        return card_odds >= pot_odds
    
    def _get_common_scenarios(self) -> List[Dict]:
        """Get common pot odds scenarios based on difficulty."""
        if self.difficulty == 'easy':
            return [
                {'pot': 100, 'bet': 50, 'outs': 9, 'scenario': 'flush draw'},
                {'pot': 80, 'bet': 20, 'outs': 8, 'scenario': 'open-ended straight draw'},
                {'pot': 60, 'bet': 30, 'outs': 4, 'scenario': 'gutshot straight draw'},
                {'pot': 120, 'bet': 40, 'outs': 2, 'scenario': 'pocket pair for set'},
            ]
        elif self.difficulty == 'medium':
            return [
                {'pot': 150, 'bet': 75, 'outs': 15, 'scenario': 'flush draw + overcards'},
                {'pot': 200, 'bet': 50, 'outs': 12, 'scenario': 'combo draw'},
                {'pot': 90, 'bet': 45, 'outs': 6, 'scenario': 'two overcards'},
                {'pot': 180, 'bet': 60, 'outs': 10, 'scenario': 'flush draw with pair'},
            ]
        else:  # hard
            return [
                {'pot': 275, 'bet': 125, 'outs': 14, 'scenario': 'complex combo draw'},
                {'pot': 320, 'bet': 80, 'outs': 7, 'scenario': 'straight draw with overcards'},
                {'pot': 450, 'bet': 150, 'outs': 11, 'scenario': 'flush draw with gutshot'},
                {'pot': 180, 'bet': 90, 'outs': 5, 'scenario': 'weak draw'},
            ]
    
    def generate_question(self) -> PotOddsQuestion:
        """Generate a single pot odds question."""
        # Get current difficulty for adaptive mode
        current_difficulty = self._get_adaptive_difficulty() if self.adaptive_mode else self.difficulty

        # Temporarily set difficulty for scenario selection
        original_difficulty = self.difficulty
        self.difficulty = current_difficulty
        scenarios = self._get_common_scenarios()
        self.difficulty = original_difficulty  # Restore original

        scenario = self._random.choice(scenarios)

        pot_size = scenario['pot']
        bet_to_call = scenario['bet']
        outs = scenario['outs']
        scenario_desc = scenario['scenario']

        # Add some randomization to make each question unique
        pot_size += self._random.randint(-20, 20)
        bet_to_call += self._random.randint(-10, 10)
        
        # Ensure positive values
        pot_size = max(pot_size, 20)
        bet_to_call = max(bet_to_call, 10)
        
        # Calculate odds
        pot_odds = self._calculate_pot_odds(pot_size, bet_to_call)
        card_odds = self._calculate_card_odds(outs)
        percentage = card_odds * 100
        should_call = self._should_call(pot_odds, card_odds)
        
        # Create question text
        question_text = (f"Pot size: ${pot_size}, Bet to call: ${bet_to_call}\n"
                        f"You have {outs} outs ({scenario_desc}).\n"
                        f"Should you call this bet?")
        
        # Create explanation
        pot_odds_ratio = f"{bet_to_call}:{pot_size}"
        required_percentage = pot_odds * 100
        explanation = (f"Pot odds: {pot_odds_ratio} ({required_percentage:.1f}% needed to break even)\n"
                      f"Your odds: {outs}/47 ({percentage:.1f}% chance)\n"
                      f"{'Call' if should_call else 'Fold'} - you {'have' if should_call else 'need'} "
                      f"better odds than required.")
        
        return PotOddsQuestion(
            pot_size=pot_size,
            bet_to_call=bet_to_call,
            outs=outs,
            question_text=question_text,
            correct_pot_odds=pot_odds,
            correct_card_odds=card_odds,
            correct_percentage=percentage,
            should_call=should_call,
            explanation=explanation
        )
    
    def run_interactive_quiz(self, count: int) -> PotOddsResult:
        """Run an interactive quiz session."""
        import click
        
        questions = []
        user_answers = []
        correct_count = 0
        
        current_difficulty = self._get_adaptive_difficulty() if self.adaptive_mode else self.difficulty
        difficulty_display = f"Adaptive ({current_difficulty.title()})" if self.adaptive_mode else f"{self.difficulty.title()}"

        click.echo(f"\n💰 Pot Odds Quiz ({difficulty_display} Difficulty)")
        click.echo(f"Calculate whether you should call based on pot odds.")
        click.echo(f"Questions: {count}\n")
        
        for i in range(count):
            question = self.generate_question()
            questions.append(question)
            
            click.echo(f"Question {i+1}/{count}:")
            click.echo(question.question_text)
            click.echo()
            
            # Get user input
            while True:
                try:
                    answer = click.prompt("Should you call? (y/n)", type=str).lower()
                    if answer in ['y', 'yes', 'call']:
                        user_answer = True
                        break
                    elif answer in ['n', 'no', 'fold']:
                        user_answer = False
                        break
                    else:
                        click.echo("Please enter 'y' for call or 'n' for fold")
                except click.Abort:
                    click.echo("\nQuiz cancelled.")
                    return PotOddsResult(i, correct_count, questions[:i], user_answers, 0.0)
            
            user_answers.append(user_answer)
            
            # Check answer
            if user_answer == question.should_call:
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
            click.echo("🏆 Excellent! You have mastered pot odds calculations.")
        elif accuracy >= 75:
            click.echo("👍 Good job! You understand pot odds well.")
        elif accuracy >= 60:
            click.echo("📚 Not bad, but practice more pot odds scenarios.")
        else:
            click.echo("🤔 Consider studying pot odds fundamentals and try again.")
        
        return PotOddsResult(count, correct_count, questions, user_answers, accuracy)
    
    def run_quiz(self, count: int, profile: str) -> PotOddsResult:
        """Run a complete quiz session (can be extended for non-interactive use)."""
        return self.run_interactive_quiz(count)
