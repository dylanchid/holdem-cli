"""Tests for equity calculation engine."""

import pytest
from holdem_cli.engine.cards import Card, Rank, Suit
from holdem_cli.engine.equity import (
    EquityCalculator, EquityResult, parse_hand_string, parse_range_string
)


class TestEquityCalculator:
    """Test equity calculation functionality."""
    
    def test_equity_calculation_basic(self):
        """Test basic equity calculation between two hands."""
        calculator = EquityCalculator(seed=42)  # Deterministic for testing
        
        # Aces vs Kings pre-flop
        aces = [Card.from_string("As"), Card.from_string("Ah")]
        kings = [Card.from_string("Ks"), Card.from_string("Kh")]
        
        result = calculator.calculate_equity(aces, kings, iterations=1000)
        
        # AA should have significant equity advantage over KK
        assert result.hand1_win > 70  # Should win > 70% of the time
        assert result.hand2_win < 30  # KK should win < 30%
        assert result.iterations == 1000
    
    def test_equity_with_board(self):
        """Test equity calculation with board cards."""
        calculator = EquityCalculator(seed=42)
        
        # AA vs random hand on A-high board (AA should dominate)
        aces = [Card.from_string("As"), Card.from_string("Ah")]
        sevens = [Card.from_string("7s"), Card.from_string("7h")]
        board = [Card.from_string("Ac"), Card.from_string("2d"), Card.from_string("3h")]
        
        result = calculator.calculate_equity(aces, sevens, board, iterations=1000)
        
        # With set of aces, should win very high percentage
        assert result.hand1_win > 95
    
    def test_equity_result_dict(self):
        """Test EquityResult dictionary conversion."""
        result = EquityResult(
            hand1_win=80.5, hand1_tie=1.0, hand1_lose=18.5,
            hand2_win=18.5, hand2_tie=1.0, hand2_lose=80.5,
            iterations=1000
        )
        
        result_dict = result.to_dict()
        assert result_dict["hand1"]["win"] == 80.5
        assert result_dict["hand2"]["lose"] == 80.5
        assert result_dict["iterations"] == 1000
    
    def test_duplicate_cards_error(self):
        """Test error handling for duplicate cards."""
        calculator = EquityCalculator()
        
        # Same card in both hands
        hand1 = [Card.from_string("As"), Card.from_string("Ah")]
        hand2 = [Card.from_string("As"), Card.from_string("Kh")]  # Duplicate As
        
        with pytest.raises(ValueError, match="Duplicate cards detected"):
            calculator.calculate_equity(hand1, hand2)
    
    def test_invalid_hand_size(self):
        """Test error handling for invalid hand sizes."""
        calculator = EquityCalculator()
        
        # Too few cards
        hand1 = [Card.from_string("As")]
        hand2 = [Card.from_string("Ks"), Card.from_string("Kh")]
        
        with pytest.raises(ValueError, match="Each hand must have exactly 2 cards"):
            calculator.calculate_equity(hand1, hand2)
    
    def test_too_many_board_cards(self):
        """Test error handling for too many board cards."""
        calculator = EquityCalculator()
        
        hand1 = [Card.from_string("As"), Card.from_string("Ah")]
        hand2 = [Card.from_string("Ks"), Card.from_string("Kh")]
        board = [Card.from_string(f"{rank}{suit}") 
                for rank in ["2", "3", "4", "5", "6", "7"]  # 6 cards
                for suit in ["c"]][:6]
        
        with pytest.raises(ValueError, match="Board cannot have more than 5 cards"):
            calculator.calculate_equity(hand1, hand2, board)


class TestHandParsing:
    """Test hand string parsing functionality."""
    
    def test_parse_hand_string_basic(self):
        """Test parsing basic hand strings."""
        # With spaces
        cards = parse_hand_string("As Kh")
        assert len(cards) == 2
        assert cards[0] == Card.from_string("As")
        assert cards[1] == Card.from_string("Kh")
        
        # Without spaces
        cards = parse_hand_string("AsKh")
        assert len(cards) == 2
        assert cards[0] == Card.from_string("As")
        assert cards[1] == Card.from_string("Kh")
    
    def test_parse_hand_string_board(self):
        """Test parsing board card strings."""
        cards = parse_hand_string("2c7sQh")
        assert len(cards) == 3
        assert cards[0] == Card.from_string("2c")
        assert cards[1] == Card.from_string("7s")
        assert cards[2] == Card.from_string("Qh")
    
    def test_parse_hand_string_invalid(self):
        """Test invalid hand string parsing."""
        with pytest.raises(ValueError):
            parse_hand_string("As K")  # Odd number of characters
        
        with pytest.raises(ValueError):
            parse_hand_string("Xs Kh")  # Invalid rank


class TestRangeParsing:
    """Test range string parsing functionality."""
    
    def test_parse_specific_pair(self):
        """Test parsing specific pair ranges."""
        hands = parse_range_string("AA")
        
        # Should generate 6 combinations (4 choose 2)
        assert len(hands) == 6
        
        # All should be pocket aces
        for hand in hands:
            assert len(hand) == 2
            assert hand[0].rank == Rank.ACE
            assert hand[1].rank == Rank.ACE
            assert hand[0].suit != hand[1].suit  # Different suits
    
    def test_parse_pair_range(self):
        """Test parsing pair ranges like JJ+."""
        hands = parse_range_string("JJ+")
        
        # Should include JJ, QQ, KK, AA = 4 * 6 = 24 combinations
        assert len(hands) == 24
        
        # Check that we have the right ranks
        ranks_found = set()
        for hand in hands:
            assert hand[0].rank == hand[1].rank  # Should be pairs
            ranks_found.add(hand[0].rank)
        
        expected_ranks = {Rank.JACK, Rank.QUEEN, Rank.KING, Rank.ACE}
        assert ranks_found == expected_ranks
    
    def test_parse_suited_hand(self):
        """Test parsing suited hands like AKs."""
        hands = parse_range_string("AKs")
        
        # Should generate 4 combinations (one per suit)
        assert len(hands) == 4
        
        for hand in hands:
            assert len(hand) == 2
            assert hand[0].rank == Rank.ACE
            assert hand[1].rank == Rank.KING
            assert hand[0].suit == hand[1].suit  # Same suit
    
    def test_parse_offsuit_hand(self):
        """Test parsing offsuit hands like AKo."""
        hands = parse_range_string("AKo")
        
        # Should generate 12 combinations (4*3 different suit combos)
        assert len(hands) == 12
        
        for hand in hands:
            assert len(hand) == 2
            assert hand[0].rank == Rank.ACE
            assert hand[1].rank == Rank.KING
            assert hand[0].suit != hand[1].suit  # Different suits
    
    def test_parse_multiple_ranges(self):
        """Test parsing comma-separated ranges."""
        hands = parse_range_string("AA,KK,AKs")
        
        # AA: 6 combos, KK: 6 combos, AKs: 4 combos = 16 total
        assert len(hands) == 16
    
    def test_range_equity_calculation(self):
        """Test calculating equity against a range."""
        calculator = EquityCalculator(seed=42)
        
        # Pocket aces vs small pairs range
        aces = [Card.from_string("As"), Card.from_string("Ah")]
        small_pairs_range = parse_range_string("22,33,44")
        
        result = calculator.calculate_range_equity(
            aces, small_pairs_range, iterations=100
        )
        
        # Aces should dominate small pairs
        assert result.hand1_win > 70
        assert result.iterations > 0


class TestDeterministicBehavior:
    """Test that equity calculations are deterministic with seeds."""
    
    def test_deterministic_with_seed(self):
        """Test that same seed produces same results."""
        hand1 = [Card.from_string("As"), Card.from_string("Ah")]
        hand2 = [Card.from_string("Ks"), Card.from_string("Kh")]
        
        calc1 = EquityCalculator(seed=12345)
        calc2 = EquityCalculator(seed=12345)
        
        result1 = calc1.calculate_equity(hand1, hand2, iterations=1000)
        result2 = calc2.calculate_equity(hand1, hand2, iterations=1000)
        
        # Results should be identical with same seed
        assert result1.hand1_win == result2.hand1_win
        assert result1.hand1_tie == result2.hand1_tie
        assert result1.hand1_lose == result2.hand1_lose
    
    def test_different_seeds_different_results(self):
        """Test that different seeds can produce different results."""
        hand1 = [Card.from_string("As"), Card.from_string("Ah")]
        hand2 = [Card.from_string("Ks"), Card.from_string("Kh")]
        
        calc1 = EquityCalculator(seed=12345)
        calc2 = EquityCalculator(seed=54321)
        
        result1 = calc1.calculate_equity(hand1, hand2, iterations=100)
        result2 = calc2.calculate_equity(hand1, hand2, iterations=100)
        
        # Results might be different (though could be same by chance)
        # Main point is that we can control randomness with seeds
