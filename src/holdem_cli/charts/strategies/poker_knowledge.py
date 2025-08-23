"""
Poker knowledge base for strategy decisions.

This module contains poker-specific knowledge and hand categorization
logic, separated from the chart generation logic.
"""

import re
from typing import Dict, List, Tuple, Optional
from .base_strategy import HandCategory


class PokerKnowledgeBase:
    """Central repository of poker knowledge and hand categorization."""

    def __init__(self):
        self._hand_patterns = self._build_hand_patterns()
        self._pair_ranges = self._build_pair_ranges()
        self._suited_ranges = self._build_suited_ranges()
        self._offsuit_ranges = self._build_offsuit_ranges()

    def _build_hand_patterns(self) -> Dict[str, re.Pattern]:
        """Build regex patterns for hand recognition."""
        return {
            'pair': re.compile(r'^(.)\1$'),
            'suited': re.compile(r'^(.)(.)s$'),
            'offsuit': re.compile(r'^(.)(.)o$'),
        }

    def _build_pair_ranges(self) -> Dict[str, List[str]]:
        """Build pair hand ranges."""
        return {
            'premium': ['AA', 'KK', 'QQ', 'JJ'],
            'strong': ['TT', '99', '88'],
            'medium': ['77', '66', '55'],
            'small': ['44', '33', '22']
        }

    def _build_suited_ranges(self) -> Dict[str, List[str]]:
        """Build suited hand ranges."""
        return {
            'premium': ['AKs', 'AQs', 'AJs', 'ATs'],
            'strong': ['A9s', 'A8s', 'A7s', 'A6s', 'A5s', 'KQs', 'KJs', 'KTs', 'QJs', 'QTs', 'JTs'],
            'ace_rag': ['A4s', 'A3s', 'A2s'],
            'king_rag': ['K9s', 'K8s', 'K7s', 'K6s', 'K5s', 'K4s', 'K3s', 'K2s'],
            'connectors': ['98s', '87s', '76s', '65s', '54s', '43s', '32s'],
            'one_gappers': ['97s', '86s', '75s', '64s', '53s', '42s'],
            'broadway': ['T9s', 'J9s', 'Q9s', 'K9s']
        }

    def _build_offsuit_ranges(self) -> Dict[str, List[str]]:
        """Build offsuit hand ranges."""
        return {
            'premium': ['AKo', 'AQo', 'AJo', 'ATo'],
            'strong': ['A9o', 'A8o', 'A7o', 'A6o', 'A5o', 'KQo', 'KJo', 'KTo', 'QJo', 'QTo', 'JTo'],
            'connectors': ['98o', '87o', '76o', '65o'],
            'one_gappers': ['97o', '86o', '75o', '64o'],
            'broadway': ['T9o', 'J9o', 'Q9o', 'K9o']
        }

    def categorize_hand(self, hand: str) -> HandCategory:
        """Categorize a poker hand into a standard category."""
        hand = hand.upper().strip()

        # Check for pairs
        if self._is_pair(hand):
            return self._categorize_pair(hand)

        # Check for suited hands
        elif hand.endswith('S'):
            return self._categorize_suited(hand)

        # Check for offsuit hands
        elif hand.endswith('O'):
            return self._categorize_offsuit(hand)

        # Fallback
        return HandCategory.TRASH

    def _is_pair(self, hand: str) -> bool:
        """Check if hand is a pair."""
        return len(hand) == 2 and hand[0] == hand[1]

    def _categorize_pair(self, hand: str) -> HandCategory:
        """Categorize a pair."""
        rank = hand[0]
        rank_values = {'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10}

        if rank in rank_values:
            numeric_value = rank_values[rank]
        else:
            numeric_value = int(rank)

        if numeric_value >= 12:  # AA, KK, QQ, JJ
            return HandCategory.PREMIUM_PAIR
        elif numeric_value >= 9:  # TT, 99, 88
            return HandCategory.STRONG_PAIR
        elif numeric_value >= 6:  # 77, 66, 55
            return HandCategory.MEDIUM_PAIR
        else:  # 44, 33, 22
            return HandCategory.SMALL_PAIR

    def _categorize_suited(self, hand: str) -> HandCategory:
        """Categorize a suited hand."""
        if len(hand) != 3:
            return HandCategory.TRASH

        high_rank, low_rank = hand[0], hand[1]

        # Premium suited aces
        if high_rank == 'A' and low_rank in 'KQJ':
            return HandCategory.PREMIUM_SUITED

        # Strong suited aces
        if high_rank == 'A' and low_rank in 'T9876':
            return HandCategory.STRONG_SUITED

        # Ace rag suited
        if high_rank == 'A' and low_rank in '5432':
            return HandCategory.ACE_SUITED

        # Premium broadway
        if high_rank in 'KQJ' and low_rank in 'QJT' and high_rank != low_rank:
            return HandCategory.STRONG_SUITED

        # Strong broadway
        if high_rank in 'KQT' and low_rank in 'JT987':
            return HandCategory.BROADWAY_SUITED

        # Suited connectors
        high_val = self._rank_to_value(high_rank)
        low_val = self._rank_to_value(low_rank)
        if abs(high_val - low_val) <= 1 and high_val >= 7:
            return HandCategory.CONNECTOR_SUITED

        # One gappers
        if abs(high_val - low_val) == 2 and high_val >= 7:
            return HandCategory.ONE_GAPPER_SUITED

        # Small suited
        if high_val <= 10:
            return HandCategory.SMALL_SUITED

        return HandCategory.TRASH

    def _categorize_offsuit(self, hand: str) -> HandCategory:
        """Categorize an offsuit hand."""
        if len(hand) != 3:
            return HandCategory.TRASH

        high_rank, low_rank = hand[0], hand[1]

        # Premium offsuit
        if high_rank == 'A' and low_rank in 'KQJ':
            return HandCategory.PREMIUM_OFFSUIT

        # Strong offsuit
        if high_rank == 'A' and low_rank in 'T987':
            return HandCategory.STRONG_OFFSUIT

        # Offsuit connectors
        high_val = self._rank_to_value(high_rank)
        low_val = self._rank_to_value(low_rank)
        if abs(high_val - low_val) <= 1 and high_val >= 8:
            return HandCategory.CONNECTOR_OFFSUIT

        # Broadway offsuit
        if high_rank in 'KQT' and low_rank in 'JT9':
            return HandCategory.BROADWAY_OFFSUIT

        return HandCategory.TRASH

    def _rank_to_value(self, rank: str) -> int:
        """Convert rank character to numeric value."""
        rank_values = {'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10}
        return rank_values.get(rank, int(rank) if rank.isdigit() else 0)

    def get_hand_strength_score(self, hand: str) -> float:
        """Get a numerical strength score for a hand (0.0 to 1.0)."""
        category = self.categorize_hand(hand)

        strength_scores = {
            HandCategory.PREMIUM_PAIR: 1.0,
            HandCategory.STRONG_PAIR: 0.9,
            HandCategory.MEDIUM_PAIR: 0.7,
            HandCategory.SMALL_PAIR: 0.5,
            HandCategory.PREMIUM_SUITED: 0.95,
            HandCategory.PREMIUM_OFFSUIT: 0.85,
            HandCategory.STRONG_SUITED: 0.8,
            HandCategory.STRONG_OFFSUIT: 0.7,
            HandCategory.ACE_SUITED: 0.6,
            HandCategory.KING_SUITED: 0.55,
            HandCategory.CONNECTOR_SUITED: 0.4,
            HandCategory.ONE_GAPPER_SUITED: 0.3,
            HandCategory.BROADWAY_SUITED: 0.45,
            HandCategory.BROADWAY_OFFSUIT: 0.35,
            HandCategory.CONNECTOR_OFFSUIT: 0.25,
            HandCategory.SMALL_SUITED: 0.2,
            HandCategory.TRASH: 0.0
        }

        return strength_scores.get(category, 0.0)

    def get_position_adjustment(self, position: str) -> float:
        """Get position-based range adjustment factor."""
        adjustments = {
            'UTG': 0.6,
            'HJ': 0.75,
            'CO': 0.9,
            'BTN': 1.0,
            'SB': 0.7,
            'BB': 0.8
        }
        return adjustments.get(position.upper(), 1.0)

    def get_stack_adjustment(self, stack_depth: int) -> float:
        """Get stack depth-based adjustment factor."""
        if stack_depth <= 20:
            return 0.8  # Tighter ranges on shallow stacks
        elif stack_depth <= 50:
            return 0.9  # Slightly tighter on medium stacks
        elif stack_depth <= 100:
            return 1.0  # Standard ranges on deep stacks
        else:
            return 1.1  # Slightly wider on very deep stacks
