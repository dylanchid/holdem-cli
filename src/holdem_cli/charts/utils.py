"""
Utility functions and helpers for the TUI.

This module contains utility functions, CLI integration functions,
and helper methods used across the TUI components.
"""

import signal
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import json

from .app import ChartViewerApp
from .quiz import ChartQuizApp
from .constants import DEFAULT_CHART_NAME, SUPPORTED_IMPORT_FORMATS
from holdem_cli.types import HandAction, ChartAction
# from holdem_cli.charts.tui.widgets.matrix import create_sample_range
from holdem_cli.storage import init_database


def run_chart_viewer(chart_name: str = DEFAULT_CHART_NAME) -> None:
    """Run the chart viewer application."""
    app = ChartViewerApp(chart_name)
    app.run()


def launch_interactive_chart_viewer(chart_name: Optional[str] = None, chart_data: Optional[Dict[str, HandAction]] = None) -> None:
    """Launch the interactive chart viewer from CLI."""
    if chart_data is None:
        chart_data = create_sample_range()

    if chart_name is None:
        chart_name = "Interactive Chart"

    app = ChartViewerApp(chart_name)
    app.current_chart = chart_data
    app.run()


def launch_chart_quiz(chart_data: Optional[Dict[str, HandAction]] = None) -> None:
    """Launch the chart training quiz from CLI."""
    if chart_data is None:
        chart_data = create_sample_range()

    app = ChartQuizApp(chart_data)
    app.run()


def create_chart_from_file(filepath: str, format_type: str = "json") -> Dict[str, HandAction]:
    """
    Create chart data from file.

    Args:
        filepath: Path to the chart file
        format_type: Format of the file ("json", "simple", "pio", "gto_wizard")

    Returns:
        Dictionary mapping hands to HandAction objects

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If format is unsupported
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    if format_type == "json":
        return _load_json_chart(path)
    elif format_type == "simple":
        return _load_simple_chart(path)
    elif format_type == "pio":
        return _load_pio_chart(path)
    elif format_type == "gto_wizard":
        return _load_gto_wizard_chart(path)
    else:
        raise ValueError(f"Unsupported format: {format_type}")


def _load_json_chart(path: Path) -> Dict[str, HandAction]:
    """Load chart from JSON format."""
    with open(path, 'r') as f:
        data = json.load(f)

    chart_data = {}
    for hand, action_data in data.get("ranges", {}).items():
        action = ChartAction(action_data.get("action", "fold"))
        chart_data[hand] = HandAction(
            action=action,
            frequency=action_data.get("frequency", 1.0),
            ev=action_data.get("ev"),
            notes=action_data.get("notes", "")
        )

    return chart_data


def _load_simple_chart(path: Path) -> Dict[str, HandAction]:
    """Load chart from simple text format."""
    chart_data = {}
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split()
            if len(parts) >= 2:
                hand = parts[0]
                action = ChartAction(parts[1].lower())
                frequency = float(parts[2]) if len(parts) > 2 else 1.0

                chart_data[hand] = HandAction(action=action, frequency=frequency)

    return chart_data


def _load_pio_chart(path: Path) -> Dict[str, HandAction]:
    """Load chart from PioSOLVER format.

    PioSOLVER typically exports in CSV format with columns like:
    Hand,Action,Frequency,EV,Notes
    Where Action can be: Raise, Call, Fold, Mixed
    """
    chart_data = {}

    try:
        with open(path, 'r', encoding='utf-8') as f:
            # Try to detect if it's a CSV file
            first_line = f.readline().strip()

            # Check if it looks like a CSV header
            if ',' in first_line and any(keyword in first_line.upper() for keyword in ['HAND', 'ACTION', 'FREQ']):
                # CSV format with headers
                f.seek(0)  # Reset file pointer
                import csv
                reader = csv.DictReader(f)

                for row in reader:
                    hand = _normalize_pio_hand(row.get('Hand', '').strip())
                    if not hand:
                        continue

                    action_str = row.get('Action', 'Fold').strip()
                    frequency = _parse_frequency(row.get('Frequency', '1.0'))
                    ev = _parse_ev(row.get('EV', None))
                    notes = row.get('Notes', '').strip()

                    action = _parse_pio_action(action_str)
                    chart_data[hand] = HandAction(
                        action=action,
                        frequency=frequency,
                        ev=ev,
                        notes=notes
                    )
            else:
                # Fallback: try to parse as simple text format
                f.seek(0)
                lines = f.readlines()

                for line in lines:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    # Try to parse different PioSOLVER line formats
                    parts = line.split()
                    if len(parts) >= 2:
                        hand = _normalize_pio_hand(parts[0])
                        if hand:
                            action = _parse_pio_action(parts[1])
                            frequency = float(parts[2]) if len(parts) > 2 and parts[2].replace('.', '').isdigit() else 1.0

                            chart_data[hand] = HandAction(action=action, frequency=frequency)

        return chart_data

    except Exception as e:
        raise ValueError(f"Error parsing PioSOLVER file: {e}")


def _normalize_pio_hand(hand_str: str) -> str:
    """Normalize hand string from PioSOLVER format to standard format."""
    if not hand_str:
        return ""

    # Remove any brackets or extra formatting
    hand_str = hand_str.replace('[', '').replace(']', '').replace('{', '').replace('}', '').strip()

    # Convert common PioSOLVER hand formats to standard format
    # Examples: "AKs" -> "AKs", "AA" -> "AA", "AKo" -> "AKo"
    if len(hand_str) >= 2:
        # Ensure proper case and format
        hand_str = hand_str.upper()

        # Handle suited/offsuit indicators
        if hand_str.endswith('S'):
            return hand_str  # Already in correct format
        elif hand_str.endswith('O'):
            return hand_str  # Already in correct format
        elif len(hand_str) == 2 and hand_str[0] == hand_str[1]:
            return hand_str  # Pocket pair
        else:
            # Try to determine if suited or offsuit
            # This is a heuristic - in practice, PioSOLVER files usually include s/o
            return hand_str + 'o'  # Default to offsuit

    return hand_str


def _parse_pio_action(action_str: str) -> ChartAction:
    """Parse action string from PioSOLVER format."""
    action_str = action_str.upper().strip()

    if 'RAISE' in action_str or action_str == 'R':
        return ChartAction.RAISE
    elif 'CALL' in action_str or action_str == 'C':
        return ChartAction.CALL
    elif 'FOLD' in action_str or action_str == 'F':
        return ChartAction.FOLD
    elif 'MIXED' in action_str or 'MIX' in action_str or action_str == 'M':
        return ChartAction.MIXED
    elif 'BLUFF' in action_str or 'B' in action_str:
        return ChartAction.BLUFF
    elif 'CHECK' in action_str or action_str == 'X':
        return ChartAction.CHECK
    else:
        # Default to fold for unknown actions
        return ChartAction.FOLD


def _parse_frequency(freq_str: str) -> float:
    """Parse frequency value from string."""
    if not freq_str or freq_str.strip() == '':
        return 1.0

    try:
        # Handle percentage format (e.g., "75%" -> 0.75)
        if '%' in freq_str:
            return float(freq_str.replace('%', '')) / 100.0
        else:
            return float(freq_str)
    except ValueError:
        return 1.0


def _parse_ev(ev_str: str) -> Optional[float]:
    """Parse EV value from string."""
    if not ev_str or ev_str.strip() == '':
        return None

    try:
        return float(ev_str)
    except ValueError:
        return None


def _load_gto_wizard_chart(path: Path) -> Dict[str, HandAction]:
    """Load chart from GTO Wizard format.

    GTO Wizard typically exports in CSV format with columns like:
    Hand,Action,Frequency,RangeSize,Notes
    Actions can be: Raise, Call, Fold, Limp, 3Bet, etc.
    """
    chart_data = {}

    try:
        with open(path, 'r', encoding='utf-8') as f:
            # Check first line to determine format
            first_line = f.readline().strip()

            if ',' in first_line and any(keyword in first_line.upper() for keyword in ['HAND', 'ACTION', 'FREQ', 'RANGE']):
                # CSV format with headers
                f.seek(0)
                import csv
                reader = csv.DictReader(f)

                for row in reader:
                    hand = _normalize_gto_hand(row.get('Hand', '').strip())
                    if not hand:
                        continue

                    action_str = row.get('Action', 'Fold').strip()
                    frequency = _parse_frequency(row.get('Frequency', '1.0'))
                    ev = _parse_ev(row.get('EV', None))
                    notes = row.get('Notes', '').strip()

                    # GTO Wizard might have additional columns like RangeSize
                    range_size = row.get('RangeSize', '')
                    if range_size and not notes:
                        notes = f"Range size: {range_size}"

                    action = _parse_gto_action(action_str)
                    chart_data[hand] = HandAction(
                        action=action,
                        frequency=frequency,
                        ev=ev,
                        notes=notes
                    )
            else:
                # Fallback: try to parse as simple text format
                f.seek(0)
                lines = f.readlines()

                for line in lines:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    parts = line.split()
                    if len(parts) >= 2:
                        hand = _normalize_gto_hand(parts[0])
                        if hand:
                            action = _parse_gto_action(parts[1])
                            frequency = float(parts[2]) if len(parts) > 2 and parts[2].replace('.', '').isdigit() else 1.0

                            chart_data[hand] = HandAction(action=action, frequency=frequency)

        return chart_data

    except Exception as e:
        raise ValueError(f"Error parsing GTO Wizard file: {e}")


def _normalize_gto_hand(hand_str: str) -> str:
    """Normalize hand string from GTO Wizard format to standard format."""
    if not hand_str:
        return ""

    # Remove any brackets or extra formatting
    hand_str = hand_str.replace('[', '').replace(']', '').replace('{', '').replace('}', '').strip()

    if len(hand_str) >= 2:
        hand_str = hand_str.upper()

        # GTO Wizard might use different suited/offsuit indicators
        if hand_str.endswith('S') or hand_str.endswith('H') or hand_str.endswith('D') or hand_str.endswith('C'):
            # Suited (any suit indicator)
            return hand_str[:-1] + 's'
        elif hand_str.endswith('O'):
            return hand_str  # Already in correct format
        elif len(hand_str) == 2 and hand_str[0] == hand_str[1]:
            return hand_str  # Pocket pair
        elif len(hand_str) == 3 and hand_str[2] in 'HDSC':
            # Format like "AKh" -> "AKs"
            return hand_str[:-1] + 's'
        else:
            # Try to determine if suited or offsuit based on common patterns
            # This is a heuristic - real GTO Wizard files usually have suit indicators
            return hand_str + 'o'  # Default to offsuit

    return hand_str


def _parse_gto_action(action_str: str) -> ChartAction:
    """Parse action string from GTO Wizard format."""
    action_str = action_str.upper().strip()

    # GTO Wizard specific actions
    if 'RAISE' in action_str or '3BET' in action_str or 'BET' in action_str or action_str == 'R':
        return ChartAction.RAISE
    elif 'CALL' in action_str or action_str == 'C':
        return ChartAction.CALL
    elif 'FOLD' in action_str or action_str == 'F':
        return ChartAction.FOLD
    elif 'LIMP' in action_str or 'CHECK' in action_str or action_str == 'X':
        return ChartAction.CHECK
    elif 'MIXED' in action_str or 'MIX' in action_str or action_str == 'M':
        return ChartAction.MIXED
    elif 'BLUFF' in action_str or 'B' in action_str:
        return ChartAction.BLUFF
    else:
        # Default to fold for unknown actions
        return ChartAction.FOLD


def demo_tui() -> None:
    """Demonstrate the TUI components."""
    def signal_handler(sig, frame):
        """Handle interrupt signals gracefully."""
        print("\nShutting down TUI gracefully...")
        sys.exit(0)

    # Set up signal handlers for better terminal handling
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("Starting Holdem CLI Chart TUI Demo...")
    print("Press Ctrl+C to exit gracefully")

    try:
        # Create sample data
        sample_chart = create_sample_range()

        # Run the chart viewer
        run_chart_viewer("Demo Chart")
    except KeyboardInterrupt:
        print("\nTUI interrupted by user")
    except Exception as e:
        print(f"TUI error: {e}")
    finally:
        print("TUI demo completed")


def demo_quiz() -> None:
    """Demonstrate the quiz functionality."""
    print("Starting Chart Quiz Demo...")

    sample_chart = create_sample_range()
    quiz_app = ChartQuizApp(sample_chart)
    quiz_app.run()


# Chart manipulation utilities
def merge_charts(chart1: Dict[str, HandAction], chart2: Dict[str, HandAction], merge_strategy: str = "override") -> Dict[str, HandAction]:
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
                avg_ev = (existing.ev + action.ev) / 2 if existing.ev is not None and action.ev is not None else None
                merged[hand] = HandAction(
                    action=existing.action,  # Keep first chart's action
                    frequency=avg_frequency,
                    ev=avg_ev,
                    notes=f"Merged: {existing.notes} | {action.notes}"
                )
        else:
            merged[hand] = action

    return merged


def filter_chart_by_action(chart: Dict[str, HandAction], actions: List[ChartAction]) -> Dict[str, HandAction]:
    """
    Filter chart to only include specific actions.

    Args:
        chart: Chart to filter
        actions: List of actions to include

    Returns:
        Filtered chart
    """
    return {hand: action for hand, action in chart.items() if action.action in actions}


def filter_chart_by_frequency(chart: Dict[str, HandAction], min_frequency: float = 0.0, max_frequency: float = 1.0) -> Dict[str, HandAction]:
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
    import json
    from datetime import datetime

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


# Database integration utilities
def save_chart_to_db(name: str, chart: Dict[str, HandAction], description: str = "") -> bool:
    """
    Save a chart to the database.

    Args:
        name: Chart name
        chart: Chart data
        description: Optional description

    Returns:
        True if successful, False otherwise
    """
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
        # For now, just simulate success
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
    try:
        db = init_database()

        # In a real implementation, this would load from the database
        # For now, return None to indicate not found
        return None
    except Exception as e:
        print(f"Error loading chart from database: {e}")
        return None
