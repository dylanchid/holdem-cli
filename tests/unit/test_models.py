"""
Unit tests for data models in holdem_cli.models
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timezone

# Setup path for direct imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from holdem_cli.models.base import (
    BaseModel, TimestampMixin, Identifiable, SoftDeleteMixin,
    VersionedMixin, SearchableMixin
)
from holdem_cli.models.poker import (
    Suit, Rank, Card, Deck, Hand, HandRank, HandStrength, PokerHand
)
from holdem_cli.models.quiz import (
    QuizType, Difficulty, QuestionType, QuizQuestion, QuizAnswer,
    QuizResult, QuizSession, LearningProgress
)


class TestBaseModel:
    """Tests for BaseModel and mixins."""

    def test_timestamp_mixin_defaults(self):
        """Test TimestampMixin has default timestamps."""
        from dataclasses import dataclass

        @dataclass
        class TestModel(TimestampMixin):
            pass

        model = TestModel()
        assert model.created_at is not None
        assert model.updated_at is not None
        assert isinstance(model.created_at, datetime)

    def test_timestamp_mixin_update(self):
        """Test update_timestamp method."""
        from dataclasses import dataclass

        @dataclass
        class TestModel(TimestampMixin):
            pass

        model = TestModel()
        original_updated = model.updated_at
        model.update_timestamp()
        assert model.updated_at >= original_updated

    def test_identifiable_has_id(self):
        """Test Identifiable mixin methods."""
        from dataclasses import dataclass

        @dataclass
        class TestModel(Identifiable):
            pass

        model = TestModel()
        assert model.is_new() is True
        assert model.has_id() is False

        model.id = 1
        assert model.is_new() is False
        assert model.has_id() is True

    def test_soft_delete_mixin(self):
        """Test SoftDeleteMixin functionality."""
        from dataclasses import dataclass

        @dataclass
        class TestModel(SoftDeleteMixin):
            pass

        model = TestModel()
        assert model.is_active() is True
        assert model.is_deleted is False

        model.soft_delete()
        assert model.is_active() is False
        assert model.is_deleted is True
        assert model.deleted_at is not None

        model.restore()
        assert model.is_active() is True
        assert model.is_deleted is False
        assert model.deleted_at is None

    def test_versioned_mixin(self):
        """Test VersionedMixin functionality."""
        from dataclasses import dataclass

        @dataclass
        class TestModel(VersionedMixin):
            pass

        model = TestModel()
        assert model.version == 1

        model.increment_version()
        assert model.version == 2

        info = model.get_version_info()
        assert info['version'] == 2

    def test_searchable_mixin(self):
        """Test SearchableMixin functionality."""
        from dataclasses import dataclass

        @dataclass
        class TestModel(SearchableMixin):
            pass

        model = TestModel()
        model.add_search_keyword("poker")
        model.add_search_keyword("texas holdem")

        assert "poker" in model.search_keywords
        assert model.matches_search("poker") is True
        assert model.matches_search("unknown") is False

        score = model.get_search_score("poker")
        assert score > 0

        model.remove_search_keyword("poker")
        assert "poker" not in model.search_keywords


class TestSuit:
    """Tests for Suit enum."""

    def test_suit_values(self):
        """Test suit symbol values."""
        assert Suit.CLUBS.symbol == "c"
        assert Suit.DIAMONDS.symbol == "d"
        assert Suit.HEARTS.symbol == "h"
        assert Suit.SPADES.symbol == "s"

    def test_suit_colors(self):
        """Test suit colors."""
        assert Suit.HEARTS.color == "red"
        assert Suit.DIAMONDS.color == "red"
        assert Suit.CLUBS.color == "black"
        assert Suit.SPADES.color == "black"


class TestRank:
    """Tests for Rank enum."""

    def test_rank_values(self):
        """Test rank numeric values."""
        assert Rank.TWO.numeric_value == 2
        assert Rank.ACE.numeric_value == 14
        assert Rank.TEN.symbol == "T"
        assert Rank.KING.symbol == "K"

    def test_rank_comparison(self):
        """Test rank comparison operators."""
        assert Rank.ACE > Rank.KING
        assert Rank.KING >= Rank.QUEEN
        assert Rank.TWO < Rank.THREE
        assert Rank.JACK <= Rank.QUEEN

    def test_rank_names(self):
        """Test rank name property."""
        assert Rank.ACE.name == "Ace"
        assert Rank.KING.name == "King"
        assert Rank.TWO.name == "Two"


class TestCard:
    """Tests for Card model."""

    def test_card_creation(self):
        """Test creating a card."""
        card = Card(rank=Rank.ACE, suit=Suit.SPADES)
        assert card.rank == Rank.ACE
        assert card.suit == Suit.SPADES

    def test_card_string(self):
        """Test card string representation."""
        card = Card(rank=Rank.ACE, suit=Suit.SPADES)
        assert str(card) == "As"

    def test_card_from_string(self):
        """Test creating card from string."""
        card = Card.from_string("Kh")
        assert card.rank == Rank.KING
        assert card.suit == Suit.HEARTS

    def test_card_from_string_invalid(self):
        """Test invalid card string raises error."""
        with pytest.raises(ValueError):
            Card.from_string("XY")

        with pytest.raises(ValueError):
            Card.from_string("A")  # Too short

    def test_card_equality(self):
        """Test card equality comparison."""
        card1 = Card(rank=Rank.ACE, suit=Suit.SPADES)
        card2 = Card(rank=Rank.ACE, suit=Suit.SPADES)
        card3 = Card(rank=Rank.KING, suit=Suit.SPADES)

        assert card1 == card2
        assert card1 != card3

    def test_card_hash(self):
        """Test card hashing for use in sets."""
        card1 = Card(rank=Rank.ACE, suit=Suit.SPADES)
        card2 = Card(rank=Rank.ACE, suit=Suit.SPADES)

        card_set = {card1, card2}
        assert len(card_set) == 1

    def test_card_properties(self):
        """Test card property methods."""
        ace = Card(rank=Rank.ACE, suit=Suit.SPADES)
        king = Card(rank=Rank.KING, suit=Suit.HEARTS)
        two = Card(rank=Rank.TWO, suit=Suit.CLUBS)

        assert ace.is_broadway_card is True
        assert king.is_face_card is True
        assert two.is_face_card is False
        assert two.is_broadway_card is False


class TestDeck:
    """Tests for Deck model."""

    def test_deck_initialization(self):
        """Test deck initializes with 52 cards."""
        deck = Deck()
        assert deck.remaining == 52

    def test_deck_deal(self):
        """Test dealing cards from deck."""
        deck = Deck()
        cards = deck.deal(5)

        assert len(cards) == 5
        assert deck.remaining == 47

    def test_deck_deal_one(self):
        """Test dealing single card."""
        deck = Deck()
        card = deck.deal_one()

        assert isinstance(card, Card)
        assert deck.remaining == 51

    def test_deck_deal_too_many(self):
        """Test dealing too many cards raises error."""
        deck = Deck()

        with pytest.raises(ValueError):
            deck.deal(53)

    def test_deck_reset(self):
        """Test deck reset."""
        deck = Deck()
        deck.deal(10)
        deck.reset()

        assert deck.remaining == 52

    def test_deck_is_empty(self):
        """Test is_empty property."""
        deck = Deck()
        assert deck.is_empty is False

        deck.deal(52)
        assert deck.is_empty is True


class TestHand:
    """Tests for Hand model."""

    def test_hand_creation(self):
        """Test creating a hand."""
        hand = Hand()
        assert len(hand) == 0

    def test_hand_add_card(self):
        """Test adding cards to hand."""
        hand = Hand()
        card = Card(rank=Rank.ACE, suit=Suit.SPADES)
        hand.add_card(card)

        assert len(hand) == 1
        assert hand.has_card(card) is True

    def test_hand_remove_card(self):
        """Test removing cards from hand."""
        hand = Hand()
        card = Card(rank=Rank.ACE, suit=Suit.SPADES)
        hand.add_card(card)

        result = hand.remove_card(card)
        assert result is True
        assert len(hand) == 0

        # Try removing non-existent card
        result = hand.remove_card(card)
        assert result is False

    def test_hand_clear(self):
        """Test clearing hand."""
        hand = Hand()
        hand.add_card(Card(rank=Rank.ACE, suit=Suit.SPADES))
        hand.add_card(Card(rank=Rank.KING, suit=Suit.HEARTS))

        hand.clear()
        assert len(hand) == 0

    def test_hand_sort_by_rank(self):
        """Test sorting hand by rank."""
        hand = Hand(cards=[
            Card(rank=Rank.TWO, suit=Suit.CLUBS),
            Card(rank=Rank.ACE, suit=Suit.SPADES),
            Card(rank=Rank.KING, suit=Suit.HEARTS)
        ])

        hand.sort_by_rank()
        assert hand.cards[0].rank == Rank.ACE
        assert hand.cards[1].rank == Rank.KING
        assert hand.cards[2].rank == Rank.TWO

    def test_hand_unique_ranks(self):
        """Test getting unique ranks."""
        hand = Hand(cards=[
            Card(rank=Rank.ACE, suit=Suit.SPADES),
            Card(rank=Rank.ACE, suit=Suit.HEARTS),
            Card(rank=Rank.KING, suit=Suit.CLUBS)
        ])

        ranks = hand.get_unique_ranks()
        assert len(ranks) == 2
        assert Rank.ACE in ranks
        assert Rank.KING in ranks


class TestHandRank:
    """Tests for HandRank enum."""

    def test_hand_rank_values(self):
        """Test hand rank numeric values."""
        assert HandRank.HIGH_CARD.numeric_value == 1
        assert HandRank.ROYAL_FLUSH.numeric_value == 10

    def test_hand_rank_comparison(self):
        """Test hand rank comparison."""
        assert HandRank.ROYAL_FLUSH > HandRank.STRAIGHT_FLUSH
        assert HandRank.PAIR < HandRank.TWO_PAIR
        assert HandRank.FULL_HOUSE >= HandRank.FULL_HOUSE


class TestHandStrength:
    """Tests for HandStrength model."""

    def test_hand_strength_creation(self):
        """Test creating hand strength."""
        strength = HandStrength(
            rank=HandRank.PAIR,
            primary_rank=Rank.ACE
        )
        assert str(strength) == "Pair"

    def test_hand_strength_comparison(self):
        """Test hand strength comparison."""
        strength1 = HandStrength(rank=HandRank.PAIR, primary_rank=Rank.ACE)
        strength2 = HandStrength(rank=HandRank.PAIR, primary_rank=Rank.KING)
        strength3 = HandStrength(rank=HandRank.TWO_PAIR, primary_rank=Rank.TWO)

        assert strength1 > strength2  # Ace pair beats King pair
        assert strength3 > strength1  # Two pair beats pair

    def test_hand_strength_description(self):
        """Test hand strength description."""
        pair = HandStrength(rank=HandRank.PAIR, primary_rank=Rank.ACE)
        assert "Aces" in pair.description

        full_house = HandStrength(
            rank=HandRank.FULL_HOUSE,
            primary_rank=Rank.ACE,
            secondary_rank=Rank.KING
        )
        assert "Aces" in full_house.description
        assert "Kings" in full_house.description


class TestPokerHand:
    """Tests for PokerHand model."""

    def test_poker_hand_creation(self):
        """Test creating poker hand."""
        hole_cards = [
            Card(rank=Rank.ACE, suit=Suit.SPADES),
            Card(rank=Rank.KING, suit=Suit.SPADES)
        ]
        hand = PokerHand(hole_cards=hole_cards)

        assert len(hand.hole_cards) == 2
        assert hand.total_cards == 2

    def test_poker_hand_validation(self):
        """Test poker hand validation."""
        # Valid hand
        hand = PokerHand(
            hole_cards=[
                Card(rank=Rank.ACE, suit=Suit.SPADES),
                Card(rank=Rank.KING, suit=Suit.SPADES)
            ]
        )
        assert hand.is_valid() is True
        assert len(hand.validate()) == 0

        # Invalid - too many hole cards
        invalid_hand = PokerHand(
            hole_cards=[
                Card(rank=Rank.ACE, suit=Suit.SPADES),
                Card(rank=Rank.KING, suit=Suit.SPADES),
                Card(rank=Rank.QUEEN, suit=Suit.SPADES)
            ]
        )
        issues = invalid_hand.validate()
        assert len(issues) > 0


class TestQuizQuestion:
    """Tests for QuizQuestion model."""

    def test_quiz_question_creation(self):
        """Test creating quiz question."""
        question = QuizQuestion(
            question_text="Which hand is stronger?",
            options=["Pair of Aces", "Pair of Kings"],
            correct_answer=0,
            explanation="Aces beat Kings"
        )

        assert question.question_text == "Which hand is stronger?"
        assert len(question.options) == 2

    def test_quiz_question_validation(self):
        """Test quiz question validation."""
        # Valid question
        question = QuizQuestion(
            question_text="Test question",
            options=["A", "B"],
            correct_answer=0,
            explanation="Test explanation"
        )
        assert len(question.validate()) == 0

        # Invalid - empty question
        invalid_question = QuizQuestion(
            question_text="",
            options=["A", "B"],
            correct_answer=0,
            explanation="Test"
        )
        issues = invalid_question.validate()
        assert any("empty" in issue.lower() for issue in issues)

    def test_quiz_question_is_correct_answer(self):
        """Test checking correct answer."""
        question = QuizQuestion(
            question_text="Test",
            options=["A", "B"],
            correct_answer=0,
            explanation="Test"
        )

        assert question.is_correct_answer(0) is True
        assert question.is_correct_answer(1) is False

    def test_quiz_question_formatted(self):
        """Test formatted question text."""
        question = QuizQuestion(
            question_text="Test question?",
            options=["Option A", "Option B"],
            correct_answer=0,
            explanation="Test"
        )

        formatted = question.get_formatted_question()
        assert "Test question?" in formatted
        assert "Option A" in formatted
        assert "Option B" in formatted


class TestQuizAnswer:
    """Tests for QuizAnswer model."""

    def test_quiz_answer_creation(self):
        """Test creating quiz answer."""
        answer = QuizAnswer(
            question_id=1,
            user_answer=0,
            is_correct=True,
            time_to_answer_seconds=5.0
        )

        assert answer.question_id == 1
        assert answer.is_correct is True

    def test_quiz_answer_score_calculation(self):
        """Test score calculation."""
        # Correct answer with quick time
        answer = QuizAnswer(
            question_id=1,
            user_answer=0,
            is_correct=True,
            time_to_answer_seconds=5.0
        )
        score = answer.calculate_score()
        assert score > 0.8

        # Incorrect answer
        wrong_answer = QuizAnswer(
            question_id=1,
            user_answer=1,
            is_correct=False,
            time_to_answer_seconds=5.0
        )
        wrong_score = wrong_answer.calculate_score()
        assert wrong_score < score


class TestQuizResult:
    """Tests for QuizResult model."""

    def test_quiz_result_creation(self):
        """Test creating quiz result."""
        result = QuizResult(
            quiz_type=QuizType.HAND_RANKING,
            total_questions=10,
            correct_answers=8,
            total_time_seconds=120.0,
            difficulty=Difficulty.MEDIUM
        )

        assert result.accuracy == 0.8
        assert result.average_time_per_question == 12.0

    def test_quiz_result_performance_summary(self):
        """Test performance summary."""
        result = QuizResult(
            quiz_type=QuizType.HAND_RANKING,
            total_questions=10,
            correct_answers=8,
            total_time_seconds=120.0,
            difficulty=Difficulty.MEDIUM
        )

        summary = result.get_performance_summary()
        assert summary['accuracy'] == 0.8
        assert summary['total_questions'] == 10


class TestQuizSession:
    """Tests for QuizSession model."""

    def test_quiz_session_creation(self):
        """Test creating quiz session."""
        session = QuizSession(
            user_id=1,
            quiz_type=QuizType.HAND_RANKING,
            difficulty=Difficulty.MEDIUM
        )

        assert session.user_id == 1
        assert session.is_completed is False

    def test_quiz_session_start_end(self):
        """Test session start and end."""
        session = QuizSession(
            user_id=1,
            quiz_type=QuizType.HAND_RANKING,
            difficulty=Difficulty.MEDIUM
        )

        session.start()
        assert session.start_time is not None

        session.end()
        assert session.is_completed is True
        assert session.duration_seconds > 0

    def test_quiz_session_progress(self):
        """Test session progress tracking."""
        session = QuizSession(
            user_id=1,
            quiz_type=QuizType.HAND_RANKING,
            difficulty=Difficulty.MEDIUM,
            question_count=10
        )

        assert session.progress_percentage == 0.0

        # Record some answers
        answer = QuizAnswer(question_id=1, user_answer=0, is_correct=True)
        session.record_answer(answer)

        assert session.progress_percentage == 10.0
        assert session.questions_answered == 1
        assert session.questions_correct == 1


class TestLearningProgress:
    """Tests for LearningProgress model."""

    def test_learning_progress_creation(self):
        """Test creating learning progress."""
        progress = LearningProgress(user_id=1)

        assert progress.user_id == 1
        assert progress.total_quizzes_completed == 0

    def test_learning_progress_skill_update(self):
        """Test updating skill progress."""
        progress = LearningProgress(user_id=1)

        progress.update_skill_progress("hand_ranking", True)
        progress.update_skill_progress("hand_ranking", True)
        progress.update_skill_progress("hand_ranking", False)

        assert "hand_ranking" in progress.skill_accuracy
        assert progress.skill_attempts["hand_ranking"] == 3
        # 2 correct out of 3
        assert abs(progress.skill_accuracy["hand_ranking"] - 0.666) < 0.01

    def test_learning_progress_weakest_skills(self):
        """Test getting weakest skills."""
        progress = LearningProgress(user_id=1)

        # Add skills with different accuracy
        progress.skill_accuracy = {
            "hand_ranking": 0.9,
            "pot_odds": 0.5,
            "ranges": 0.3
        }

        weakest = progress.get_weakest_skills(limit=2)
        assert weakest[0] == "ranges"
        assert weakest[1] == "pot_odds"

    def test_learning_progress_strongest_skills(self):
        """Test getting strongest skills."""
        progress = LearningProgress(user_id=1)

        progress.skill_accuracy = {
            "hand_ranking": 0.9,
            "pot_odds": 0.5,
            "ranges": 0.3
        }

        strongest = progress.get_strongest_skills(limit=2)
        assert strongest[0] == "hand_ranking"
        assert strongest[1] == "pot_odds"
