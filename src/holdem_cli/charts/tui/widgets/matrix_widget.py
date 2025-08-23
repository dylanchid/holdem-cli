"""
Interactive hand matrix widget for the TUI.

This module contains the HandMatrixWidget class that provides an interactive
13x13 poker hand matrix display with navigation, selection, and multiple view modes.
"""

from textual.widgets import Static
from textual.reactive import reactive
from textual import events
from typing import Dict, Optional, Any, List
import hashlib

# Import the matrix classes from the current matrix.py file
from .matrix import HandMatrix, HandAction, ChartAction
from ...constants import HAND_MATRIX_CSS
from ...messages import HandSelected
from ...tui.core.render_optimizer import get_render_optimizer, optimized_render
from ...tui.core.performance import cached_render, get_performance_optimizer


class HandMatrixWidget(Static):
    """
    Interactive 13x13 poker hand matrix widget with enhanced features:
    - Multiple view modes (range, frequency, EV)
    - Range builder functionality
    - Efficient caching and rendering
    - Keyboard navigation
    - Search and filtering capabilities
    """
    
    CSS = HAND_MATRIX_CSS
    
    # Reactive properties for UI state
    selected_row: reactive[int] = reactive(0)
    selected_col: reactive[int] = reactive(0)
    view_mode: reactive[str] = reactive("range")
    range_builder_mode: reactive[bool] = reactive(False)
    
    def __init__(self, actions: Dict[str, HandAction], chart_name: str = "Chart", **kwargs):
        super().__init__(**kwargs)
        self.actions = actions
        self.chart_name = chart_name or "Chart"
        self.can_focus = True

        # Performance optimization - render caching
        self._render_cache = {}
        self._cache_max_size = 20  # Limit cache size to prevent memory leaks
        self._last_actions_hash = None

        # Performance and render optimization
        self._performance_optimizer = get_performance_optimizer()
        self._render_optimizer = get_render_optimizer()
        self._component_id = f"matrix_{id(self)}"

        # Virtual scrolling support
        self.virtual_scroll_enabled = False
        self.total_rows = 13
        self.visible_rows = (0, 13)

        # View modes
        self.view_mode = "range"
        self.supported_view_modes = ["range", "frequency", "ev"]

        # Range builder
        self.range_builder_mode = False
        self.custom_range = {}
        self.current_action_template = ChartAction.RAISE

        # Search functionality
        self.search_results = []
        self.current_search_index = -1

        # Create matrix instance for calculations
        self.matrix = HandMatrix(actions, chart_name)
    
    def _get_cache_key(self) -> str:
        """Generate cache key based on current state."""
        # Include all state that affects rendering
        state_components = [
            str(self.selected_row),
            str(self.selected_col),
            self.view_mode,
            str(len(self.actions)),
            str(self.range_builder_mode),
            str(len(self.custom_range)),
            str(hash(frozenset(self.actions.items())) if self.actions else 0)
        ]
        state_str = ":".join(state_components)
        return hashlib.md5(state_str.encode()).hexdigest()
    
    def _manage_cache_size(self) -> None:
        """Prevent cache from growing indefinitely."""
        if len(self._render_cache) > self._cache_max_size:
            # Remove oldest entries (simple FIFO)
            keys = list(self._render_cache.keys())
            for key in keys[:len(keys) - self._cache_max_size]:
                del self._render_cache[key]
    
    @optimized_render("matrix")
    def render(self) -> str:
        """Render the matrix with performance optimization."""
        # Use performance optimizer for caching
        cache_key = self._get_cache_key()

        def _do_render():
            lines = []

            # Title and header
            lines.extend(self._render_header())

            # Matrix body (with virtual scrolling if enabled)
            if self.virtual_scroll_enabled:
                lines.extend(self._render_virtual_matrix_body())
            else:
                lines.extend(self._render_matrix_body())

            # Statistics
            lines.extend(self._render_statistics())

            # Controls hint
            lines.append("")
            lines.append("[dim]Arrow keys: Navigate | Enter: Details | Tab: Next view | H: Help[/dim]")

            return "\n".join(lines)

        # Use performance-optimized rendering
        return self._performance_optimizer.cached_render(
            self._component_id,
            _do_render
        )
    
    def _render_header(self) -> List[str]:
        """Render header section."""
        lines = []
        
        # Title with mode indicators
        mode_suffix = f" ({self.view_mode.title()} View)"
        if self.range_builder_mode:
            mode_suffix += " 🔧"
        
        title = f"📊 {self.chart_name}{mode_suffix}"
        lines.append(title)
        lines.append("=" * len(title))
        lines.append("")
        
        # Column headers
        header = "     " + "".join(f"{rank:>4}" for rank in HandMatrix.RANKS)
        lines.append(header)
        
        return lines
    
    def _render_matrix_body(self) -> List[str]:
        """Render the matrix rows."""
        lines = []
        
        for i, rank in enumerate(HandMatrix.RANKS):
            row_parts = [f" {rank} "]
            
            for j in range(13):
                cell = self._render_cell(i, j)
                row_parts.append(f"{cell:>4}")
            
            lines.append("".join(row_parts))
        
        return lines

    def _render_virtual_matrix_body(self) -> List[str]:
        """Render matrix body with virtual scrolling optimization."""
        lines = []

        # Get visible row range
        row_start, row_end = self.visible_rows

        for i in range(row_start, min(row_end, len(HandMatrix.RANKS))):
            row_parts = [f" {HandMatrix.RANKS[i]} "]

            for j in range(13):
                cell = self._render_cell(i, j)
                row_parts.append(f"{cell:>4}")

            lines.append("".join(row_parts))

        return lines

    def _render_cell(self, row: int, col: int) -> str:
        """Render a single cell based on current state and view mode."""
        hand = self.matrix.get_hand_at_position(row, col)
        
        # Check if selected
        if row == self.selected_row and col == self.selected_col:
            if row == col:  # Pocket pair
                return f"[reverse][{hand}][/reverse]"
            else:
                return f"[reverse] {hand}[/reverse]"
        
        # Get action (from custom range if in builder mode, otherwise from chart)
        if self.range_builder_mode and hand in self.custom_range:
            action = self.custom_range[hand]
        else:
            action = self.matrix.get_action_for_hand(hand)
        
        if not action:
            # No action defined
            if row == col:
                return f"[{hand}]"
            else:
                return f" {hand}"
        
        # Render based on view mode
        if self.view_mode == "frequency":
            return self._render_frequency_cell(hand, action)
        elif self.view_mode == "ev":
            return self._render_ev_cell(hand, action)
        else:  # range view
            return self._render_range_cell(hand, action, row == col)
    
    def _render_range_cell(self, hand: str, action: HandAction, is_pair: bool) -> str:
        """Render cell in range view mode."""
        color_map = {
            ChartAction.RAISE: "red",
            ChartAction.CALL: "green",
            ChartAction.FOLD: "dim white",
            ChartAction.MIXED: "yellow",
            ChartAction.BLUFF: "blue",
            ChartAction.CHECK: "cyan"
        }
        
        color = color_map.get(action.action, "white")
        
        if is_pair:
            return f"[{color}][{hand}][/{color}]"
        else:
            return f"[{color}] {hand}[/{color}]"
    
    def _render_frequency_cell(self, hand: str, action: HandAction) -> str:
        """Render cell in frequency view mode."""
        freq_pct = action.frequency * 100
        
        if freq_pct >= 80:
            color = "green"
        elif freq_pct >= 50:
            color = "yellow"
        else:
            color = "red"
        
        return f"[{color}]{freq_pct:3.0f}%[/{color}]"
    
    def _render_ev_cell(self, hand: str, action: HandAction) -> str:
        """Render cell in EV view mode."""
        if action.ev is None:
            return " N/A"
        
        if action.ev > 1.0:
            color = "green"
        elif action.ev > 0:
            color = "yellow"
        else:
            color = "red"
        
        return f"[{color}]{action.ev:+3.1f}[/{color}]"
    
    def _render_statistics(self) -> List[str]:
        """Render statistics section."""
        lines = []
        lines.append("")
        
        # Use the existing matrix statistics calculation
        stats = self.matrix._calculate_statistics()
        lines.extend(stats)
        
        # Add view-specific stats
        if self.view_mode == "frequency":
            lines.append("")
            lines.append("Frequency Distribution:")
            freq_dist = self._calculate_frequency_distribution()
            lines.extend(freq_dist)
        elif self.view_mode == "ev":
            lines.append("")
            lines.append("EV Analysis:")
            ev_stats = self._calculate_ev_statistics()
            lines.extend(ev_stats)
        
        # Range builder stats
        if self.range_builder_mode and self.custom_range:
            lines.append("")
            lines.append(f"Custom Range: {len(self.custom_range)} hands")
        
        return lines
    
    def _calculate_frequency_distribution(self) -> List[str]:
        """Calculate frequency distribution for frequency view."""
        buckets = {"100%": 0, "75-99%": 0, "50-74%": 0, "25-49%": 0, "0-24%": 0}
        
        for action in self.actions.values():
            freq_pct = action.frequency * 100
            if freq_pct == 100:
                buckets["100%"] += 1
            elif freq_pct >= 75:
                buckets["75-99%"] += 1
            elif freq_pct >= 50:
                buckets["50-74%"] += 1
            elif freq_pct >= 25:
                buckets["25-49%"] += 1
            else:
                buckets["0-24%"] += 1
        
        return [f"  {k}: {v} hands" for k, v in buckets.items()]
    
    def _calculate_ev_statistics(self) -> List[str]:
        """Calculate EV statistics for EV view."""
        ev_values = [a.ev for a in self.actions.values() if a.ev is not None]
        
        if not ev_values:
            return ["  No EV data available"]
        
        avg_ev = sum(ev_values) / len(ev_values)
        max_ev = max(ev_values)
        min_ev = min(ev_values)
        positive_ev = sum(1 for ev in ev_values if ev > 0)
        
        return [
            f"  Average EV: {avg_ev:+.2f}bb",
            f"  Max EV: {max_ev:+.2f}bb",
            f"  Min EV: {min_ev:+.2f}bb",
            f"  Positive EV hands: {positive_ev}/{len(ev_values)}"
        ]
    
    def on_key(self, event: events.Key) -> None:
        """Handle keyboard input with improved navigation."""
        # Navigation
        if event.key == "up":
            self.selected_row = max(0, self.selected_row - 1)
            self._update_selection()
            event.prevent_default()
        elif event.key == "down":
            self.selected_row = min(12, self.selected_row + 1)
            self._update_selection()
            event.prevent_default()
        elif event.key == "left":
            self.selected_col = max(0, self.selected_col - 1)
            self._update_selection()
            event.prevent_default()
        elif event.key == "right":
            self.selected_col = min(12, self.selected_col + 1)
            self._update_selection()
            event.prevent_default()
        
        # Alternative navigation (WASD)
        elif event.key == "w":
            self.selected_row = max(0, self.selected_row - 1)
            self._update_selection()
            event.prevent_default()
        elif event.key == "s":
            self.selected_row = min(12, self.selected_row + 1)
            self._update_selection()
            event.prevent_default()
        elif event.key == "a":
            self.selected_col = max(0, self.selected_col - 1)
            self._update_selection()
            event.prevent_default()
        elif event.key == "d":
            self.selected_col = min(12, self.selected_col + 1)
            self._update_selection()
            event.prevent_default()
        
        # Jump to corners
        elif event.key == "home":
            self.selected_row = 0
            self.selected_col = 0
            self._update_selection()
            event.prevent_default()
        elif event.key == "end":
            self.selected_row = 12
            self.selected_col = 12
            self._update_selection()
            event.prevent_default()
        
        # Selection
        elif event.key in ["enter", "space"]:
            self._show_hand_details()
            event.prevent_default()
        
        # Range builder actions (if enabled)
        elif self.range_builder_mode:
            if event.key == "a":
                self._add_hand_to_custom_range()
                event.prevent_default()
            elif event.key == "d":
                self._remove_hand_from_custom_range()
                event.prevent_default()
    
    def _update_selection(self) -> None:
        """Update selection and refresh display."""
        # Clear cache to force re-render with new selection
        self._render_cache.clear()
        self.refresh()
    
    def _show_hand_details(self) -> None:
        """Show details for currently selected hand."""
        hand = self.matrix.get_hand_at_position(self.selected_row, self.selected_col)
        self.post_message(HandSelected(hand))
    
    def _add_hand_to_custom_range(self) -> None:
        """Add currently selected hand to custom range."""
        if not self.range_builder_mode:
            return
        
        hand = self.get_selected_hand()
        if hand:
            action = HandAction(
                action=self.current_action_template,
                frequency=1.0,
                ev=0.5,
                notes="Added via range builder"
            )
            self.custom_range[hand] = action
            self._render_cache.clear()
            self.refresh()
    
    def _remove_hand_from_custom_range(self) -> None:
        """Remove currently selected hand from custom range."""
        if not self.range_builder_mode:
            return
        
        hand = self.get_selected_hand()
        if hand and hand in self.custom_range:
            del self.custom_range[hand]
            self._render_cache.clear()
            self.refresh()
    
    def get_selected_hand(self) -> str:
        """Get currently selected hand."""
        return self.matrix.get_hand_at_position(self.selected_row, self.selected_col)
    
    def update_actions(self, new_actions: Dict[str, HandAction]) -> None:
        """Update the chart actions and refresh display."""
        self.actions = new_actions
        self.matrix = HandMatrix(new_actions, self.chart_name)
        self._render_cache.clear()  # Clear cache when data changes
        self._last_actions_hash = None
        self.refresh()
    
    def set_view_mode(self, mode: str) -> None:
        """Set the view mode and refresh display."""
        if mode in self.supported_view_modes:
            self.view_mode = mode
            self._render_cache.clear()
            self.refresh()
    
    def toggle_range_builder(self) -> None:
        """Toggle range builder mode."""
        self.range_builder_mode = not self.range_builder_mode
        self._render_cache.clear()
        self.refresh()
    
    def clear_custom_range(self) -> None:
        """Clear the custom range."""
        self.custom_range.clear()
        if self.range_builder_mode:
            self._render_cache.clear()
            self.refresh()
    
    def set_action_template(self, action: ChartAction) -> None:
        """Set the action template for range builder."""
        self.current_action_template = action
    
    def navigate_to_hand(self, hand: str) -> bool:
        """Navigate to a specific hand in the matrix."""
        for row in range(13):
            for col in range(13):
                matrix_hand = self.matrix.get_hand_at_position(row, col)
                if matrix_hand == hand:
                    self.selected_row = row
                    self.selected_col = col
                    self._update_selection()
                    return True
        return False
    
    def search_hands(self, query: str) -> List[str]:
        """Search for hands matching the query."""
        self.search_results = []
        query_lower = query.lower()
        
        for hand, action in self.actions.items():
            if self._hand_matches_query(hand, action, query_lower):
                self.search_results.append(hand)
        
        self.current_search_index = -1
        return self.search_results
    
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
        
        return False
    
    def next_search_result(self) -> Optional[str]:
        """Navigate to next search result."""
        if not self.search_results:
            return None
        
        self.current_search_index = (self.current_search_index + 1) % len(self.search_results)
        hand = self.search_results[self.current_search_index]
        self.navigate_to_hand(hand)
        return hand
    
    def prev_search_result(self) -> Optional[str]:
        """Navigate to previous search result."""
        if not self.search_results:
            return None
        
        self.current_search_index = (self.current_search_index - 1) % len(self.search_results)
        hand = self.search_results[self.current_search_index]
        self.navigate_to_hand(hand)
        return hand
    
    def get_selection_info(self) -> Dict[str, Any]:
        """Get information about the current selection."""
        hand = self.get_selected_hand()
        action = None
        
        if self.range_builder_mode and hand in self.custom_range:
            action = self.custom_range[hand]
        else:
            action = self.matrix.get_action_for_hand(hand)
        
        return {
            "hand": hand,
            "row": self.selected_row,
            "col": self.selected_col,
            "action": action,
            "view_mode": self.view_mode,
            "range_builder": self.range_builder_mode
        }
    
    def get_chart_summary(self) -> Dict[str, Any]:
        """Get a summary of the current chart state."""
        total_hands = len(self.actions)
        custom_hands = len(self.custom_range) if self.range_builder_mode else 0
        
        # Action distribution
        action_counts = {}
        for action in self.actions.values():
            action_name = action.action.value
            action_counts[action_name] = action_counts.get(action_name, 0) + 1
        
        return {
            "name": self.chart_name,
            "total_hands": total_hands,
            "custom_hands": custom_hands,
            "view_mode": self.view_mode,
            "range_builder": self.range_builder_mode,
            "action_distribution": action_counts,
            "selected_hand": self.get_selected_hand()
        }
    
    def clear_cache(self) -> None:
        """Explicitly clear the render cache."""
        self._render_cache.clear()
        self._last_actions_hash = None
    
    def export_matrix_data(self) -> Dict[str, Any]:
        """Export matrix data for external use."""
        return {
            "chart_name": self.chart_name,
            "actions": {
                hand: {
                    "action": action.action.value,
                    "frequency": action.frequency,
                    "ev": action.ev,
                    "notes": action.notes
                }
                for hand, action in self.actions.items()
            },
            "custom_range": {
                hand: {
                    "action": action.action.value,
                    "frequency": action.frequency,
                    "ev": action.ev,
                    "notes": action.notes
                }
                for hand, action in self.custom_range.items()
            } if self.range_builder_mode else {},
            "view_mode": self.view_mode,
            "selection": {
                "row": self.selected_row,
                "col": self.selected_col,
                "hand": self.get_selected_hand()
            }
        }


# Utility functions for HandMatrixWidget
def create_matrix_widget(chart_data: Dict[str, HandAction], chart_name: str = "Chart") -> HandMatrixWidget:
    """Create a configured HandMatrixWidget."""
    return HandMatrixWidget(chart_data, chart_name)


def merge_chart_actions(base_actions: Dict[str, HandAction], 
                       overlay_actions: Dict[str, HandAction]) -> Dict[str, HandAction]:
    """Merge two sets of chart actions, with overlay taking precedence."""
    merged = base_actions.copy()
    merged.update(overlay_actions)
    return merged


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
