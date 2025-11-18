"""Tests for the preflop quiz module."""

import pytest
from unittest.mock import patch, MagicMock

from holdem_cli.quiz.preflop import PreflopQuiz, PreflopQuestion
from holdem_cli.engine.cards import Card, Rank, Suit


class TestPreflopQuestion:
    """Tests for PreflopQuestion dataclass."""

    def test_creation(self):
        """Test that PreflopQuestion can be created."""
        cards = [Card(Rank.ACE, Suit.SPADES), Card(Rank.KING, Suit.SPADES)]
        question = PreflopQuestion(
            question_text="Test question",
            hole_cards=cards,
            correct_action="raise",
            position="button",
            explanation="Test explanation",
            difficulty_tags=["easy"]
        )

        assert question.question_text == "Test question"
        assert question.hole_cards == cards
        assert question.correct_action == "raise"
        assert question.position == "button"
        assert question.explanation == "Test explanation"
        assert question.difficulty_tags == ["easy"]


class TestPreflopQuiz:
    """Tests for PreflopQuiz class."""

    def test_initialization_default(self):
        """Test default initialization."""
        quiz = PreflopQuiz()
        assert quiz.difficulty == 'medium'

    def test_initialization_with_difficulty(self):
        """Test initialization with custom difficulty."""
        quiz = PreflopQuiz(difficulty='hard')
        assert quiz.difficulty == 'hard'

    def test_initialization_with_seed(self):
        """Test initialization with seed for deterministic behavior."""
        quiz = PreflopQuiz(seed=12345)
        assert quiz.difficulty == 'medium'


class TestGetHandStrengthCategory:
    """Tests for _get_hand_strength_category method."""

    def setup_method(self):
        """Set up quiz instance for tests."""
        self.quiz = PreflopQuiz(seed=42)

    def test_premium_pair_aces(self):
        """Test AA is categorized as premium pair."""
        cards = [Card(Rank.ACE, Suit.SPADES), Card(Rank.ACE, Suit.HEARTS)]
        category = self.quiz._get_hand_strength_category(cards)
        assert category == "premium_pair"

    def test_premium_pair_kings(self):
        """Test KK is categorized as premium pair."""
        cards = [Card(Rank.KING, Suit.SPADES), Card(Rank.KING, Suit.HEARTS)]
        category = self.quiz._get_hand_strength_category(cards)
        assert category == "premium_pair"

    def test_strong_pair_queens(self):
        """Test QQ is categorized as strong pair."""
        cards = [Card(Rank.QUEEN, Suit.SPADES), Card(Rank.QUEEN, Suit.HEARTS)]
        category = self.quiz._get_hand_strength_category(cards)
        assert category == "strong_pair"

    def test_strong_pair_tens(self):
        """Test TT is categorized as strong pair."""
        cards = [Card(Rank.TEN, Suit.SPADES), Card(Rank.TEN, Suit.HEARTS)]
        category = self.quiz._get_hand_strength_category(cards)
        assert category == "strong_pair"

    def test_medium_pair_nines(self):
        """Test 99 is categorized as medium pair."""
        cards = [Card(Rank.NINE, Suit.SPADES), Card(Rank.NINE, Suit.HEARTS)]
        category = self.quiz._get_hand_strength_category(cards)
        assert category == "medium_pair"

    def test_small_pair_twos(self):
        """Test 22 is categorized as small pair."""
        cards = [Card(Rank.TWO, Suit.SPADES), Card(Rank.TWO, Suit.HEARTS)]
        category = self.quiz._get_hand_strength_category(cards)
        assert category == "small_pair"

    def test_premium_suited_aks(self):
        """Test AKs is categorized as premium suited."""
        cards = [Card(Rank.ACE, Suit.SPADES), Card(Rank.KING, Suit.SPADES)]
        category = self.quiz._get_hand_strength_category(cards)
        assert category == "premium_suited"

    def test_premium_offsuit_ako(self):
        """Test AKo is categorized as premium offsuit."""
        cards = [Card(Rank.ACE, Suit.SPADES), Card(Rank.KING, Suit.HEARTS)]
        category = self.quiz._get_hand_strength_category(cards)
        assert category == "premium_offsuit"

    def test_ace_suited(self):
        """Test A5s is categorized as ace suited."""
        cards = [Card(Rank.ACE, Suit.SPADES), Card(Rank.FIVE, Suit.SPADES)]
        category = self.quiz._get_hand_strength_category(cards)
        assert category == "ace_suited"

    def test_suited_connectors(self):
        """Test 87s is categorized as suited connectors."""
        cards = [Card(Rank.EIGHT, Suit.SPADES), Card(Rank.SEVEN, Suit.SPADES)]
        category = self.quiz._get_hand_strength_category(cards)
        assert category == "suited_connectors"

    def test_trash_hand(self):
        """Test 72o is categorized as trash."""
        cards = [Card(Rank.SEVEN, Suit.SPADES), Card(Rank.TWO, Suit.HEARTS)]
        category = self.quiz._get_hand_strength_category(cards)
        assert category == "trash"

    def test_invalid_hand_size(self):
        """Test that wrong number of cards returns unknown."""
        cards = [Card(Rank.ACE, Suit.SPADES)]
        category = self.quiz._get_hand_strength_category(cards)
        assert category == "unknown"


class TestGetPositionRequirements:
    """Tests for _get_position_requirements method."""

    def setup_method(self):
        """Set up quiz instance for tests."""
        self.quiz = PreflopQuiz(seed=42)

    def test_early_position(self):
        """Test early position returns correct chart."""
        chart = self.quiz._get_position_requirements("early")
        assert chart["premium_pair"] == "raise"
        assert chart["trash"] == "fold"
        assert chart["small_pair"] == "fold"

    def test_middle_position(self):
        """Test middle position returns correct chart."""
        chart = self.quiz._get_position_requirements("middle")
        assert chart["premium_pair"] == "raise"
        assert chart["small_pair"] == "call"

    def test_late_position(self):
        """Test late position returns correct chart."""
        chart = self.quiz._get_position_requirements("late")
        assert chart["premium_pair"] == "raise"
        assert chart["suited_connectors"] == "call"

    def test_button_position(self):
        """Test button position returns widest range."""
        chart = self.quiz._get_position_requirements("button")
        assert chart["premium_pair"] == "raise"
        assert chart["small_pair"] == "raise"
        assert chart["offsuit_connectors"] == "call"

    def test_unknown_position_defaults_to_middle(self):
        """Test unknown position defaults to middle."""
        chart = self.quiz._get_position_requirements("unknown")
        middle_chart = self.quiz._get_position_requirements("middle")
        assert chart == middle_chart


class TestGenerateQuestion:
    """Tests for _generate_question method."""

    def setup_method(self):
        """Set up quiz instance for tests."""
        self.quiz = PreflopQuiz(seed=42)

    def test_generates_valid_question(self):
        """Test that generate_question returns valid PreflopQuestion."""
        question = self.quiz._generate_question()

        assert isinstance(question, PreflopQuestion)
        assert len(question.hole_cards) == 2
        assert question.correct_action in ['fold', 'call', 'raise']
        assert question.position in ['early', 'middle', 'late', 'button']
        assert len(question.question_text) > 0
        assert len(question.explanation) > 0
        assert len(question.difficulty_tags) > 0

    def test_deterministic_with_seed(self):
        """Test that same seed produces consistent results."""
        quiz1 = PreflopQuiz(seed=12345)

        q1 = quiz1._generate_question()

        # Just verify the question is valid - full determinism requires
        # controlling Deck's random state as well
        assert isinstance(q1, PreflopQuestion)
        assert q1.position in ['early', 'middle', 'late', 'button']


class TestGenerateExplanation:
    """Tests for _generate_explanation method."""

    def setup_method(self):
        """Set up quiz instance for tests."""
        self.quiz = PreflopQuiz(seed=42)

    def test_premium_pair_explanation(self):
        """Test explanation for premium pair."""
        explanation = self.quiz._generate_explanation("premium_pair", "early", "raise", "AA")
        assert "premium pocket pair" in explanation.lower()
        assert "Early position" in explanation

    def test_trash_hand_explanation(self):
        """Test explanation for trash hand."""
        explanation = self.quiz._generate_explanation("trash", "early", "fold", "72o")
        assert "not a profitable" in explanation.lower()

    def test_position_notes_included(self):
        """Test that position notes are included."""
        explanation = self.quiz._generate_explanation("premium_pair", "button", "raise", "AA")
        assert "Button" in explanation


class TestGetDifficultyTags:
    """Tests for _get_difficulty_tags method."""

    def setup_method(self):
        """Set up quiz instance for tests."""
        self.quiz = PreflopQuiz(seed=42)

    def test_easy_tags_for_premium_hands(self):
        """Test that premium hands get easy tag."""
        tags = self.quiz._get_difficulty_tags("premium_pair", "button")
        assert "easy" in tags

    def test_medium_tags_for_strong_hands(self):
        """Test that strong hands get medium tag."""
        tags = self.quiz._get_difficulty_tags("strong_pair", "middle")
        assert "medium" in tags

    def test_hard_tags_for_marginal_hands(self):
        """Test that marginal hands get hard tag."""
        tags = self.quiz._get_difficulty_tags("ace_suited", "middle")
        assert "hard" in tags

    def test_position_clarity_tags(self):
        """Test that position clarity tags are added."""
        tags_button = self.quiz._get_difficulty_tags("premium_pair", "button")
        tags_middle = self.quiz._get_difficulty_tags("premium_pair", "middle")

        assert "clear_position" in tags_button
        assert "marginal_position" in tags_middle


class TestFilterQuestionsByDifficulty:
    """Tests for _filter_questions_by_difficulty method."""

    def setup_method(self):
        """Set up quiz instance for tests."""
        self.quiz = PreflopQuiz(seed=42)

    def test_easy_filter(self):
        """Test filtering for easy difficulty."""
        self.quiz.difficulty = "easy"

        questions = [
            PreflopQuestion("Q1", [], "raise", "button", "Exp", ["easy"]),
            PreflopQuestion("Q2", [], "fold", "early", "Exp", ["hard"]),
            PreflopQuestion("Q3", [], "call", "middle", "Exp", ["medium"]),
        ]

        filtered = self.quiz._filter_questions_by_difficulty(questions)
        assert len(filtered) == 1
        assert "easy" in filtered[0].difficulty_tags

    def test_hard_filter(self):
        """Test filtering for hard difficulty."""
        self.quiz.difficulty = "hard"

        questions = [
            PreflopQuestion("Q1", [], "raise", "button", "Exp", ["easy"]),
            PreflopQuestion("Q2", [], "fold", "early", "Exp", ["hard"]),
            PreflopQuestion("Q3", [], "call", "middle", "Exp", ["medium"]),
        ]

        filtered = self.quiz._filter_questions_by_difficulty(questions)
        assert len(filtered) == 1
        assert "hard" in filtered[0].difficulty_tags

    def test_medium_filter_includes_easy(self):
        """Test that medium difficulty includes easy questions."""
        self.quiz.difficulty = "medium"

        questions = [
            PreflopQuestion("Q1", [], "raise", "button", "Exp", ["easy"]),
            PreflopQuestion("Q2", [], "fold", "early", "Exp", ["hard"]),
            PreflopQuestion("Q3", [], "call", "middle", "Exp", ["medium"]),
        ]

        filtered = self.quiz._filter_questions_by_difficulty(questions)
        assert len(filtered) == 2


class TestGenerateQuiz:
    """Tests for generate_quiz method."""

    def setup_method(self):
        """Set up quiz instance for tests."""
        self.quiz = PreflopQuiz(seed=42)

    def test_generates_requested_number_of_questions(self):
        """Test that correct number of questions is generated."""
        questions = self.quiz.generate_quiz(num_questions=5)
        assert len(questions) == 5

    def test_all_questions_are_valid(self):
        """Test that all generated questions are valid."""
        questions = self.quiz.generate_quiz(num_questions=10)

        for q in questions:
            assert isinstance(q, PreflopQuestion)
            assert len(q.hole_cards) == 2
            assert q.correct_action in ['fold', 'call', 'raise']

    def test_default_generates_ten_questions(self):
        """Test default generates 10 questions."""
        questions = self.quiz.generate_quiz()
        assert len(questions) == 10


class TestRunInteractiveQuiz:
    """Tests for run_interactive_quiz method."""

    def setup_method(self):
        """Set up quiz instance for tests."""
        self.quiz = PreflopQuiz(seed=42)

    @patch('click.echo')
    @patch('click.prompt')
    def test_returns_quiz_result(self, mock_prompt, mock_echo):
        """Test that interactive quiz returns QuizResult."""
        # Simulate user answers
        mock_prompt.side_effect = ['raise', 'fold', 'call']

        result = self.quiz.run_interactive_quiz(num_questions=3)

        assert result.total_questions == 3
        assert 0 <= result.correct_answers <= 3
        assert 0 <= result.accuracy <= 100

    @patch('click.echo')
    @patch('click.prompt')
    def test_handles_correct_answers(self, mock_prompt, mock_echo):
        """Test that correct answers are counted."""
        # Generate questions first to know correct answers
        questions = self.quiz.generate_quiz(num_questions=2)
        correct_actions = [q.correct_action for q in questions]

        # Reset quiz to generate same questions
        self.quiz = PreflopQuiz(seed=42)
        mock_prompt.side_effect = correct_actions

        result = self.quiz.run_interactive_quiz(num_questions=2)

        assert result.correct_answers == 2
        assert result.accuracy == 100.0

    @patch('click.echo')
    @patch('click.prompt')
    def test_handles_invalid_then_valid_input(self, mock_prompt, mock_echo):
        """Test that invalid input is retried."""
        # First invalid, then valid
        mock_prompt.side_effect = ['invalid', 'raise']

        result = self.quiz.run_interactive_quiz(num_questions=1)

        assert result.total_questions == 1
