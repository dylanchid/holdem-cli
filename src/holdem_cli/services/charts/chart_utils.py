"""
Chart utility functions for the TUI services.

This module contains chart-specific utility functions that don't depend on the main app.
"""

from typing import Dict, List, Optional, Tuple, Any
from holdem_cli.types import HandAction, ChartAction


def validate_chart(actions: Dict[str, HandAction]) -> List[str]:
    """
    Validate a chart data structure.

    Args:
        actions: Chart actions to validate

    Returns:
        List of validation error messages
    """
    errors = []

    if not actions:
        errors.append("Chart is empty")
        return errors

    if not isinstance(actions, dict):
        errors.append("Chart must be a dictionary")
        return errors

    # Validate each hand/action
    for hand, action in actions.items():
        # Validate hand format
        if not _is_valid_hand_format(hand):
            errors.append(f"Invalid hand format: {hand}")

        # Validate action
        if not isinstance(action, HandAction):
            errors.append(f"Invalid action type for hand {hand}: expected HandAction")
        else:
            # Validate action properties
            if action.frequency < 0 or action.frequency > 1:
                errors.append(f"Invalid frequency for hand {hand}: {action.frequency}")

            if action.ev is not None and abs(action.ev) > 10:
                errors.append(f"Unrealistic EV for hand {hand}: {action.ev}")

    return errors


def _is_valid_hand_format(hand: str) -> bool:
    """Validate poker hand format (e.g., 'AKs', 'TT', 'AJo')."""
    if not isinstance(hand, str) or len(hand) < 2 or len(hand) > 3:
        return False

    # Pocket pairs (AA, KK, etc.)
    if len(hand) == 2 and hand[0] == hand[1]:
        return hand[0] in '23456789TJQKA'

    # Suited/offsuit hands (AKs, AJo, etc.)
    if len(hand) == 3:
        rank1, rank2, suit = hand[0], hand[1], hand[2]
        if rank1 not in 'AKQJT98765432' or rank2 not in 'AKQJT98765432':
            return False
        if suit not in 'so':
            return False
        # Ensure ranks are in valid order (higher rank first)
        ranks = 'AKQJT98765432'
        return ranks.index(rank1) <= ranks.index(rank2)

    return False


def get_chart_statistics(actions: Dict[str, HandAction]) -> Dict[str, Any]:
    """
    Calculate statistics for a chart.

    Args:
        actions: Chart actions to analyze

    Returns:
        Dictionary containing chart statistics
    """
    if not actions:
        return {'error': 'No chart data available'}

    stats = {
        'total_hands': len(actions),
        'action_distribution': {},
        'frequency_analysis': {},
        'ev_analysis': {},
        'range_analysis': {}
    }

    # Action distribution
    actions_count = {}
    frequencies = []
    evs = []

    for action in actions.values():
        action_name = action.action.value
        actions_count[action_name] = actions_count.get(action_name, 0) + 1

        if action.frequency is not None:
            frequencies.append(action.frequency)

        if action.ev is not None:
            evs.append(action.ev)

    stats['action_distribution'] = actions_count

    # Frequency analysis
    if frequencies:
        stats['frequency_analysis'] = {
            'average': sum(frequencies) / len(frequencies),
            'min': min(frequencies),
            'max': max(frequencies),
            'high_frequency_hands': len([f for f in frequencies if f >= 0.8]),
            'low_frequency_hands': len([f for f in frequencies if f <= 0.3])
        }

    # EV analysis
    if evs:
        stats['ev_analysis'] = {
            'average': sum(evs) / len(evs),
            'min': min(evs),
            'max': max(evs),
            'positive_ev_hands': len([ev for ev in evs if ev > 0]),
            'profitable_hands': len([ev for ev in evs if ev > 0.5])
        }

    # Range analysis
    total_possible = 169  # Standard poker hand count
    range_percent = len(actions) / total_possible * 100

    if range_percent < 15:
        tightness = "Very Tight"
    elif range_percent < 25:
        tightness = "Tight"
    elif range_percent < 35:
        tightness = "Balanced"
    elif range_percent < 45:
        tightness = "Loose"
    else:
        tightness = "Very Loose"

    stats['range_analysis'] = {
        'range_percentage': range_percent,
        'tightness': tightness,
        'recommendation': _get_range_recommendation(range_percent, actions_count)
    }

    return stats


def _get_range_recommendation(range_percent: float, actions: Dict[str, int]) -> str:
    """Get range recommendation based on analysis."""
    recommendations = []

    if range_percent < 20:
        recommendations.append("Consider opening up your range slightly for more bluffing opportunities")

    if range_percent > 40:
        recommendations.append("Your range might be too loose - consider tightening up")

    # Check action balance
    total_actions = sum(actions.values())
    if total_actions > 0:
        raise_percent = actions.get('raise', 0) / total_actions * 100
        call_percent = actions.get('call', 0) / total_actions * 100

        if raise_percent > 70:
            recommendations.append("High raise percentage - consider more balanced action distribution")

        if call_percent > 50:
            recommendations.append("High call percentage - consider more aggressive actions")

    return "; ".join(recommendations) if recommendations else "Range looks well-balanced"


def classify_hand_type(hand: str) -> str:
    """Classify a hand into its type category."""
    if len(hand) == 2 and hand[0] == hand[1]:
        return "pocket_pair"
    elif hand.endswith('s'):
        return "suited"
    elif hand.endswith('o'):
        return "offsuit"
    else:
        return "unknown"


def filter_actions_by_criteria(actions: Dict[str, HandAction],
                              criteria: Dict[str, Any]) -> Dict[str, HandAction]:
    """Filter actions based on specified criteria."""
    filtered = {}

    for hand, action in actions.items():
        include = True

        # Filter by action type
        if "action" in criteria and action.action.value not in criteria["action"]:
            include = False

        # Filter by frequency range
        if "min_frequency" in criteria and action.frequency < criteria["min_frequency"]:
            include = False
        if "max_frequency" in criteria and action.frequency > criteria["max_frequency"]:
            include = False

        # Filter by EV range
        if "min_ev" in criteria and action.ev is not None and action.ev < criteria["min_ev"]:
            include = False
        if "max_ev" in criteria and action.ev is not None and action.ev > criteria["max_ev"]:
            include = False

        # Filter by hand type
        if "hand_types" in criteria:
            hand_type = classify_hand_type(hand)
            if hand_type not in criteria["hand_types"]:
                include = False

        if include:
            filtered[hand] = action

    return filtered


def calculate_hand_equity(hand1: str, hand2: str, board: Optional[str] = None,
                         iterations: int = 10000) -> Dict[str, Any]:
    """
    Calculate equity between two hands.

    Args:
        hand1: First hand (e.g., "AKs")
        hand2: Second hand (e.g., "QQ")
        board: Optional board cards
        iterations: Number of simulation iterations

    Returns:
        Equity calculation results
    """
    # This is a simplified implementation
    # In a real implementation, this would use proper poker equity calculation

    # Basic hand strength comparison (simplified)
    hand_strength = {
        'AA': 100, 'KK': 95, 'QQ': 90, 'JJ': 85, 'TT': 80, '99': 75, '88': 70, '77': 65,
        'AKs': 85, 'AKo': 75, 'AQs': 80, 'AQo': 70, 'AJs': 75, 'AJo': 65,
        'KQs': 70, 'KQo': 60, 'KJs': 65, 'KJo': 55,
        'QJs': 60, 'QJo': 50, 'JTs': 55, 'JTo': 45,
        'A9s': 50, 'A9o': 40, 'A8s': 45, 'A8o': 35,
    }

    strength1 = hand_strength.get(hand1, 25)
    strength2 = hand_strength.get(hand2, 25)

    # Simple equity calculation
    if strength1 > strength2:
        equity1 = 0.65 + (strength1 - strength2) / 200
        equity2 = 0.35 - (strength1 - strength2) / 200
    elif strength2 > strength1:
        equity2 = 0.65 + (strength2 - strength1) / 200
        equity1 = 0.35 - (strength2 - strength1) / 200
    else:
        equity1 = equity2 = 0.5

    return {
        'hand1': hand1,
        'hand2': hand2,
        'equity1': equity1,
        'equity2': equity2,
        'tie': 0.0,
        'iterations': iterations,
        'board': board or ""
    }
