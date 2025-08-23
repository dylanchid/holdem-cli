"""
GTO Chart Library for Holdem CLI.

This module provides a modern, abstracted interface to GTO chart generation
using strategy patterns and proper separation of concerns.
"""

from typing import Dict, List, Optional, Tuple
from .tui.widgets.matrix import HandAction, ChartAction
from .strategies.base_strategy import Position, StackDepth, Scenario
from .strategies.chart_generator import ChartGenerator
from ..utils.logging_utils import get_logger


class GTOChartLibrary:
    """Modern, abstracted GTO chart library using strategy patterns."""

    def __init__(self):
        """Initialize the GTO chart library."""
        self._generator = ChartGenerator()
        self._logger = get_logger()

    @classmethod
    def get_available_positions(cls) -> List[str]:
        """Get list of available positions."""
        return [pos.value for pos in Position]

    @classmethod
    def get_available_scenarios(cls) -> List[str]:
        """Get list of available scenarios."""
        return [scenario.value for scenario in Scenario]

    @classmethod
    def get_available_stack_depths(cls) -> List[int]:
        """Get list of available stack depths."""
        return [depth.value for depth in StackDepth]

    @classmethod
    def create_position_chart(cls, hero_position: str, villain_position: str,
                            stack_depth: int = 100, scenario: str = "open_raise") -> Dict[str, HandAction]:
        """
        Create a GTO chart for a specific position matchup using modern strategy patterns.

        Args:
            hero_position: Hero's position (UTG, HJ, CO, BTN, SB, BB)
            villain_position: Villain's position (UTG, HJ, CO, BTN, SB, BB)
            stack_depth: Effective stack depth in BB
            scenario: Poker scenario (open_raise, 3bet, vs_steal, etc.)

        Returns:
            Dictionary mapping hand strings to HandAction objects
        """
        # Validate inputs
        if hero_position not in cls.get_available_positions():
            raise ValueError(f"Invalid hero position: {hero_position}")
        if villain_position not in cls.get_available_positions():
            raise ValueError(f"Invalid villain position: {villain_position}")
        if stack_depth not in cls.get_available_stack_depths():
            raise ValueError(f"Invalid stack depth: {stack_depth}")
        if scenario not in cls.get_available_scenarios():
            raise ValueError(f"Invalid scenario: {scenario}")

        # Convert string parameters to enums
        hero_pos = Position(hero_position)
        villain_pos = Position(villain_position)
        stack = StackDepth(stack_depth)
        scenario_enum = Scenario(scenario)

        # Use the chart generator
        generator = ChartGenerator()
        return generator.generate_chart(hero_pos, villain_pos, stack, scenario_enum)

    # Legacy methods for backward compatibility - these now use the new strategy system

    @classmethod
    def get_chart_metadata(cls, hero_pos: str, villain_pos: str, stack_depth: int,
                          scenario: str) -> Dict:
        """Get metadata for a specific chart using the new system."""
        from datetime import datetime
        from .strategies.poker_knowledge import PokerKnowledgeBase

        knowledge = PokerKnowledgeBase()

        return {
            "hero_position": hero_pos,
            "villain_position": villain_pos,
            "stack_depth": stack_depth,
            "scenario": scenario,
            "description": f"{hero_pos} vs {villain_pos} {scenario.replace('_', ' ')} at {stack_depth}bb",
            "position_adjustment": knowledge.get_position_adjustment(hero_pos),
            "stack_adjustment": knowledge.get_stack_adjustment(stack_depth),
            "created_at": datetime.now().isoformat(),
            "version": "2.0",
            "strategy_system": "Modern abstracted strategies"
        }

    @classmethod
    def list_available_charts(cls) -> List[Dict]:
        """List all available charts using the new system."""
        generator = ChartGenerator()
        charts = []

        positions = cls.get_available_positions()
        scenarios = cls.get_available_scenarios()
        depths = cls.get_available_stack_depths()

        for hero_pos in positions:
            for villain_pos in positions:
                if hero_pos == villain_pos:
                    continue  # Skip same position matchups
                for depth in depths:
                    for scenario in scenarios:
                        # Get metadata for each chart
                        metadata = cls.get_chart_metadata(hero_pos, villain_pos, depth, scenario)
                        charts.append({
                            "hero_position": hero_pos,
                            "villain_position": villain_pos,
                            "stack_depth": depth,
                            "scenario": scenario,
                            "description": metadata["description"],
                            "available": True,
                            "metadata": metadata
                        })

        return charts

    @classmethod
    def search_charts(cls, hero_pos: Optional[str] = None,
                     villain_pos: Optional[str] = None,
                     min_depth: Optional[int] = None,
                     max_depth: Optional[int] = None,
                     scenario: Optional[str] = None) -> List[Dict]:
        """Search for charts matching specific criteria using modern filtering."""
        all_charts = cls.list_available_charts()
        filtered_charts = []

        for chart in all_charts:
            if hero_pos and chart["hero_position"] != hero_pos:
                continue
            if villain_pos and chart["villain_position"] != villain_pos:
                continue
            if scenario and chart["scenario"] != scenario:
                continue
            if min_depth and chart["stack_depth"] < min_depth:
                continue
            if max_depth and chart["stack_depth"] > max_depth:
                continue
            filtered_charts.append(chart)

        return filtered_charts
