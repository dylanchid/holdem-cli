"""
Base strategy classes for GTO chart generation.

This module provides the foundation for different poker strategies
used in generating GTO charts.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..tui.widgets.matrix import HandAction, ChartAction


class Position(Enum):
    """Poker table positions."""
    UTG = "UTG"
    HJ = "HJ"
    CO = "CO"
    BTN = "BTN"
    SB = "SB"
    BB = "BB"


class StackDepth(Enum):
    """Common stack depths in BB."""
    SHALLOW = 20
    MID = 50
    DEEP = 100
    VERY_DEEP = 200


class Scenario(Enum):
    """Common poker scenarios."""
    OPEN_RAISE = "open_raise"
    THREE_BET = "3bet"
    FOUR_BET = "4bet"
    VS_STEAL = "vs_steal"
    SQUEEZE = "squeeze"
    COLD_CALL = "cold_call"


class HandCategory(Enum):
    """Poker hand categories for strategy decisions."""
    PREMIUM_PAIR = "premium_pair"
    STRONG_PAIR = "strong_pair"
    MEDIUM_PAIR = "medium_pair"
    SMALL_PAIR = "small_pair"
    PREMIUM_SUITED = "premium_suited"
    PREMIUM_OFFSUIT = "premium_offsuit"
    STRONG_SUITED = "strong_suited"
    STRONG_OFFSUIT = "strong_offsuit"
    ACE_SUITED = "ace_suited"
    KING_SUITED = "king_suited"
    CONNECTOR_SUITED = "connector_suited"
    ONE_GAPPER_SUITED = "one_gapper_suited"
    SMALL_SUITED = "small_suited"
    BROADWAY_SUITED = "broadway_suited"
    BROADWAY_OFFSUIT = "broadway_offsuit"
    CONNECTOR_OFFSUIT = "connector_offsuit"
    TRASH = "trash"


@dataclass
class StrategyDecision:
    """A decision made by a poker strategy."""
    action: ChartAction
    frequency: float  # 0.0 to 1.0
    expected_value: Optional[float] = None
    notes: Optional[str] = None
    confidence: float = 1.0  # How confident the strategy is in this decision


class PokerStrategy(ABC):
    """Abstract base class for poker strategies."""

    def __init__(self, position: Position, stack_depth: StackDepth):
        """Initialize strategy with position and stack depth."""
        self.position = position
        self.stack_depth = stack_depth

    @abstractmethod
    def get_decision(self, hand: str, scenario: Scenario) -> StrategyDecision:
        """Get the strategy decision for a specific hand in a scenario."""
        pass

    @abstractmethod
    def get_hand_category(self, hand: str) -> HandCategory:
        """Categorize a poker hand."""
        pass

    def get_position_multiplier(self) -> float:
        """Get the range width multiplier based on position."""
        multipliers = {
            Position.UTG: 0.6,
            Position.HJ: 0.75,
            Position.CO: 0.9,
            Position.BTN: 1.0,
            Position.SB: 0.7,
            Position.BB: 0.8
        }
        return multipliers.get(self.position, 1.0)

    def adjust_for_stack_depth(self, decision: StrategyDecision) -> StrategyDecision:
        """Adjust decision based on stack depth."""
        # Deeper stacks allow for more nuanced play
        if self.stack_depth == StackDepth.VERY_DEEP:
            # Slightly wider ranges in very deep situations
            adjusted_freq = min(1.0, decision.frequency * 1.1)
            return StrategyDecision(
                action=decision.action,
                frequency=adjusted_freq,
                expected_value=decision.expected_value,
                notes=decision.notes,
                confidence=decision.confidence
            )
        elif self.stack_depth == StackDepth.SHALLOW:
            # Tighter ranges in shallow situations
            adjusted_freq = decision.frequency * 0.8
            return StrategyDecision(
                action=decision.action,
                frequency=adjusted_freq,
                expected_value=decision.expected_value,
                notes=f"{decision.notes} (tightened for shallow stack)",
                confidence=decision.confidence * 0.9
            )

        return decision
