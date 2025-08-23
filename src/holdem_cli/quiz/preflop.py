"""Pre-flop starting hand evaluation quiz implementation."""

from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass

from ..engine.cards import Card, Deck, Rank, Suit
from ..utils.random_utils import get_global_random
from .hand_ranking import QuizResult  # Reuse the result structure


@dataclass
class PreflopQuestion:
    """A single preflop quiz question."""
    question_text: str
    hole_cards: List[Card]
    correct_action: str  # 'fold', 'call', 'raise'
    position: str
    explanation: str
    difficulty_tags: List[str]


class PreflopQuiz:
    """Quiz for testing preflop starting hand knowledge."""
    
    def __init__(self, difficulty: str = 'medium', seed: Optional[int] = None):
        """Initialize quiz with difficulty and optional seed for testing."""
        self.difficulty = difficulty
        self._random = get_global_random()
        if seed is not None:
            self._random.seed(seed)
    
    def _get_hand_strength_category(self, cards: List[Card]) -> str:
        """Categorize hand strength for preflop evaluation."""
        if len(cards) != 2:
            return "unknown"
        
        card1, card2 = cards
        
        # Pocket pairs
        if card1.rank == card2.rank:
            rank_value = card1.rank.numeric_value
            if rank_value >= 13:  # KK+
                return "premium_pair"
            elif rank_value >= 10:  # TT-QQ
                return "strong_pair"
            elif rank_value >= 7:   # 77-99
                return "medium_pair"
            else:                   # 22-66
                return "small_pair"
        
        # Non-pairs
        suited = card1.suit == card2.suit
        high_card = max(card1.rank.numeric_value, card2.rank.numeric_value)
        low_card = min(card1.rank.numeric_value, card2.rank.numeric_value)
        gap = high_card - low_card
        
        # Premium hands
        if (high_card == 14 and low_card >= 12) or (high_card == 13 and low_card == 12):  # AK, AQ, KQ
            return "premium_suited" if suited else "premium_offsuit"
        
        # Strong broadways
        if high_card >= 12 and low_card >= 10:  # AJ, AT, KJ, KT, QJ, QT, JT
            return "strong_suited" if suited else "strong_offsuit"
        
        # Ace-rag suited
        if high_card == 14 and suited and low_card <= 9:
            return "ace_suited"
        
        # King-rag suited
        if high_card == 13 and suited and low_card <= 9:
            return "king_suited"
        
        # Suited connectors
        if suited and gap <= 1:
            return "suited_connectors"
        
        # One-gappers suited
        if suited and gap == 2:
            return "suited_one_gapper"
        
        # Small suited cards
        if suited and high_card <= 10:
            return "small_suited"
        
        # Offsuit hands
        if gap <= 1 and high_card >= 8:
            return "offsuit_connectors"
        
        return "trash"
    
    def _get_position_requirements(self, position: str) -> Dict[str, str]:
        """Get recommended actions by hand category for different positions."""
        position_charts = {
            "early": {
                "premium_pair": "raise",
                "strong_pair": "raise", 
                "medium_pair": "call",
                "small_pair": "fold",
                "premium_suited": "raise",
                "premium_offsuit": "raise",
                "strong_suited": "call",
                "strong_offsuit": "fold",
                "ace_suited": "fold",
                "king_suited": "fold",
                "suited_connectors": "fold",
                "suited_one_gapper": "fold",
                "small_suited": "fold",
                "offsuit_connectors": "fold",
                "trash": "fold"
            },
            "middle": {
                "premium_pair": "raise",
                "strong_pair": "raise",
                "medium_pair": "call",
                "small_pair": "call",
                "premium_suited": "raise",
                "premium_offsuit": "raise",
                "strong_suited": "call",
                "strong_offsuit": "call",
                "ace_suited": "call",
                "king_suited": "fold",
                "suited_connectors": "call",
                "suited_one_gapper": "fold",
                "small_suited": "fold",
                "offsuit_connectors": "fold",
                "trash": "fold"
            },
            "late": {
                "premium_pair": "raise",
                "strong_pair": "raise",
                "medium_pair": "raise",
                "small_pair": "call",
                "premium_suited": "raise",
                "premium_offsuit": "raise",
                "strong_suited": "raise",
                "strong_offsuit": "call",
                "ace_suited": "call",
                "king_suited": "call",
                "suited_connectors": "call",
                "suited_one_gapper": "call",
                "small_suited": "call",
                "offsuit_connectors": "call",
                "trash": "fold"
            },
            "button": {
                "premium_pair": "raise",
                "strong_pair": "raise", 
                "medium_pair": "raise",
                "small_pair": "raise",
                "premium_suited": "raise",
                "premium_offsuit": "raise",
                "strong_suited": "raise",
                "strong_offsuit": "raise",
                "ace_suited": "raise",
                "king_suited": "call",
                "suited_connectors": "call",
                "suited_one_gapper": "call",
                "small_suited": "call",
                "offsuit_connectors": "call",
                "trash": "fold"
            }
        }
        
        return position_charts.get(position, position_charts["middle"])
    
    def _generate_question(self) -> PreflopQuestion:
        """Generate a single preflop question."""
        # Create deck and deal random hand
        deck = Deck()
        hole_cards = deck.deal(2)
        
        # Choose random position
        positions = ["early", "middle", "late", "button"]
        position = self._random.choice(positions)
        
        # Determine hand category and correct action
        hand_category = self._get_hand_strength_category(hole_cards)
        position_chart = self._get_position_requirements(position)
        correct_action = position_chart[hand_category]
        
        # Format hand string
        hand_str = f"{hole_cards[0]}{hole_cards[1]}"
        if hole_cards[0].rank == hole_cards[1].rank:
            hand_display = f"{hole_cards[0].rank.symbol}{hole_cards[1].rank.symbol}"
        elif hole_cards[0].suit == hole_cards[1].suit:
            hand_display = f"{hole_cards[0].rank.symbol}{hole_cards[1].rank.symbol}s"
        else:
            hand_display = f"{hole_cards[0].rank.symbol}{hole_cards[1].rank.symbol}o"
        
        question_text = f"You are dealt {hand_display} in {position} position. What should you do?"
        
        # Generate explanation
        explanation = self._generate_explanation(hand_category, position, correct_action, hand_display)
        
        # Difficulty tags
        difficulty_tags = self._get_difficulty_tags(hand_category, position)
        
        return PreflopQuestion(
            question_text=question_text,
            hole_cards=hole_cards,
            correct_action=correct_action,
            position=position,
            explanation=explanation,
            difficulty_tags=difficulty_tags
        )
    
    def _generate_explanation(self, hand_category: str, position: str, action: str, hand_display: str) -> str:
        """Generate explanation for the correct action."""
        explanations = {
            "premium_pair": f"{hand_display} is a premium pocket pair. Always raise for value from any position.",
            "strong_pair": f"{hand_display} is a strong pocket pair. Raise for value from most positions.",
            "medium_pair": f"{hand_display} is a medium pocket pair. Play depends on position - can raise in late position, call in early/middle.",
            "small_pair": f"{hand_display} is a small pocket pair. Look to set-mine when the odds are right, fold in early position.",
            "premium_suited": f"{hand_display} is a premium suited hand. Raise for value from any position.",
            "premium_offsuit": f"{hand_display} is a premium offsuit hand. Raise for value, though less strong than suited version.",
            "strong_suited": f"{hand_display} is a strong suited hand. Play aggressively in late position, more carefully in early position.",
            "strong_offsuit": f"{hand_display} is a strong offsuit hand. Playable in late position but can be folded in early position.",
            "ace_suited": f"{hand_display} has good blocker value and flush potential. Can be played in late position.",
            "king_suited": f"{hand_display} has some potential but should be played carefully. Position matters a lot.",
            "suited_connectors": f"{hand_display} has straight and flush potential. Best played in late position with good implied odds.",
            "suited_one_gapper": f"{hand_display} has some drawing potential but should be played selectively.",
            "small_suited": f"{hand_display} has limited potential. Only playable in very favorable conditions.",
            "offsuit_connectors": f"{hand_display} has some straight potential but lacks the flush draw. Play carefully.",
            "trash": f"{hand_display} is not a profitable hand to play from {position} position."
        }
        
        base_explanation = explanations.get(hand_category, f"{hand_display} should be {action} in {position} position.")
        
        position_notes = {
            "early": "Early position requires tight play due to many players acting after you.",
            "middle": "Middle position allows for slightly looser play but still requires caution.",
            "late": "Late position allows you to play more hands due to positional advantage.",
            "button": "Button is the best position - you act last post-flop, allowing for wider ranges."
        }
        
        return f"{base_explanation} {position_notes[position]}"
    
    def _get_difficulty_tags(self, hand_category: str, position: str) -> List[str]:
        """Get difficulty tags for the question."""
        tags = []
        
        # Hand-based difficulty
        if hand_category in ["premium_pair", "premium_suited", "trash"]:
            tags.append("easy")
        elif hand_category in ["strong_pair", "medium_pair", "strong_suited"]:
            tags.append("medium") 
        else:
            tags.append("hard")
        
        # Position-based difficulty
        if position in ["early", "button"]:
            tags.append("clear_position")
        else:
            tags.append("marginal_position")
        
        return tags
    
    def _filter_questions_by_difficulty(self, questions: List[PreflopQuestion]) -> List[PreflopQuestion]:
        """Filter questions based on difficulty setting."""
        if self.difficulty == "easy":
            return [q for q in questions if "easy" in q.difficulty_tags]
        elif self.difficulty == "hard":
            return [q for q in questions if "hard" in q.difficulty_tags]
        else:  # medium
            return [q for q in questions if "medium" in q.difficulty_tags or "easy" in q.difficulty_tags]
    
    def generate_quiz(self, num_questions: int = 10) -> List[PreflopQuestion]:
        """Generate a set of quiz questions."""
        # Generate more questions than needed
        all_questions = []
        for _ in range(num_questions * 3):  # Generate 3x to allow filtering
            question = self._generate_question()
            all_questions.append(question)
        
        # Filter by difficulty
        filtered_questions = self._filter_questions_by_difficulty(all_questions)
        
        # Remove duplicates based on hand and position combination
        unique_questions = []
        seen_combinations = set()
        
        for question in filtered_questions:
            hand_str = f"{question.hole_cards[0]}{question.hole_cards[1]}"
            combination = (hand_str, question.position)
            if combination not in seen_combinations:
                unique_questions.append(question)
                seen_combinations.add(combination)
                
                if len(unique_questions) >= num_questions:
                    break
        
        # If we don't have enough unique questions, generate more
        while len(unique_questions) < num_questions:
            question = self._generate_question()
            unique_questions.append(question)
        
        return unique_questions[:num_questions]
    
    def run_interactive_quiz(self, num_questions: int = 10) -> QuizResult:
        """Run an interactive preflop quiz."""
        import click
        
        questions = self.generate_quiz(num_questions)
        user_answers = []
        correct_count = 0
        
        click.echo(f"\\n🎯 Starting Preflop Starting Hand Quiz ({self.difficulty} difficulty)")
        click.echo(f"📚 Answer 'fold', 'call', or 'raise' for each scenario\\n")
        
        for i, question in enumerate(questions, 1):
            click.echo(f"Question {i}/{num_questions}")
            click.echo(f"{question.question_text}")
            
            while True:
                try:
                    answer = click.prompt("Your action", type=str).lower().strip()
                    if answer in ['fold', 'call', 'raise']:
                        break
                    else:
                        click.echo("Please answer 'fold', 'call', or 'raise'")
                except click.Abort:
                    click.echo("\\nQuiz cancelled.")
                    return QuizResult(0, 0, [], [], 0.0)
            
            user_answers.append(answer)
            
            if answer == question.correct_action:
                correct_count += 1
                click.echo(f"✅ Correct! {question.explanation}")
            else:
                click.echo(f"❌ Incorrect. Correct answer: {question.correct_action}")
                click.echo(f"💡 {question.explanation}")
            
            click.echo()  # Empty line
        
        # Calculate results
        accuracy = (correct_count / num_questions) * 100
        
        click.echo(f"\\n📊 Quiz Results:")
        click.echo(f"Score: {correct_count}/{num_questions} ({accuracy:.1f}%)")
        
        if accuracy >= 90:
            click.echo("🏆 Excellent! You have strong preflop fundamentals.")
        elif accuracy >= 75:
            click.echo("👍 Good work! Keep practicing the marginal spots.")
        elif accuracy >= 60:
            click.echo("📖 Not bad, but study position-based starting hand charts.")
        else:
            click.echo("📚 Focus on learning tight preflop ranges first.")
        
        # Convert to QuizResult format for compatibility
        quiz_questions = []
        for question in questions:
            # Create a fake multiple choice format for compatibility
            choices = ['fold', 'call', 'raise']
            correct_idx = choices.index(question.correct_action)
            
            quiz_questions.append(type('Question', (), {
                'question_text': question.question_text,
                'correct_answer': correct_idx,
                'explanation': question.explanation
            })())
        
        user_answer_indices = [['fold', 'call', 'raise'].index(ans) for ans in user_answers]
        
        return QuizResult(
            total_questions=num_questions,
            correct_answers=correct_count,
            questions=quiz_questions,
            user_answers=user_answer_indices,
            accuracy=accuracy
        )
