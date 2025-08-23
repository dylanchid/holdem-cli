"""Core poker engine components."""

import random
from enum import Enum
from typing import List, Tuple, Optional
from dataclasses import dataclass


class Suit(Enum):
    """Card suits."""
    CLUBS = "c"
    DIAMONDS = "d"
    HEARTS = "h"
    SPADES = "s"


class Rank(Enum):
    """Card ranks with numeric values for comparison."""
    TWO = (2, "2")
    THREE = (3, "3")
    FOUR = (4, "4")
    FIVE = (5, "5")
    SIX = (6, "6")
    SEVEN = (7, "7")
    EIGHT = (8, "8")
    NINE = (9, "9")
    TEN = (10, "T")
    JACK = (11, "J")
    QUEEN = (12, "Q")
    KING = (13, "K")
    ACE = (14, "A")
    
    def __init__(self, numeric_value: int, symbol: str) -> None:
        self.numeric_value = numeric_value
        self.symbol = symbol
    
    def __lt__(self, other: 'Rank') -> bool:
        return self.numeric_value < other.numeric_value
    
    def __le__(self, other: 'Rank') -> bool:
        return self.numeric_value <= other.numeric_value
    
    def __gt__(self, other: 'Rank') -> bool:
        return self.numeric_value > other.numeric_value
    
    def __ge__(self, other: 'Rank') -> bool:
        return self.numeric_value >= other.numeric_value


@dataclass(frozen=True)
class Card:
    """A playing card with rank and suit."""
    rank: Rank
    suit: Suit
    
    def __str__(self) -> str:
        return f"{self.rank.symbol}{self.suit.value}"
    
    def __repr__(self) -> str:
        return f"Card({self.rank.symbol}{self.suit.value})"
    
    @classmethod
    def from_string(cls, card_str: str) -> 'Card':
        """Create a card from string notation like 'As' or 'Kh'."""
        if len(card_str) != 2:
            raise ValueError(f"Invalid card string: {card_str}")
        
        rank_str, suit_str = card_str[0], card_str[1].lower()
        
        # Find rank
        rank = None
        for r in Rank:
            if r.symbol == rank_str.upper():
                rank = r
                break
        if rank is None:
            raise ValueError(f"Invalid rank: {rank_str}")
        
        # Find suit
        suit = None
        for s in Suit:
            if s.value == suit_str:
                suit = s
                break
        if suit is None:
            raise ValueError(f"Invalid suit: {suit_str}")
        
        return cls(rank, suit)


class Deck:
    """A standard 52-card deck with shuffling capabilities."""

    def __init__(self, seed: Optional[int] = None) -> None:
        """Initialize deck with optional deterministic seeding for tests."""
        self.cards: List[Card] = []
        self._random = random.Random()
        if seed is not None:
            self._random.seed(seed)
        self.reset()
    
    def reset(self) -> None:
        """Reset deck to standard 52 cards."""
        self.cards = [
            Card(rank, suit) 
            for rank in Rank 
            for suit in Suit
        ]
    
    def shuffle(self) -> None:
        """Shuffle the deck in place."""
        self._random.shuffle(self.cards)
    
    def deal(self, count: int = 1) -> List[Card]:
        """Deal cards from the top of the deck."""
        if count > len(self.cards):
            raise ValueError(f"Cannot deal {count} cards, only {len(self.cards)} remaining")
        
        dealt = self.cards[:count]
        self.cards = self.cards[count:]
        return dealt
    
    def deal_one(self) -> Card:
        """Deal a single card."""
        return self.deal(1)[0]
    
    def remaining(self) -> int:
        """Number of cards remaining in deck."""
        return len(self.cards)


class HandRank(Enum):
    """Poker hand rankings from lowest to highest."""
    HIGH_CARD = (1, "High Card")
    PAIR = (2, "Pair")
    TWO_PAIR = (3, "Two Pair")
    THREE_OF_A_KIND = (4, "Three of a Kind")
    STRAIGHT = (5, "Straight")
    FLUSH = (6, "Flush")
    FULL_HOUSE = (7, "Full House")
    FOUR_OF_A_KIND = (8, "Four of a Kind")
    STRAIGHT_FLUSH = (9, "Straight Flush")
    ROYAL_FLUSH = (10, "Royal Flush")
    
    def __init__(self, numeric_value: int, name: str) -> None:
        self.numeric_value = numeric_value
        self.hand_name = name
    
    def __lt__(self, other: 'HandRank') -> bool:
        return self.numeric_value < other.numeric_value
    
    def __le__(self, other: 'HandRank') -> bool:
        return self.numeric_value <= other.numeric_value
    
    def __gt__(self, other: 'HandRank') -> bool:
        return self.numeric_value > other.numeric_value
    
    def __ge__(self, other: 'HandRank') -> bool:
        return self.numeric_value >= other.numeric_value


@dataclass
class HandStrength:
    """Represents the strength of a poker hand."""
    rank: HandRank
    kickers: List[Rank]  # Supporting cards for tie-breaking
    
    @property
    def description(self) -> str:
        """Human-readable description of the hand."""
        return self.rank.hand_name
    
    @property
    def cards(self) -> List[Card]:
        """Get the cards that make up this hand (placeholder for compatibility)."""
        # This is a simplified implementation for compatibility
        # In a full implementation, we'd store the actual cards
        return []
    
    def __lt__(self, other: 'HandStrength') -> bool:
        if self.rank != other.rank:
            return self.rank < other.rank
        return self.kickers < other.kickers
    
    def __le__(self, other: 'HandStrength') -> bool:
        return self < other or self == other
    
    def __gt__(self, other: 'HandStrength') -> bool:
        return not (self <= other)
    
    def __ge__(self, other: 'HandStrength') -> bool:
        return not (self < other)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, HandStrength):
            return NotImplemented
        return self.rank == other.rank and self.kickers == other.kickers


class HandEvaluator:
    """Evaluates poker hands and determines winners."""
    
    @staticmethod
    def evaluate_hand(cards: List[Card]) -> HandStrength:
        """Evaluate a 5-7 card hand and return its strength."""
        if len(cards) < 5:
            raise ValueError("Need at least 5 cards to evaluate hand")
        
        # For 6-7 cards, find the best 5-card hand
        if len(cards) > 5:
            from itertools import combinations
            best_hand = None
            for combo in combinations(cards, 5):
                hand_strength = HandEvaluator._evaluate_five_cards(list(combo))
                if best_hand is None or hand_strength > best_hand:
                    best_hand = hand_strength
            return best_hand
        
        return HandEvaluator._evaluate_five_cards(cards)
    
    @staticmethod
    def _evaluate_five_cards(cards: List[Card]) -> HandStrength:
        """Evaluate exactly 5 cards."""
        if len(cards) != 5:
            raise ValueError("Must have exactly 5 cards")
        
        # Sort cards by rank (high to low)
        sorted_cards = sorted(cards, key=lambda c: c.rank.numeric_value, reverse=True)
        ranks = [c.rank for c in sorted_cards]
        suits = [c.suit for c in sorted_cards]
        
        # Check for flush
        is_flush = len(set(suits)) == 1
        
        # Check for straight
        is_straight, straight_high = HandEvaluator._is_straight(ranks)
        
        # Count rank frequencies
        rank_counts = {}
        for rank in ranks:
            rank_counts[rank] = rank_counts.get(rank, 0) + 1
        
        # Sort by count then rank value
        count_groups = sorted(rank_counts.items(), 
                            key=lambda x: (x[1], x[0].numeric_value), reverse=True)
        
        # Determine hand type
        counts = [count for _, count in count_groups]
        
        if is_straight and is_flush:
            if ranks[0] == Rank.ACE and straight_high == Rank.FIVE:
                # A-2-3-4-5 straight flush (wheel)
                return HandStrength(HandRank.STRAIGHT_FLUSH, [Rank.FIVE])
            elif ranks[0] == Rank.ACE and straight_high == Rank.ACE:
                # Royal flush
                return HandStrength(HandRank.ROYAL_FLUSH, [Rank.ACE])
            else:
                return HandStrength(HandRank.STRAIGHT_FLUSH, [straight_high])
        
        if counts == [4, 1]:
            # Four of a kind
            quad_rank = count_groups[0][0]
            kicker = count_groups[1][0]
            return HandStrength(HandRank.FOUR_OF_A_KIND, [quad_rank, kicker])
        
        if counts == [3, 2]:
            # Full house
            trips_rank = count_groups[0][0]
            pair_rank = count_groups[1][0]
            return HandStrength(HandRank.FULL_HOUSE, [trips_rank, pair_rank])
        
        if is_flush:
            return HandStrength(HandRank.FLUSH, ranks)
        
        if is_straight:
            if ranks[0] == Rank.ACE and straight_high == Rank.FIVE:
                # A-2-3-4-5 straight (wheel)
                return HandStrength(HandRank.STRAIGHT, [Rank.FIVE])
            return HandStrength(HandRank.STRAIGHT, [straight_high])
        
        if counts == [3, 1, 1]:
            # Three of a kind
            trips_rank = count_groups[0][0]
            kickers = [rank for rank, _ in count_groups[1:]]
            return HandStrength(HandRank.THREE_OF_A_KIND, [trips_rank] + kickers)
        
        if counts == [2, 2, 1]:
            # Two pair
            high_pair = count_groups[0][0]
            low_pair = count_groups[1][0]
            kicker = count_groups[2][0]
            return HandStrength(HandRank.TWO_PAIR, [high_pair, low_pair, kicker])
        
        if counts == [2, 1, 1, 1]:
            # One pair
            pair_rank = count_groups[0][0]
            kickers = [rank for rank, _ in count_groups[1:]]
            return HandStrength(HandRank.PAIR, [pair_rank] + kickers)
        
        # High card
        return HandStrength(HandRank.HIGH_CARD, ranks)
    
    @staticmethod
    def _is_straight(ranks: List[Rank]) -> Tuple[bool, Optional[Rank]]:
        """Check if ranks form a straight. Returns (is_straight, high_card)."""
        # Handle ace-low straight (A-2-3-4-5)
        if ranks == [Rank.ACE, Rank.FIVE, Rank.FOUR, Rank.THREE, Rank.TWO]:
            return True, Rank.FIVE
        
        # Check normal straight
        for i in range(len(ranks) - 1):
            if ranks[i].numeric_value - ranks[i + 1].numeric_value != 1:
                return False, None
        
        return True, ranks[0]
