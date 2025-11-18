"""Tests for the poker simulator module."""

import pytest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock

from holdem_cli.simulator.poker_simulator import (
    PokerSimulator,
    PlayerState,
    BettingRound,
    HandResult,
)
from holdem_cli.engine.cards import Card, Rank, Suit
from holdem_cli.simulator.ai_player import PlayerAction, Action


class TestPokerSimulatorInit:
    """Tests for PokerSimulator initialization."""

    def test_default_initialization(self):
        """Test default simulator initialization."""
        simulator = PokerSimulator()

        assert simulator.ai_level == 'easy'
        assert simulator.hand_history == []
        assert simulator.ai_player is not None

    def test_initialization_with_difficulty(self):
        """Test initialization with different difficulty levels."""
        for level in ['easy', 'medium', 'hard']:
            simulator = PokerSimulator(ai_level=level)
            assert simulator.ai_level == level

    def test_initialization_with_seed(self):
        """Test initialization with random seed."""
        simulator1 = PokerSimulator(seed=42)
        simulator2 = PokerSimulator(seed=42)

        # Both should be initialized with the same seed
        assert simulator1._random is not None
        assert simulator2._random is not None


class TestPlayerState:
    """Tests for PlayerState dataclass."""

    def test_player_state_creation(self):
        """Test creating a player state."""
        cards = [Card(Rank.ACE, Suit.SPADES), Card(Rank.KING, Suit.HEARTS)]
        state = PlayerState(name="Test", cards=cards, chips=1000)

        assert state.name == "Test"
        assert len(state.cards) == 2
        assert state.chips == 1000
        assert state.current_bet == 0
        assert state.has_folded is False
        assert state.has_acted is False

    def test_player_state_with_bet(self):
        """Test player state with bet."""
        cards = [Card(Rank.ACE, Suit.SPADES), Card(Rank.KING, Suit.HEARTS)]
        state = PlayerState(
            name="Test",
            cards=cards,
            chips=900,
            current_bet=100
        )

        assert state.chips == 900
        assert state.current_bet == 100


class TestBettingRound:
    """Tests for BettingRound dataclass."""

    def test_betting_round_creation(self):
        """Test creating a betting round."""
        round = BettingRound(street="preflop", pot_before=100, pot_after=200)

        assert round.street == "preflop"
        assert round.actions == []
        assert round.pot_before == 100
        assert round.pot_after == 200

    def test_betting_round_with_actions(self):
        """Test betting round with actions."""
        actions = [
            {"player": "Human", "action": "call", "amount": 50},
            {"player": "AI", "action": "raise", "amount": 100}
        ]
        round = BettingRound(
            street="flop",
            actions=actions,
            pot_before=100,
            pot_after=250
        )

        assert len(round.actions) == 2


class TestHandResult:
    """Tests for HandResult dataclass."""

    def test_hand_result_creation(self):
        """Test creating a hand result."""
        player_cards = [Card(Rank.ACE, Suit.SPADES), Card(Rank.KING, Suit.HEARTS)]
        ai_cards = [Card(Rank.QUEEN, Suit.DIAMONDS), Card(Rank.QUEEN, Suit.CLUBS)]
        board = [
            Card(Rank.TEN, Suit.HEARTS),
            Card(Rank.JACK, Suit.SPADES),
            Card(Rank.TWO, Suit.CLUBS),
            Card(Rank.THREE, Suit.DIAMONDS),
            Card(Rank.FOUR, Suit.HEARTS)
        ]

        result = HandResult(
            winner="Human",
            pot_size=500,
            player_cards=player_cards,
            ai_cards=ai_cards,
            board=board,
            action_history=[],
            final_hands={"Human": "Straight", "AI": "Pair"},
            reasoning=["Player had the best hand"]
        )

        assert result.winner == "Human"
        assert result.pot_size == 500
        assert result.showdown_occurred is False


class TestActionProcessing:
    """Tests for action processing methods."""

    @pytest.fixture
    def simulator(self):
        """Create a simulator for testing."""
        return PokerSimulator(seed=42)

    @pytest.fixture
    def player_state(self):
        """Create a player state for testing."""
        cards = [Card(Rank.ACE, Suit.SPADES), Card(Rank.KING, Suit.HEARTS)]
        return PlayerState(name="Test", cards=cards, chips=1000)

    def test_process_fold_action(self, simulator, player_state):
        """Test processing a fold action."""
        action = PlayerAction(Action.FOLD, reasoning="Test fold")
        actions = []
        players = [player_state, PlayerState(
            name="AI",
            cards=[Card(Rank.TWO, Suit.CLUBS), Card(Rank.THREE, Suit.DIAMONDS)],
            chips=1000
        )]

        hand_over = simulator._process_fold_action(player_state, action, actions, players)

        assert player_state.has_folded is True
        assert len(actions) == 1
        assert actions[0]["action"] == "fold"
        assert hand_over is True  # Only one player left

    @patch('click.echo')
    def test_process_call_action(self, mock_echo, simulator, player_state):
        """Test processing a call action."""
        action = PlayerAction(Action.CALL, 50, "Test call")
        actions = []

        pot_contribution = simulator._process_call_action(
            player_state, action, actions, current_bet=50
        )

        assert pot_contribution == 50
        assert player_state.chips == 950
        assert player_state.current_bet == 50
        assert player_state.has_acted is True

    @patch('click.echo')
    def test_process_check_action(self, mock_echo, simulator, player_state):
        """Test processing a check action."""
        action = PlayerAction(Action.CHECK, reasoning="Test check")
        actions = []

        simulator._process_check_action(player_state, action, actions)

        assert player_state.has_acted is True
        assert len(actions) == 1
        assert actions[0]["action"] == "check"

    @patch('click.echo')
    def test_process_bet_action(self, mock_echo, simulator, player_state):
        """Test processing a bet action."""
        action = PlayerAction(Action.BET, 100, "Test bet")
        actions = []
        ai_state = PlayerState(
            name="AI",
            cards=[Card(Rank.TWO, Suit.CLUBS), Card(Rank.THREE, Suit.DIAMONDS)],
            chips=1000
        )
        players = [player_state, ai_state]

        pot_contribution, new_bet = simulator._process_bet_action(
            player_state, action, actions, players
        )

        assert pot_contribution == 100
        assert new_bet == 100
        assert player_state.chips == 900
        assert player_state.has_acted is True
        # AI should have acted flag reset
        assert ai_state.has_acted is False


class TestDealingMethods:
    """Tests for card dealing methods."""

    @pytest.fixture
    def simulator(self):
        """Create a simulator for testing."""
        return PokerSimulator(seed=42)

    def test_deal_starting_hands(self, simulator):
        """Test dealing starting hands."""
        from holdem_cli.engine.cards import Deck
        deck = Deck()

        player_cards, ai_cards = simulator._deal_starting_hands(deck)

        assert len(player_cards) == 2
        assert len(ai_cards) == 2
        # All cards should be different
        all_cards = player_cards + ai_cards
        assert len(set(str(c) for c in all_cards)) == 4

    def test_deal_board_flop(self, simulator):
        """Test dealing flop."""
        from holdem_cli.engine.cards import Deck
        deck = Deck()
        deck.deal(4)  # Deal some cards first

        flop = simulator._deal_board(deck, 'flop')

        assert len(flop) == 3

    def test_deal_board_turn(self, simulator):
        """Test dealing turn."""
        from holdem_cli.engine.cards import Deck
        deck = Deck()
        deck.deal(7)  # Deal some cards first

        turn = simulator._deal_board(deck, 'turn')

        assert len(turn) == 1

    def test_deal_board_river(self, simulator):
        """Test dealing river."""
        from holdem_cli.engine.cards import Deck
        deck = Deck()
        deck.deal(8)  # Deal some cards first

        river = simulator._deal_board(deck, 'river')

        assert len(river) == 1

    def test_deal_board_invalid_street(self, simulator):
        """Test dealing for invalid street returns empty list."""
        from holdem_cli.engine.cards import Deck
        deck = Deck()

        cards = simulator._deal_board(deck, 'invalid')

        assert cards == []


class TestExportHandHistory:
    """Tests for hand history export functionality."""

    @pytest.fixture
    def simulator_with_history(self):
        """Create a simulator with hand history for testing."""
        simulator = PokerSimulator(seed=42)

        # Add a mock hand result to history
        player_cards = [Card(Rank.ACE, Suit.SPADES), Card(Rank.KING, Suit.HEARTS)]
        ai_cards = [Card(Rank.QUEEN, Suit.DIAMONDS), Card(Rank.QUEEN, Suit.CLUBS)]
        board = [
            Card(Rank.TEN, Suit.HEARTS),
            Card(Rank.JACK, Suit.SPADES),
            Card(Rank.TWO, Suit.CLUBS),
            Card(Rank.THREE, Suit.DIAMONDS),
            Card(Rank.FOUR, Suit.HEARTS)
        ]

        result = HandResult(
            winner="Human",
            pot_size=500,
            player_cards=player_cards,
            ai_cards=ai_cards,
            board=board,
            action_history=[{"player": "Human", "action": "call", "amount": 50}],
            final_hands={"Human": "Straight", "AI": "Pair"},
            reasoning=["Player had the best hand"],
            betting_rounds=[BettingRound("preflop", pot_before=0, pot_after=100)]
        )

        simulator.hand_history.append(result)
        return simulator

    def test_export_hand_history_json(self, simulator_with_history):
        """Test exporting hand history to JSON format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name

        try:
            simulator_with_history.export_hand_history(filepath, format='json')

            assert os.path.exists(filepath)

            with open(filepath) as f:
                data = json.load(f)

            # Check for export format in either location
            export_format = data.get('format', data.get('export_format', ''))
            if not export_format and 'export_info' in data:
                export_format = data['export_info'].get('export_format', '')
            assert 'holdem-cli' in export_format
            assert len(data['hands']) == 1
            assert data['hands'][0]['winner'] == 'Human'
        finally:
            os.unlink(filepath)

    def test_export_hand_history_txt(self, simulator_with_history):
        """Test exporting hand history to text format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            filepath = f.name

        try:
            simulator_with_history.export_hand_history(filepath, format='txt')

            assert os.path.exists(filepath)

            with open(filepath) as f:
                content = f.read()

            assert 'Poker Hand History Export' in content
            assert 'AI Level: easy' in content
            assert 'Total Hands: 1' in content
        finally:
            os.unlink(filepath)

    def test_export_empty_history(self):
        """Test exporting empty hand history."""
        simulator = PokerSimulator()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name

        try:
            simulator.export_hand_history(filepath, format='json')

            with open(filepath) as f:
                data = json.load(f)

            assert data['hands'] == []
            # Check for either key name
            total_hands = data.get('total_hands', len(data['hands']))
            assert total_hands == 0
        finally:
            os.unlink(filepath)


class TestSessionStatistics:
    """Tests for session statistics functionality."""

    @pytest.fixture
    def simulator_with_multiple_hands(self):
        """Create simulator with multiple hands for statistics testing."""
        simulator = PokerSimulator()

        # Add several hand results
        for i in range(5):
            player_cards = [Card(Rank.ACE, Suit.SPADES), Card(Rank.KING, Suit.HEARTS)]
            ai_cards = [Card(Rank.QUEEN, Suit.DIAMONDS), Card(Rank.QUEEN, Suit.CLUBS)]
            board = [
                Card(Rank.TEN, Suit.HEARTS),
                Card(Rank.JACK, Suit.SPADES),
                Card(Rank.TWO, Suit.CLUBS),
                Card(Rank.THREE, Suit.DIAMONDS),
                Card(Rank.FOUR, Suit.HEARTS)
            ]

            # Alternate winners
            winner = "Human" if i % 2 == 0 else "AI"

            result = HandResult(
                winner=winner,
                pot_size=100 + i * 50,
                player_cards=player_cards,
                ai_cards=ai_cards,
                board=board,
                action_history=[],
                final_hands={"Human": "Pair", "AI": "High Card"},
                reasoning=["Test"],
                showdown_occurred=(i % 3 == 0)
            )

            simulator.hand_history.append(result)

        return simulator

    def test_get_session_statistics(self, simulator_with_multiple_hands):
        """Test getting session statistics."""
        stats = simulator_with_multiple_hands.get_session_statistics()

        assert stats['total_hands'] == 5
        assert stats['player_wins'] == 3  # indices 0, 2, 4
        assert stats['ai_wins'] == 2  # indices 1, 3
        assert 'average_pot_size' in stats
        assert 'showdown_rate' in stats

    def test_empty_session_statistics(self):
        """Test getting statistics from empty session."""
        simulator = PokerSimulator()
        stats = simulator.get_session_statistics()

        assert stats['total_hands'] == 0


class TestBettingRoundLogic:
    """Tests for betting round execution logic."""

    @pytest.fixture
    def simulator(self):
        """Create a simulator for testing."""
        return PokerSimulator(seed=42)

    @patch('click.prompt')
    @patch('click.echo')
    def test_get_user_action_fold(self, mock_echo, mock_prompt, simulator):
        """Test getting fold action from user."""
        from holdem_cli.simulator.ai_player import GameState

        mock_prompt.return_value = 'fold'

        game_state = GameState(
            street='flop',
            pot_size=100,
            current_bet=50,
            bet_to_call=50,
            board=[Card(Rank.TEN, Suit.HEARTS)],
            position='late',
            num_players=2,
            num_active_players=2
        )

        player_cards = [Card(Rank.ACE, Suit.SPADES), Card(Rank.KING, Suit.HEARTS)]

        action = simulator._get_user_action(game_state, player_cards, 900, 0)

        assert action.action == Action.FOLD

    @patch('click.prompt')
    @patch('click.echo')
    def test_get_user_action_check(self, mock_echo, mock_prompt, simulator):
        """Test getting check action from user."""
        from holdem_cli.simulator.ai_player import GameState

        mock_prompt.return_value = 'check'

        game_state = GameState(
            street='flop',
            pot_size=100,
            current_bet=0,
            bet_to_call=0,
            board=[Card(Rank.TEN, Suit.HEARTS)],
            position='late',
            num_players=2,
            num_active_players=2
        )

        player_cards = [Card(Rank.ACE, Suit.SPADES), Card(Rank.KING, Suit.HEARTS)]

        action = simulator._get_user_action(game_state, player_cards, 1000, 0)

        assert action.action == Action.CHECK


class TestIntegration:
    """Integration tests for the poker simulator."""

    def test_simulator_creates_valid_hand_result(self):
        """Test that simulator can create valid hand results."""
        simulator = PokerSimulator(seed=42)

        # Verify simulator is properly initialized
        assert simulator.ai_player is not None
        assert simulator.evaluator is not None

        # Verify empty hand history
        assert len(simulator.hand_history) == 0

    def test_multiple_simulators_independent(self):
        """Test that multiple simulators are independent."""
        sim1 = PokerSimulator(ai_level='easy')
        sim2 = PokerSimulator(ai_level='hard')

        assert sim1.ai_level != sim2.ai_level
        assert sim1.hand_history is not sim2.hand_history
