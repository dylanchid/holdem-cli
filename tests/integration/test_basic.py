#!/usr/bin/env python3
"""Basic functionality test for Holdem CLI."""

import sys
import os
from pathlib import Path

# Setup standardized imports using test utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
from test_utils import setup_test_imports
src_dir = setup_test_imports()

from holdem_cli.engine.cards import Card, Deck, HandEvaluator, HandRank
from holdem_cli.engine.equity import EquityCalculator, parse_hand_string
from holdem_cli.quiz.hand_ranking import HandRankingQuiz
from holdem_cli.quiz.pot_odds import PotOddsQuiz
from holdem_cli.simulator.ai_player import AIPlayer
from holdem_cli.storage import init_database


def test_cards():
    """Test basic card functionality."""
    print("Testing cards...")
    
    # Test card creation
    card = Card.from_string("As")
    assert str(card) == "As"
    
    # Test deck
    deck = Deck(seed=42)
    deck.shuffle()
    hand = deck.deal(5)
    assert len(hand) == 5
    
    # Test hand evaluation
    evaluator = HandEvaluator()
    strength = evaluator.evaluate_hand(hand)
    assert strength.description in ["High Card", "Pair", "Two Pair", "Three of a Kind", 
                                  "Straight", "Flush", "Full House", "Four of a Kind",
                                  "Straight Flush", "Royal Flush"]
    
    print("✅ Cards working correctly")


def test_equity():
    """Test equity calculation."""
    print("Testing equity...")
    
    calculator = EquityCalculator(seed=42)
    aces = parse_hand_string("AsAh")
    kings = parse_hand_string("KsKh")
    
    result = calculator.calculate_equity(aces, kings, iterations=1000)
    
    # AA should have equity advantage over KK
    assert result.hand1_win > 70
    assert result.hand2_win < 30
    
    print("✅ Equity calculator working correctly")


def test_quiz():
    """Test quiz functionality."""
    print("Testing quiz...")
    
    quiz = HandRankingQuiz(difficulty='easy', seed=42)
    question = quiz.generate_question()
    
    assert len(question.hands) == 2
    assert len(question.hand_descriptions) == 2
    assert question.correct_answer in [0, 1]
    assert len(question.explanation) > 0
    
    print("✅ Quiz working correctly")


def test_ai():
    """Test AI player."""
    print("Testing AI...")
    
    from holdem_cli.simulator.ai_player import GameState, Action
    
    ai = AIPlayer(difficulty='easy', seed=42)
    hole_cards = parse_hand_string("AsKh")
    board = []
    
    game_state = GameState(
        pot_size=100,
        bet_to_call=10,
        current_bet=10,
        position='button',
        street='preflop',
        board=board,
        num_players=2,
        num_active_players=2
    )
    
    action = ai.decide_action(hole_cards, game_state)
    assert action.action in [Action.FOLD, Action.CALL, Action.RAISE]
    
    print("✅ AI working correctly")


def test_database():
    """Test database functionality."""
    print("Testing database...")

    # Create temporary database
    import tempfile
    from pathlib import Path
    from holdem_cli.storage.database import Database
    from typing import Dict, Any

    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)

    try:
        db: Database = init_database(db_path)

        # Test user creation
        user_id: int = db.create_user("test_user")
        user: Dict[str, Any] | None = db.get_user("test_user")
        assert user is not None, "User should exist after creation"
        assert user['name'] == "test_user"

        # Test quiz session
        session_id: int = db.create_quiz_session(user_id, "hand-ranking", 8, 10, "medium")
        db.add_quiz_question(session_id, "Test question", "1", "2", "Test explanation")

        # Test stats
        stats = db.get_user_quiz_stats(user_id)
        assert stats['overall']['total_sessions'] == 1

        db.close()
        print("✅ Database working correctly")

    finally:
        # Clean up
        if db_path.exists():
            db_path.unlink()


def main():
    """Run all tests."""
    print("🎰 Testing Holdem CLI components...\n")
    
    try:
        test_cards()
        test_equity()
        test_quiz()
        test_ai()
        test_database()
        
        print("\n🎉 All tests passed! Holdem CLI is working correctly.")
        print("\nTry running:")
        print("  python -m pip install -e .")
        print("  holdem init")
        print("  holdem quiz hand-ranking --count 3")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
