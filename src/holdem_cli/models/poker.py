"""
Poker-specific data models for Holdem CLI.

This module defines standardized models for poker-related data structures,
ensuring consistency across all poker-related modules.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from enum import Enum
from .base import BaseModel, TimestampMixin


class Suit(Enum):
    """Card suits with standardized values."""
    CLUBS = "c"
    DIAMONDS = "d"
    HEARTS = "h"
    SPADES = "s"

    @property
    def symbol(self) -> str:
        """Get the suit symbol."""
        return self.value

    @property
    def name(self) -> str:
        """Get the full suit name."""
        return self.name.lower().capitalize()

    @property
    def color(self) -> str:
        """Get the suit color."""
        return "red" if self in [Suit.HEARTS, Suit.DIAMONDS] else "black"


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

    def __init__(self, numeric_value: int, symbol: str):
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

    @property
    def name(self) -> str:
        """Get the full rank name."""
        names = {
            2: "Two", 3: "Three", 4: "Four", 5: "Five",
            6: "Six", 7: "Seven", 8: "Eight", 9: "Nine",
            10: "Ten", 11: "Jack", 12: "Queen", 13: "King", 14: "Ace"
        }
        return names.get(self.numeric_value, str(self.numeric_value))


@dataclass
class Card(BaseModel):
    """Standardized playing card model."""
    rank: Rank
    suit: Suit

    def __str__(self) -> str:
        return f"{self.rank.symbol}{self.suit.symbol}"

    def __repr__(self) -> str:
        return f"Card({self.rank.symbol}{self.suit.symbol})"

    def __hash__(self) -> int:
        return hash((self.rank, self.suit))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self.rank == other.rank and self.suit == other.suit

    @classmethod
    def from_string(cls, card_str: str) -> 'Card':
        """Create a card from string notation (e.g., 'As', 'Kh')."""
        if len(card_str) != 2:
            raise ValueError(f"Invalid card string: {card_str}")

        rank_str, suit_str = card_str[0].upper(), card_str[1].lower()

        # Find rank
        rank = None
        for r in Rank:
            if r.symbol == rank_str:
                rank = r
                break
        if rank is None:
            raise ValueError(f"Invalid rank: {rank_str}")

        # Find suit
        suit = None
        for s in Suit:
            if s.symbol == suit_str:
                suit = s
                break
        if suit is None:
            raise ValueError(f"Invalid suit: {suit_str}")

        return cls(rank=rank, suit=suit)

    @property
    def is_face_card(self) -> bool:
        """Check if this is a face card (J, Q, K)."""
        return self.rank in [Rank.JACK, Rank.QUEEN, Rank.KING]

    @property
    def is_broadway_card(self) -> bool:
        """Check if this is a broadway card (T, J, Q, K, A)."""
        return self.rank.numeric_value >= 10

    @property
    def numeric_value(self) -> int:
        """Get the numeric value of the card."""
        return self.rank.numeric_value


@dataclass
class Deck(BaseModel):
    """Standardized deck model."""
    cards: List[Card] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize deck if empty."""
        if not self.cards:
            self.reset()

    def reset(self) -> None:
        """Reset deck to standard 52 cards."""
        self.cards = [
            Card(rank, suit)
            for suit in Suit
            for rank in Rank
        ]

    def shuffle(self) -> None:
        """Shuffle the deck."""
        from ..utils.random_utils import shuffle
        shuffle(self.cards)

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

    @property
    def remaining(self) -> int:
        """Number of cards remaining in deck."""
        return len(self.cards)

    @property
    def is_empty(self) -> bool:
        """Check if deck is empty."""
        return len(self.cards) == 0


@dataclass
class Hand(BaseModel):
    """Standardized poker hand model."""
    cards: List[Card] = field(default_factory=list)

    def __str__(self) -> str:
        return ' '.join(str(card) for card in self.cards)

    def __len__(self) -> int:
        return len(self.cards)

    def add_card(self, card: Card) -> None:
        """Add a card to the hand."""
        self.cards.append(card)

    def remove_card(self, card: Card) -> bool:
        """Remove a card from the hand."""
        try:
            self.cards.remove(card)
            return True
        except ValueError:
            return False

    def clear(self) -> None:
        """Clear all cards from the hand."""
        self.cards.clear()

    def has_card(self, card: Card) -> bool:
        """Check if hand contains a specific card."""
        return card in self.cards

    def sort_by_rank(self) -> None:
        """Sort cards by rank (high to low)."""
        self.cards.sort(key=lambda c: c.rank.numeric_value, reverse=True)

    def get_unique_ranks(self) -> Set[Rank]:
        """Get unique ranks in the hand."""
        return {card.rank for card in self.cards}

    def get_unique_suits(self) -> Set[Suit]:
        """Get unique suits in the hand."""
        return {card.suit for card in self.cards}


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

    def __init__(self, numeric_value: int, display_name: str):
        self.numeric_value = numeric_value
        self.display_name = display_name

    def __lt__(self, other: 'HandRank') -> bool:
        return self.numeric_value < other.numeric_value

    def __le__(self, other: 'HandRank') -> bool:
        return self.numeric_value <= other.numeric_value

    def __gt__(self, other: 'HandRank') -> bool:
        return self.numeric_value > other.numeric_value

    def __ge__(self, other: 'HandRank') -> bool:
        return self.numeric_value >= other.numeric_value


@dataclass
class HandStrength(BaseModel):
    """Represents the strength of a poker hand."""
    rank: HandRank
    primary_rank: Rank  # Main rank (e.g., pair of Aces)
    secondary_rank: Optional[Rank] = None  # Secondary rank (e.g., full house trips)
    kickers: List[Rank] = field(default_factory=list)
    made_cards: List[Card] = field(default_factory=list)  # Cards that make the hand

    def __str__(self) -> str:
        return self.rank.display_name

    def __lt__(self, other: 'HandStrength') -> bool:
        if self.rank != other.rank:
            return self.rank < other.rank

        # Compare primary ranks
        if self.primary_rank != other.primary_rank:
            return self.primary_rank < other.primary_rank

        # Compare secondary ranks
        if self.secondary_rank != other.secondary_rank:
            return (self.secondary_rank or Rank.TWO) < (other.secondary_rank or Rank.TWO)

        # Compare kickers
        return self.kickers < other.kickers

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, HandStrength):
            return NotImplemented
        return (self.rank == other.rank and
                self.primary_rank == other.primary_rank and
                self.secondary_rank == other.secondary_rank and
                self.kickers == other.kickers)

    @property
    def description(self) -> str:
        """Get a human-readable description of the hand."""
        base_desc = self.rank.display_name

        if self.rank == HandRank.HIGH_CARD:
            return f"{base_desc} ({self.primary_rank.name})"
        elif self.rank == HandRank.PAIR:
            return f"{base_desc} of {self.primary_rank.name}s"
        elif self.rank == HandRank.TWO_PAIR:
            return f"{base_desc} ({self.primary_rank.name}s and {self.secondary_rank.name}s)"
        elif self.rank == HandRank.THREE_OF_A_KIND:
            return f"{base_desc} ({self.primary_rank.name}s)"
        elif self.rank == HandRank.STRAIGHT:
            return f"{base_desc} to {self.primary_rank.name}"
        elif self.rank == HandRank.FLUSH:
            return f"{base_desc} ({self.primary_rank.name} high)"
        elif self.rank == HandRank.FULL_HOUSE:
            return f"{base_desc} ({self.primary_rank.name}s full of {self.secondary_rank.name}s)"
        elif self.rank == HandRank.FOUR_OF_A_KIND:
            return f"{base_desc} ({self.primary_rank.name}s)"
        elif self.rank == HandRank.STRAIGHT_FLUSH:
            return f"{base_desc} to {self.primary_rank.name}"
        elif self.rank == HandRank.ROYAL_FLUSH:
            return f"{base_desc} ({self.primary_rank.name} high)"

        return base_desc


@dataclass
class PokerHand(BaseModel):
    """Complete poker hand representation."""
    hole_cards: List[Card] = field(default_factory=list)
    community_cards: List[Card] = field(default_factory=list)
    hand_strength: Optional[HandStrength] = None

    @property
    def all_cards(self) -> List[Card]:
        """Get all cards in the hand (hole + community)."""
        return self.hole_cards + self.community_cards

    @property
    def total_cards(self) -> int:
        """Get total number of cards."""
        return len(self.all_cards)

    def is_valid(self) -> bool:
        """Check if the hand is valid."""
        return (len(self.hole_cards) == 2 and
                0 <= len(self.community_cards) <= 5 and
                len(self.all_cards) <= 7)

    def validate(self) -> List[str]:
        """Validate the poker hand."""
        issues = []

        if len(self.hole_cards) != 2:
            issues.append(f"Expected 2 hole cards, got {len(self.hole_cards)}")

        if len(self.community_cards) > 5:
            issues.append(f"Too many community cards: {len(self.community_cards)} (max 5)")

        # Check for duplicate cards
        all_cards = self.all_cards
        if len(all_cards) != len(set(all_cards)):
            issues.append("Duplicate cards found in hand")

        return issues
