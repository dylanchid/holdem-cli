"""Tests for poker engine card and hand evaluation logic."""

import pytest
from holdem_cli.engine.cards import (
    Card, Deck, HandEvaluator, HandRank, HandStrength, Rank, Suit
)


class TestCard:
    """Test Card class functionality."""
    
    def test_card_creation(self):
        """Test creating cards."""
        card = Card(Rank.ACE, Suit.SPADES)
        assert card.rank == Rank.ACE
        assert card.suit == Suit.SPADES
    
    def test_card_string_representation(self):
        """Test card string formatting."""
        card = Card(Rank.KING, Suit.HEARTS)
        assert str(card) == "Kh"
        assert repr(card) == "Card(Kh)"
    
    def test_card_from_string(self):
        """Test parsing cards from string notation."""
        card = Card.from_string("As")
        assert card.rank == Rank.ACE
        assert card.suit == Suit.SPADES
        
        card = Card.from_string("Tc")
        assert card.rank == Rank.TEN
        assert card.suit == Suit.CLUBS
    
    def test_card_from_string_invalid(self):
        """Test invalid card string handling."""
        with pytest.raises(ValueError):
            Card.from_string("Xs")  # Invalid rank
        
        with pytest.raises(ValueError):
            Card.from_string("Ax")  # Invalid suit
        
        with pytest.raises(ValueError):
            Card.from_string("A")   # Too short


class TestDeck:
    """Test Deck class functionality."""
    
    def test_deck_initialization(self):
        """Test deck starts with 52 cards."""
        deck = Deck()
        assert len(deck.cards) == 52
        assert deck.remaining() == 52
    
    def test_deck_has_all_cards(self):
        """Test deck contains all 52 unique cards."""
        deck = Deck()
        cards_set = set(deck.cards)
        assert len(cards_set) == 52
        
        # Check all ranks and suits are present
        ranks = {card.rank for card in deck.cards}
        suits = {card.suit for card in deck.cards}
        assert len(ranks) == 13
        assert len(suits) == 4
    
    def test_deck_shuffle_deterministic(self):
        """Test deterministic shuffling with seed."""
        deck1 = Deck(seed=42)
        deck2 = Deck(seed=42)
        
        deck1.shuffle()
        deck2.shuffle()
        
        # Same seed should produce same order
        assert deck1.cards == deck2.cards
    
    def test_deck_deal(self):
        """Test dealing cards from deck."""
        deck = Deck()
        original_count = deck.remaining()
        
        # Deal one card
        card = deck.deal_one()
        assert isinstance(card, Card)
        assert deck.remaining() == original_count - 1
        
        # Deal multiple cards
        cards = deck.deal(5)
        assert len(cards) == 5
        assert deck.remaining() == original_count - 6
    
    def test_deck_deal_too_many(self):
        """Test dealing more cards than available."""
        deck = Deck()
        
        with pytest.raises(ValueError):
            deck.deal(53)  # More than 52 cards
    
    def test_deck_reset(self):
        """Test resetting deck to full 52 cards."""
        deck = Deck()
        deck.deal(10)
        assert deck.remaining() == 42
        
        deck.reset()
        assert deck.remaining() == 52


class TestHandEvaluator:
    """Test hand evaluation logic."""
    
    def test_royal_flush(self):
        """Test royal flush detection."""
        cards = [
            Card.from_string("As"),
            Card.from_string("Ks"),
            Card.from_string("Qs"),
            Card.from_string("Js"),
            Card.from_string("Ts")
        ]
        
        strength = HandEvaluator.evaluate_hand(cards)
        assert strength.rank == HandRank.ROYAL_FLUSH
    
    def test_straight_flush(self):
        """Test straight flush detection."""
        cards = [
            Card.from_string("9s"),
            Card.from_string("8s"),
            Card.from_string("7s"),
            Card.from_string("6s"),
            Card.from_string("5s")
        ]
        
        strength = HandEvaluator.evaluate_hand(cards)
        assert strength.rank == HandRank.STRAIGHT_FLUSH
        assert strength.kickers[0] == Rank.NINE
    
    def test_wheel_straight_flush(self):
        """Test A-2-3-4-5 straight flush (wheel)."""
        cards = [
            Card.from_string("As"),
            Card.from_string("5s"),
            Card.from_string("4s"),
            Card.from_string("3s"),
            Card.from_string("2s")
        ]
        
        strength = HandEvaluator.evaluate_hand(cards)
        assert strength.rank == HandRank.STRAIGHT_FLUSH
        assert strength.kickers[0] == Rank.FIVE  # 5-high straight
    
    def test_four_of_a_kind(self):
        """Test four of a kind detection."""
        cards = [
            Card.from_string("Ah"),
            Card.from_string("As"),
            Card.from_string("Ad"),
            Card.from_string("Ac"),
            Card.from_string("Kh")
        ]
        
        strength = HandEvaluator.evaluate_hand(cards)
        assert strength.rank == HandRank.FOUR_OF_A_KIND
        assert strength.kickers[0] == Rank.ACE
        assert strength.kickers[1] == Rank.KING
    
    def test_full_house(self):
        """Test full house detection."""
        cards = [
            Card.from_string("Ah"),
            Card.from_string("As"),
            Card.from_string("Ad"),
            Card.from_string("Kh"),
            Card.from_string("Ks")
        ]
        
        strength = HandEvaluator.evaluate_hand(cards)
        assert strength.rank == HandRank.FULL_HOUSE
        assert strength.kickers[0] == Rank.ACE   # Trips
        assert strength.kickers[1] == Rank.KING  # Pair
    
    def test_flush(self):
        """Test flush detection."""
        cards = [
            Card.from_string("Ah"),
            Card.from_string("Kh"),
            Card.from_string("Qh"),
            Card.from_string("Jh"),
            Card.from_string("9h")
        ]
        
        strength = HandEvaluator.evaluate_hand(cards)
        assert strength.rank == HandRank.FLUSH
        assert strength.kickers[0] == Rank.ACE
    
    def test_straight(self):
        """Test straight detection."""
        cards = [
            Card.from_string("Ah"),
            Card.from_string("Ks"),
            Card.from_string("Qd"),
            Card.from_string("Jh"),
            Card.from_string("Ts")
        ]
        
        strength = HandEvaluator.evaluate_hand(cards)
        assert strength.rank == HandRank.STRAIGHT
        assert strength.kickers[0] == Rank.ACE
    
    def test_wheel_straight(self):
        """Test A-2-3-4-5 straight (wheel)."""
        cards = [
            Card.from_string("Ah"),
            Card.from_string("5s"),
            Card.from_string("4d"),
            Card.from_string("3h"),
            Card.from_string("2s")
        ]
        
        strength = HandEvaluator.evaluate_hand(cards)
        assert strength.rank == HandRank.STRAIGHT
        assert strength.kickers[0] == Rank.FIVE  # 5-high straight
    
    def test_three_of_a_kind(self):
        """Test three of a kind detection."""
        cards = [
            Card.from_string("Ah"),
            Card.from_string("As"),
            Card.from_string("Ad"),
            Card.from_string("Kh"),
            Card.from_string("Qs")
        ]
        
        strength = HandEvaluator.evaluate_hand(cards)
        assert strength.rank == HandRank.THREE_OF_A_KIND
        assert strength.kickers[0] == Rank.ACE
        assert strength.kickers[1] == Rank.KING
        assert strength.kickers[2] == Rank.QUEEN
    
    def test_two_pair(self):
        """Test two pair detection."""
        cards = [
            Card.from_string("Ah"),
            Card.from_string("As"),
            Card.from_string("Kd"),
            Card.from_string("Kh"),
            Card.from_string("Qs")
        ]
        
        strength = HandEvaluator.evaluate_hand(cards)
        assert strength.rank == HandRank.TWO_PAIR
        assert strength.kickers[0] == Rank.ACE
        assert strength.kickers[1] == Rank.KING
        assert strength.kickers[2] == Rank.QUEEN
    
    def test_one_pair(self):
        """Test one pair detection."""
        cards = [
            Card.from_string("Ah"),
            Card.from_string("As"),
            Card.from_string("Kd"),
            Card.from_string("Qh"),
            Card.from_string("Js")
        ]
        
        strength = HandEvaluator.evaluate_hand(cards)
        assert strength.rank == HandRank.PAIR
        assert strength.kickers[0] == Rank.ACE
        assert strength.kickers[1] == Rank.KING
        assert strength.kickers[2] == Rank.QUEEN
        assert strength.kickers[3] == Rank.JACK
    
    def test_high_card(self):
        """Test high card detection."""
        cards = [
            Card.from_string("Ah"),
            Card.from_string("Ks"),
            Card.from_string("Qd"),
            Card.from_string("Jh"),
            Card.from_string("9s")
        ]
        
        strength = HandEvaluator.evaluate_hand(cards)
        assert strength.rank == HandRank.HIGH_CARD
        assert strength.kickers[0] == Rank.ACE
        assert strength.kickers[1] == Rank.KING
        assert strength.kickers[2] == Rank.QUEEN
        assert strength.kickers[3] == Rank.JACK
        assert strength.kickers[4] == Rank.NINE
    
    def test_seven_card_evaluation(self):
        """Test evaluating 7-card hands (finds best 5)."""
        cards = [
            Card.from_string("Ah"),  # Hole cards
            Card.from_string("As"),
            Card.from_string("Kd"),  # Board
            Card.from_string("Kh"),
            Card.from_string("Qs"),
            Card.from_string("2c"),
            Card.from_string("3h")
        ]
        
        strength = HandEvaluator.evaluate_hand(cards)
        assert strength.rank == HandRank.TWO_PAIR
        assert strength.kickers[0] == Rank.ACE
        assert strength.kickers[1] == Rank.KING
        assert strength.kickers[2] == Rank.QUEEN  # Best kicker
    
    def test_hand_comparison(self):
        """Test comparing hand strengths."""
        # Royal flush beats straight flush
        royal = HandStrength(HandRank.ROYAL_FLUSH, [Rank.ACE])
        straight_flush = HandStrength(HandRank.STRAIGHT_FLUSH, [Rank.NINE])
        assert royal > straight_flush
        
        # Same rank, compare kickers
        pair_aces = HandStrength(HandRank.PAIR, [Rank.ACE, Rank.KING, Rank.QUEEN, Rank.JACK])
        pair_kings = HandStrength(HandRank.PAIR, [Rank.KING, Rank.ACE, Rank.QUEEN, Rank.JACK])
        assert pair_aces > pair_kings
    
    def test_insufficient_cards(self):
        """Test error handling for insufficient cards."""
        cards = [Card.from_string("Ah"), Card.from_string("Ks")]
        
        with pytest.raises(ValueError):
            HandEvaluator.evaluate_hand(cards)
    
    def test_hand_strength_description(self):
        """Test that HandStrength has description property."""
        cards = [
            Card.from_string("Ah"),
            Card.from_string("As"),
            Card.from_string("Kd"),
            Card.from_string("Qh"),
            Card.from_string("Js")
        ]
        
        strength = HandEvaluator.evaluate_hand(cards)
        assert hasattr(strength, 'description')
        assert strength.description == "Pair"
