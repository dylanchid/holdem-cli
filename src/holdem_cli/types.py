"""
Common types and data structures for the charts module.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ChartAction(Enum):
    """Actions that can be taken with poker hands."""
    RAISE = "raise"
    CALL = "call"
    FOLD = "fold"
    MIXED = "mixed"
    BLUFF = "bluff"
    CHECK = "check"


class Color:
    """ANSI color codes for terminal output."""
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    DARK_GRAY = "\033[90m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    # Background colors
    BG_RED = "\033[101m"
    BG_GREEN = "\033[102m"
    BG_YELLOW = "\033[103m"
    BG_BLUE = "\033[104m"
    BG_MAGENTA = "\033[105m"
    BG_CYAN = "\033[106m"
    BG_DARK_GRAY = "\033[100m"


@dataclass
class HandAction:
    """Action for a specific poker hand."""
    action: ChartAction
    frequency: float = 1.0
    ev: Optional[float] = None
    notes: str = ""

    @property
    def color(self) -> str:
        """Get ANSI color for this action."""
        color_map = {
            ChartAction.RAISE: Color.RED,
            ChartAction.CALL: Color.GREEN,
            ChartAction.FOLD: Color.DARK_GRAY,
            ChartAction.BLUFF: Color.BLUE,
            ChartAction.MIXED: Color.YELLOW,
            ChartAction.CHECK: Color.CYAN
        }
        return color_map.get(self.action, Color.WHITE)

    @property
    def bg_color(self) -> str:
        """Get background color for this action."""
        bg_map = {
            ChartAction.RAISE: Color.BG_RED,
            ChartAction.CALL: Color.BG_GREEN,
            ChartAction.FOLD: Color.BG_DARK_GRAY,
            ChartAction.BLUFF: Color.BG_BLUE,
            ChartAction.MIXED: Color.BG_YELLOW,
            ChartAction.CHECK: Color.BG_CYAN
        }
        return bg_map.get(self.action, "")
