"""
Opening range strategy implementation.

This module contains the logic for determining optimal opening ranges
from different positions.
"""

from typing import Dict, Optional
from .base_strategy import (
    PokerStrategy, Position, StackDepth, Scenario, HandCategory, StrategyDecision
)
from .poker_knowledge import PokerKnowledgeBase
from ..tui.widgets.matrix import ChartAction


class OpeningRangeStrategy(PokerStrategy):
    """Strategy for determining optimal opening ranges."""

    def __init__(self, position: Position, stack_depth: StackDepth):
        """Initialize opening range strategy."""
        super().__init__(position, stack_depth)
        self.knowledge = PokerKnowledgeBase()

    def get_decision(self, hand: str, scenario: Scenario) -> StrategyDecision:
        """Get opening decision for a hand."""
        if scenario != Scenario.OPEN_RAISE:
            raise ValueError("OpeningRangeStrategy only handles open_raise scenarios")

        category = self.knowledge.categorize_hand(hand)
        decision = self._get_category_decision(category)

        # Apply position adjustment
        position_multiplier = self.get_position_multiplier()
        adjusted_frequency = min(1.0, decision.frequency * position_multiplier)

        # Apply stack depth adjustment
        decision.frequency = adjusted_frequency
        return self.adjust_for_stack_depth(decision)

    def get_hand_category(self, hand: str) -> HandCategory:
        """Get hand category using poker knowledge base."""
        return self.knowledge.categorize_hand(hand)

    def _get_category_decision(self, category: HandCategory) -> StrategyDecision:
        """Get decision for a specific hand category."""
        decisions = {
            # Premium pairs - always raise
            HandCategory.PREMIUM_PAIR: StrategyDecision(
                action=ChartAction.RAISE,
                frequency=1.0,
                expected_value=3.0,
                notes="Premium pocket pair - always raise"
            ),

            # Strong pairs - raise most of the time
            HandCategory.STRONG_PAIR: StrategyDecision(
                action=ChartAction.RAISE,
                frequency=0.9,
                expected_value=2.0,
                notes="Strong pocket pair"
            ),

            # Medium pairs - position dependent
            HandCategory.MEDIUM_PAIR: StrategyDecision(
                action=ChartAction.MIXED,
                frequency=0.6,
                expected_value=1.0,
                notes="Medium pocket pair"
            ),

            # Small pairs - call or fold based on position
            HandCategory.SMALL_PAIR: StrategyDecision(
                action=ChartAction.CALL,
                frequency=0.3,
                expected_value=0.5,
                notes="Small pocket pair"
            ),

            # Premium suited - always raise
            HandCategory.PREMIUM_SUITED: StrategyDecision(
                action=ChartAction.RAISE,
                frequency=1.0,
                expected_value=2.5,
                notes="Premium suited hand"
            ),

            # Premium offsuit - raise most
            HandCategory.PREMIUM_OFFSUIT: StrategyDecision(
                action=ChartAction.RAISE,
                frequency=0.95,
                expected_value=2.2,
                notes="Premium offsuit hand"
            ),

            # Strong suited - raise in good position
            HandCategory.STRONG_SUITED: StrategyDecision(
                action=ChartAction.RAISE,
                frequency=0.8,
                expected_value=1.5,
                notes="Strong suited hand"
            ),

            # Strong offsuit - position dependent
            HandCategory.STRONG_OFFSUIT: StrategyDecision(
                action=ChartAction.MIXED,
                frequency=0.4,
                expected_value=0.8,
                notes="Strong offsuit hand"
            ),

            # Ace rag suited - position dependent
            HandCategory.ACE_SUITED: StrategyDecision(
                action=ChartAction.CALL,
                frequency=0.4,
                expected_value=0.3,
                notes="Ace with low kicker suited"
            ),

            # King rag suited - call in good position
            HandCategory.KING_SUITED: StrategyDecision(
                action=ChartAction.CALL,
                frequency=0.3,
                expected_value=0.2,
                notes="King with low kicker suited"
            ),

            # Suited connectors - call in good position
            HandCategory.CONNECTOR_SUITED: StrategyDecision(
                action=ChartAction.CALL,
                frequency=0.5,
                expected_value=0.4,
                notes="Suited connector"
            ),

            # One gapper suited - occasional call
            HandCategory.ONE_GAPPER_SUITED: StrategyDecision(
                action=ChartAction.MIXED,
                frequency=0.2,
                expected_value=0.1,
                notes="Suited one-gapper"
            ),

            # Broadway suited - raise in good position
            HandCategory.BROADWAY_SUITED: StrategyDecision(
                action=ChartAction.MIXED,
                frequency=0.5,
                expected_value=0.6,
                notes="Broadway suited"
            ),

            # Broadway offsuit - occasional call
            HandCategory.BROADWAY_OFFSUIT: StrategyDecision(
                action=ChartAction.CALL,
                frequency=0.3,
                expected_value=0.4,
                notes="Broadway offsuit"
            ),

            # Offsuit connectors - rare
            HandCategory.CONNECTOR_OFFSUIT: StrategyDecision(
                action=ChartAction.FOLD,
                frequency=0.9,
                expected_value=-0.2,
                notes="Offsuit connector"
            ),

            # Small suited - rare
            HandCategory.SMALL_SUITED: StrategyDecision(
                action=ChartAction.FOLD,
                frequency=0.95,
                expected_value=-0.3,
                notes="Small suited hand"
            ),

            # Trash hands - fold
            HandCategory.TRASH: StrategyDecision(
                action=ChartAction.FOLD,
                frequency=0.99,
                expected_value=-0.5,
                notes="Unplayable hand"
            )
        }

        return decisions.get(category, StrategyDecision(
            action=ChartAction.FOLD,
            frequency=1.0,
            expected_value=-0.5,
            notes="Unknown hand type"
        ))
