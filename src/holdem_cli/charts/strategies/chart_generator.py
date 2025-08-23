"""
Chart generator using strategy abstractions.

This module provides a clean interface for generating GTO charts
using different strategy implementations.
"""

import time
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base_strategy import (
    PokerStrategy, Position, StackDepth, Scenario, StrategyDecision
)
from .opening_strategy import OpeningRangeStrategy
from ..tui.widgets.matrix import HandAction, ChartAction
from ...utils.logging_utils import get_logger


class ChartGenerator:
    """Generates GTO charts using strategy implementations."""

    def __init__(self):
        """Initialize chart generator."""
        self.logger = get_logger()
        self._cache = {}  # Simple cache for generated charts
        self._strategy_cache = {}  # Cache for strategy instances

    def generate_chart(
        self,
        hero_position: Position,
        villain_position: Position,
        stack_depth: StackDepth,
        scenario: Scenario,
        hands: Optional[List[str]] = None
    ) -> Dict[str, HandAction]:
        """Generate a GTO chart for given parameters."""

        # Create cache key
        cache_key = f"{hero_position.value}_{villain_position.value}_{stack_depth.value}_{scenario.value}"

        # Check cache first
        if cache_key in self._cache:
            self.logger.debug(f"Using cached chart for {cache_key}")
            return self._cache[cache_key].copy()

        start_time = time.time()

        # Get appropriate strategy
        strategy = self._get_strategy(hero_position, stack_depth, scenario)

        # Generate all possible hands if not provided
        if hands is None:
            hands = self._generate_all_hands()

        self.logger.info(f"Generating {scenario.value} chart for {hero_position.value} vs {villain_position.value}")

        # Generate chart using strategy
        chart = {}
        for hand in hands:
            try:
                decision = strategy.get_decision(hand, scenario)
                chart[hand] = HandAction(
                    action=decision.action,
                    frequency=decision.frequency,
                    ev=decision.expected_value,
                    notes=decision.notes
                )
            except Exception as e:
                self.logger.warning(f"Error generating decision for {hand}: {e}")
                # Fallback to fold
                chart[hand] = HandAction(
                    action=ChartAction.FOLD,
                    frequency=1.0,
                    ev=-0.5,
                    notes="Error in strategy calculation"
                )

        # Cache the result
        self._cache[cache_key] = chart.copy()

        elapsed = time.time() - start_time
        self.logger.info(".2f")

        return chart

    def generate_chart_batch(
        self,
        parameters_list: List[Tuple[Position, Position, StackDepth, Scenario]],
        max_workers: int = 4
    ) -> Dict[str, Dict[str, HandAction]]:
        """Generate multiple charts in parallel."""

        self.logger.info(f"Generating {len(parameters_list)} charts in batch mode")

        results = {}

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_params = {
                executor.submit(self.generate_chart, *params): params
                for params in parameters_list
            }

            # Collect results as they complete
            for future in as_completed(future_to_params):
                params = future_to_params[future]
                cache_key = f"{params[0].value}_{params[1].value}_{params[2].value}_{params[3].value}"

                try:
                    chart = future.result()
                    results[cache_key] = chart
                except Exception as e:
                    self.logger.error(f"Error generating chart for {cache_key}: {e}")
                    results[cache_key] = {}

        self.logger.info(f"Batch generation complete: {len(results)} charts generated")
        return results

    def _get_strategy(
        self,
        position: Position,
        stack_depth: StackDepth,
        scenario: Scenario
    ) -> PokerStrategy:
        """Get appropriate strategy for the given parameters."""

        # Create strategy key for caching
        strategy_key = f"{position.value}_{stack_depth.value}_{scenario.value}"

        if strategy_key in self._strategy_cache:
            return self._strategy_cache[strategy_key]

        # Create new strategy instance
        if scenario == Scenario.OPEN_RAISE:
            strategy = OpeningRangeStrategy(position, stack_depth)
        else:
            # For now, default to opening strategy for other scenarios
            # TODO: Implement other strategy types
            self.logger.warning(f"Using opening strategy for {scenario.value} (not fully implemented)")
            strategy = OpeningRangeStrategy(position, stack_depth)

        # Cache the strategy
        self._strategy_cache[strategy_key] = strategy

        return strategy

    def _generate_all_hands(self) -> List[str]:
        """Generate all possible poker hands."""
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        hands = []

        # Generate pairs
        for rank in ranks:
            hands.append(f"{rank}{rank}")

        # Generate suited hands
        for i, high_rank in enumerate(ranks):
            for low_rank in ranks[:i]:  # Only lower ranks
                hands.append(f"{high_rank}{low_rank}s")

        # Generate offsuit hands
        for i, high_rank in enumerate(ranks):
            for low_rank in ranks[:i]:  # Only lower ranks
                hands.append(f"{high_rank}{low_rank}o")

        return hands

    def clear_cache(self) -> None:
        """Clear all cached charts and strategies."""
        self._cache.clear()
        self._strategy_cache.clear()
        self.logger.info("Chart generator cache cleared")

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            'charts_cached': len(self._cache),
            'strategies_cached': len(self._strategy_cache)
        }
