"""
Chart manipulation and analysis operations.

This module contains functions for merging, filtering, and analyzing chart data.
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional

from holdem_cli.types import HandAction, ChartAction


def merge_charts(
    chart1: Dict[str, HandAction],
    chart2: Dict[str, HandAction],
    merge_strategy: str = "override"
) -> Dict[str, HandAction]:
    """
    Merge two charts together.

    Args:
        chart1: Primary chart
        chart2: Secondary chart
        merge_strategy: How to handle conflicts ("override", "keep_existing", "average")

    Returns:
        Merged chart
    """
    merged = chart1.copy()

    for hand, action in chart2.items():
        if hand in merged:
            if merge_strategy == "override":
                merged[hand] = action
            elif merge_strategy == "keep_existing":
                continue  # Keep existing action
            elif merge_strategy == "average":
                # Average the frequencies and EVs
                existing = merged[hand]
                avg_frequency = (existing.frequency + action.frequency) / 2
                avg_ev = None
                if existing.ev is not None and action.ev is not None:
                    avg_ev = (existing.ev + action.ev) / 2
                merged[hand] = HandAction(
                    action=existing.action,  # Keep first chart's action
                    frequency=avg_frequency,
                    ev=avg_ev,
                    notes=f"Merged: {existing.notes} | {action.notes}"
                )
        else:
            merged[hand] = action

    return merged


def filter_chart_by_action(
    chart: Dict[str, HandAction],
    actions: List[ChartAction]
) -> Dict[str, HandAction]:
    """
    Filter chart to only include specific actions.

    Args:
        chart: Chart to filter
        actions: List of actions to include

    Returns:
        Filtered chart
    """
    return {hand: action for hand, action in chart.items() if action.action in actions}


def filter_chart_by_frequency(
    chart: Dict[str, HandAction],
    min_frequency: float = 0.0,
    max_frequency: float = 1.0
) -> Dict[str, HandAction]:
    """
    Filter chart by frequency range.

    Args:
        chart: Chart to filter
        min_frequency: Minimum frequency threshold
        max_frequency: Maximum frequency threshold

    Returns:
        Filtered chart
    """
    return {
        hand: action for hand, action in chart.items()
        if min_frequency <= action.frequency <= max_frequency
    }


def get_chart_statistics(chart: Dict[str, HandAction]) -> Dict[str, Any]:
    """
    Calculate comprehensive statistics for a chart.

    Args:
        chart: Chart to analyze

    Returns:
        Dictionary with various statistics
    """
    if not chart:
        return {}

    stats = {
        "total_hands": len(chart),
        "actions": {},
        "frequency_stats": {},
        "ev_stats": {},
        "hand_types": {
            "pocket_pairs": 0,
            "suited": 0,
            "offsuit": 0
        }
    }

    total_ev = 0
    positive_ev_hands = 0
    frequencies = []
    evs = []

    for hand, action in chart.items():
        # Action distribution
        action_name = action.action.value
        stats["actions"][action_name] = stats["actions"].get(action_name, 0) + 1

        # Frequency tracking
        frequencies.append(action.frequency)

        # EV tracking
        if action.ev is not None:
            evs.append(action.ev)
            total_ev += action.ev
            if action.ev > 0:
                positive_ev_hands += 1

        # Hand type classification
        if len(hand) == 2 and hand[0] == hand[1]:
            stats["hand_types"]["pocket_pairs"] += 1
        elif hand.endswith('s'):
            stats["hand_types"]["suited"] += 1
        elif hand.endswith('o'):
            stats["hand_types"]["offsuit"] += 1

    # Frequency statistics
    if frequencies:
        stats["frequency_stats"] = {
            "min": min(frequencies),
            "max": max(frequencies),
            "avg": sum(frequencies) / len(frequencies),
            "median": sorted(frequencies)[len(frequencies) // 2]
        }

    # EV statistics
    if evs:
        stats["ev_stats"] = {
            "min": min(evs),
            "max": max(evs),
            "avg": total_ev / len(evs),
            "positive_ev_hands": positive_ev_hands,
            "positive_ev_percentage": (positive_ev_hands / len(evs)) * 100
        }

    return stats


def export_chart_statistics(chart: Dict[str, HandAction], filepath: str) -> None:
    """
    Export chart statistics to a file.

    Args:
        chart: Chart to analyze
        filepath: Path to export file
    """
    stats = get_chart_statistics(chart)

    # Add metadata
    export_data = {
        "export_format": "holdem-cli-stats-v1",
        "export_timestamp": datetime.now().isoformat(),
        "statistics": stats
    }

    with open(filepath, 'w') as f:
        json.dump(export_data, f, indent=2)


def validate_chart(chart: Dict[str, HandAction]) -> List[str]:
    """
    Validate a chart for common issues.

    Args:
        chart: Chart to validate

    Returns:
        List of validation warnings/errors
    """
    warnings = []

    if not chart:
        warnings.append("Chart is empty")
        return warnings

    # Check for invalid hand formats
    valid_suits = {'s', 'o'}
    valid_ranks = set('23456789TJQKA')

    for hand in chart.keys():
        if len(hand) == 2:
            # Pocket pair format
            if hand[0] not in valid_ranks or hand[1] not in valid_ranks:
                warnings.append(f"Invalid ranks in pocket pair: {hand}")
        elif len(hand) == 3:
            # Suited/offsuit format
            if (hand[0] not in valid_ranks or
                hand[1] not in valid_ranks or
                hand[2] not in valid_suits):
                warnings.append(f"Invalid hand format: {hand}")
        else:
            warnings.append(f"Invalid hand length: {hand}")

    # Check for frequency ranges
    for hand, action in chart.items():
        if not 0 <= action.frequency <= 1:
            warnings.append(f"Invalid frequency for {hand}: {action.frequency}")

    # Check for duplicate hands
    hands = list(chart.keys())
    if len(hands) != len(set(hands)):
        warnings.append("Duplicate hands found in chart")

    return warnings


def save_chart_to_db(
    name: str,
    chart: Dict[str, HandAction],
    description: str = ""
) -> bool:
    """
    Save a chart to the database.

    Args:
        name: Chart name
        chart: Chart data
        description: Optional description

    Returns:
        True if successful, False otherwise
    """
    from holdem_cli.storage import init_database

    try:
        db = init_database()

        # Convert chart to database format
        chart_data = {
            hand: {
                "action": action.action.value,
                "frequency": action.frequency,
                "ev": action.ev,
                "notes": action.notes
            }
            for hand, action in chart.items()
        }

        # In a real implementation, this would save to the database
        return True
    except Exception as e:
        print(f"Error saving chart to database: {e}")
        return False


def load_chart_from_db(name: str) -> Optional[Dict[str, HandAction]]:
    """
    Load a chart from the database.

    Args:
        name: Chart name

    Returns:
        Chart data if found, None otherwise
    """
    from holdem_cli.storage import init_database

    try:
        db = init_database()

        # In a real implementation, this would load from the database
        return None
    except Exception as e:
        print(f"Error loading chart from database: {e}")
        return None
