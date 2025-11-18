"""
Chart file loaders for various formats.

This module contains functions to load chart data from different file formats
including JSON, simple text, PioSOLVER, and GTO Wizard formats.
"""

import csv
import json
from pathlib import Path
from typing import Dict, Optional

from holdem_cli.types import HandAction, ChartAction


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
        return load_json_chart(path)
    elif format_type == "simple":
        return load_simple_chart(path)
    elif format_type == "pio":
        return load_pio_chart(path)
    elif format_type == "gto_wizard":
        return load_gto_wizard_chart(path)
    else:
        raise ValueError(f"Unsupported format: {format_type}")


def load_json_chart(path: Path) -> Dict[str, HandAction]:
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


def load_simple_chart(path: Path) -> Dict[str, HandAction]:
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


def load_pio_chart(path: Path) -> Dict[str, HandAction]:
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
            # Default to offsuit
            return hand_str + 'o'

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


def load_gto_wizard_chart(path: Path) -> Dict[str, HandAction]:
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
            # Default to offsuit
            return hand_str + 'o'

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
        return ChartAction.FOLD
