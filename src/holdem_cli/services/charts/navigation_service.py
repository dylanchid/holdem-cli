"""
Navigation service for TUI components.

This module provides services for handling navigation, user interactions,
and UI state management for the terminal user interface.
"""

from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import time

from holdem_cli.charts.tui.core.error_handler import get_error_handler, ErrorCategory, ErrorSeverity
from holdem_cli.types import HandAction, ChartAction
from holdem_cli.charts.constants import VIEW_MODES, POSITIONS


class NavigationMode(Enum):
    """Navigation modes for different interaction styles."""
    MATRIX = "matrix"
    MENU = "menu"
    SEARCH = "search"
    RANGE_BUILDER = "range_builder"
    HELP = "help"


class Direction(Enum):
    """Navigation directions."""
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    NEXT = "next"
    PREVIOUS = "previous"


@dataclass
class NavigationState:
    """State of navigation system."""
    mode: NavigationMode = NavigationMode.MATRIX
    current_position: Tuple[int, int] = (0, 0)
    selected_hand: Optional[str] = None
    selected_action: Optional[HandAction] = None
    view_mode: str = "range"
    range_builder_mode: bool = False
    search_active: bool = False
    search_query: str = ""
    search_results: List[str] = field(default_factory=list)
    search_index: int = -1
    help_visible: bool = False
    last_action_time: float = field(default_factory=time.time)

    def reset_search(self):
        """Reset search state."""
        self.search_active = False
        self.search_query = ""
        self.search_results.clear()
        self.search_index = -1

    def next_search_result(self) -> Optional[str]:
        """Navigate to next search result."""
        if not self.search_results:
            return None
        self.search_index = (self.search_index + 1) % len(self.search_results)
        return self.search_results[self.search_index]

    def previous_search_result(self) -> Optional[str]:
        """Navigate to previous search result."""
        if not self.search_results:
            return None
        self.search_index = (self.search_index - 1) % len(self.search_results)
        return self.search_results[self.search_index]


@dataclass
class NavigationContext:
    """Context information for navigation decisions."""
    chart_size: int = 169
    visible_rows: int = 13
    visible_cols: int = 13
    scroll_position: Tuple[int, int] = (0, 0)
    has_selection: bool = False
    in_range_builder: bool = False
    has_search_results: bool = False


class NavigationService:
    """
    Service for handling navigation and user interactions.

    This service provides:
    - Matrix navigation with bounds checking
    - Search functionality with result navigation
    - Position jumping and quick navigation
    - Range builder navigation
    - Keyboard shortcut management
    - Navigation state management
    """

    def __init__(self):
        self.error_handler = get_error_handler()
        self.state = NavigationState()
        self.context = NavigationContext()
        self._navigation_handlers: Dict[str, Callable] = {}
        self._position_map = self._build_position_map()

    def _build_position_map(self) -> Dict[str, Tuple[int, int]]:
        """Build mapping from poker positions to matrix coordinates."""
        # Map positions to approximate matrix locations
        return {
            "UTG": (0, 0),      # Top-left corner
            "MP": (6, 3),       # Middle-left
            "CO": (12, 6),      # Bottom-middle
            "BTN": (12, 12),    # Bottom-right
            "SB": (8, 8),       # Middle
            "BB": (10, 10)      # Lower-middle
        }

    def navigate_matrix(self, direction: Direction, row: int, col: int,
                       matrix_size: Tuple[int, int] = (13, 13)) -> Tuple[int, int]:
        """
        Navigate the matrix in the specified direction.

        Args:
            direction: Navigation direction
            row: Current row
            col: Current column
            matrix_size: Matrix dimensions (rows, cols)

        Returns:
            New (row, col) position
        """
        max_row, max_col = matrix_size

        try:
            if direction == Direction.UP:
                new_row = max(0, row - 1)
                return new_row, col
            elif direction == Direction.DOWN:
                new_row = min(max_row - 1, row + 1)
                return new_row, col
            elif direction == Direction.LEFT:
                new_col = max(0, col - 1)
                return row, new_col
            elif direction == Direction.RIGHT:
                new_col = min(max_col - 1, col + 1)
                return row, new_col
            else:
                return row, col

        except Exception as e:
            self.error_handler.handle_error(
                e,
                context={'operation': 'matrix_navigation', 'direction': direction.value},
                category=ErrorCategory.UI_INTERACTION,
                severity=ErrorSeverity.LOW
            )
            return row, col

    def jump_to_position(self, position: str) -> Optional[Tuple[int, int]]:
        """
        Jump to a specific poker position.

        Args:
            position: Position name (UTG, MP, CO, BTN, SB, BB)

        Returns:
            Matrix coordinates for the position, or None if not found
        """
        return self._position_map.get(position.upper())

    def navigate_to_hand(self, hand: str, hand_matrix: Any) -> Optional[Tuple[int, int]]:
        """
        Navigate to a specific hand in the matrix.

        Args:
            hand: Hand notation (e.g., "AKs", "TT", "AJo")
            hand_matrix: Matrix instance with hand lookup capability

        Returns:
            Matrix coordinates for the hand, or None if not found
        """
        if not hasattr(hand_matrix, 'get_hand_at_position'):
            return None

        # Search through the matrix for the hand
        for row in range(13):
            for col in range(13):
                try:
                    matrix_hand = hand_matrix.get_hand_at_position(row, col)
                    if matrix_hand == hand:
                        return row, col
                except Exception:
                    continue

        return None

    def perform_search(self, query: str, chart_data: Dict[str, HandAction],
                      hand_matrix: Any) -> List[str]:
        """
        Perform search in chart data.

        Args:
            query: Search query
            chart_data: Chart data to search in
            hand_matrix: Matrix for hand lookups

        Returns:
            List of matching hand notations
        """
        query = query.lower().strip()
        if not query:
            return []

        results = []

        try:
            for hand, action in chart_data.items():
                if self._hand_matches_query(hand, action, query):
                    results.append(hand)

            # Update navigation state
            self.state.search_active = True
            self.state.search_query = query
            self.state.search_results = results
            self.state.search_index = 0 if results else -1

        except Exception as e:
            self.error_handler.handle_error(
                e,
                context={'operation': 'search', 'query': query},
                category=ErrorCategory.UI_INTERACTION,
                severity=ErrorSeverity.MEDIUM
            )
            return []

        return results

    def _hand_matches_query(self, hand: str, action: HandAction, query: str) -> bool:
        """Check if a hand matches the search query."""
        # Hand name matching
        if query in hand.lower():
            return True

        # Action matching
        if query in action.action.value.lower():
            return True

        # Suited/offsuit matching
        if "suited" in query and hand.endswith("s"):
            return True
        if "offsuit" in query and hand.endswith("o"):
            return True
        if "pocket" in query and len(hand) == 2 and hand[0] == hand[1]:
            return True

        # Rank matching
        if "broadway" in query and hand[0] in "AKQJT":
            return True
        if "high" in query and hand[0] in "AKQJ":
            return True
        if "low" in query and hand[0] in "23456":
            return True

        # Connector matching
        if "connector" in query and self._is_connector(hand):
            return True

        # Premium hand matching
        if "premium" in query and self._is_premium_hand(hand):
            return True

        return False

    def _is_connector(self, hand: str) -> bool:
        """Check if hand is a connector."""
        if len(hand) < 2:
            return False

        ranks = "23456789TJQKA"
        try:
            rank1, rank2 = hand[0], hand[1]
            if rank1 not in ranks or rank2 not in ranks:
                return False

            pos1 = ranks.index(rank1)
            pos2 = ranks.index(rank2)
            return abs(pos1 - pos2) == 1
        except (ValueError, IndexError):
            return False

    def _is_premium_hand(self, hand: str) -> bool:
        """Check if hand is premium."""
        premium_hands = ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77",
                        "AKs", "AKo", "AQs", "AQo", "AJs", "AJo",
                        "KQs", "KQo", "KJs", "KJo"]

        return hand in premium_hands

    def cycle_view_mode(self) -> str:
        """
        Cycle to the next view mode.

        Returns:
            New view mode
        """
        current_index = VIEW_MODES.index(self.state.view_mode)
        next_index = (current_index + 1) % len(VIEW_MODES)
        new_mode = VIEW_MODES[next_index]
        self.state.view_mode = new_mode
        return new_mode

    def get_navigation_info(self) -> Dict[str, Any]:
        """
        Get current navigation information.

        Returns:
            Dictionary with navigation state information
        """
        return {
            'mode': self.state.mode.value,
            'position': self.state.current_position,
            'selected_hand': self.state.selected_hand,
            'view_mode': self.state.view_mode,
            'range_builder_mode': self.state.range_builder_mode,
            'search_active': self.state.search_active,
            'search_query': self.state.search_query,
            'search_results_count': len(self.state.search_results),
            'search_index': self.state.search_index,
            'help_visible': self.state.help_visible,
            'context': {
                'chart_size': self.context.chart_size,
                'visible_rows': self.context.visible_rows,
                'visible_cols': self.context.visible_cols,
                'has_selection': self.context.has_selection,
                'in_range_builder': self.context.in_range_builder,
                'has_search_results': self.context.has_search_results
            }
        }

    def register_navigation_handler(self, name: str, handler: Callable):
        """
        Register a navigation handler.

        Args:
            name: Handler name
            handler: Handler function
        """
        self._navigation_handlers[name] = handler

    def get_navigation_handler(self, name: str) -> Optional[Callable]:
        """
        Get a navigation handler by name.

        Args:
            name: Handler name

        Returns:
            Handler function or None
        """
        return self._navigation_handlers.get(name)

    def handle_quick_navigation(self, key: str) -> Optional[Tuple[int, int]]:
        """
        Handle quick navigation keys.

        Args:
            key: Navigation key

        Returns:
            Target position or None
        """
        key_lower = key.lower()

        # Position shortcuts
        if key_lower in ['1', '2', '3', '4', '5', '6']:
            position_map = {'1': 'UTG', '2': 'MP', '3': 'CO',
                          '4': 'BTN', '5': 'SB', '6': 'BB'}
            position = position_map[key_lower]
            return self.jump_to_position(position)

        # Corner shortcuts
        elif key_lower == 'home':
            return (0, 0)  # Top-left
        elif key_lower == 'end':
            return (12, 12)  # Bottom-right

        # WASD navigation
        elif key_lower == 'w':
            return self.navigate_matrix(Direction.UP, *self.state.current_position)
        elif key_lower == 's':
            return self.navigate_matrix(Direction.DOWN, *self.state.current_position)
        elif key_lower == 'a':
            return self.navigate_matrix(Direction.LEFT, *self.state.current_position)
        elif key_lower == 'd':
            return self.navigate_matrix(Direction.RIGHT, *self.state.current_position)

        return None

    def get_movement_feedback(self, old_pos: Tuple[int, int], new_pos: Tuple[int, int],
                            hand: Optional[str], action: Optional[HandAction]) -> str:
        """
        Generate user feedback for movement.

        Args:
            old_pos: Previous position
            new_pos: New position
            hand: Selected hand
            action: Hand action

        Returns:
            Feedback message
        """
        if not hand or not action:
            return f"⚪ Position ({new_pos[0]}, {new_pos[1]})"

        # Action emoji mapping
        action_emojis = {
            "raise": "🔴",
            "call": "🟢",
            "fold": "⚫",
            "mixed": "🟡",
            "bluff": "🔵",
            "check": "⚪"
        }

        emoji = action_emojis.get(action.action.value, "⚪")
        frequency_info = f" ({action.frequency:.0%})" if action.frequency < 1.0 else ""

        return f"{emoji} {hand}: {action.action.value.title()}{frequency_info}"

    def update_context(self, **kwargs):
        """
        Update navigation context.

        Args:
            **kwargs: Context parameters to update
        """
        for key, value in kwargs.items():
            if hasattr(self.context, key):
                setattr(self.context, key, value)

    def reset_to_defaults(self):
        """Reset navigation state to defaults."""
        self.state = NavigationState()
        self.context = NavigationContext()

    def get_statistics(self) -> Dict[str, Any]:
        """Get navigation statistics."""
        return {
            'total_searches': len(self.state.search_results) if self.state.search_active else 0,
            'current_search_position': self.state.search_index + 1 if self.state.search_index >= 0 else 0,
            'navigation_mode': self.state.mode.value,
            'time_since_last_action': time.time() - self.state.last_action_time,
            'registered_handlers': len(self._navigation_handlers)
        }


# Global service instance
_navigation_service: Optional[NavigationService] = None


def get_navigation_service() -> NavigationService:
    """Get or create the global navigation service instance."""
    global _navigation_service
    if _navigation_service is None:
        _navigation_service = NavigationService()
    return _navigation_service


def reset_navigation_service():
    """Reset the global navigation service instance."""
    global _navigation_service
    _navigation_service = None
