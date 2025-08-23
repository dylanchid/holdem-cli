# src/holdem_cli/charts/tui/widgets/matrix.py
"""13x13 poker hand matrix renderer for terminal output."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum
import math

from holdem_cli.types import ChartAction, HandAction, Color

class HandMatrix:
    """Renders standard 13x13 poker hand matrix."""
    
    RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
    
    # Matrix layout: [row][col] where row=first card, col=second card
    # Upper triangle: suited hands (s)
    # Diagonal: pocket pairs
    # Lower triangle: offsuit hands (o)
    HAND_MATRIX = [
        ["AA", "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s"],
        ["AKo", "KK", "KQs", "KJs", "KTs", "K9s", "K8s", "K7s", "K6s", "K5s", "K4s", "K3s", "K2s"],
        ["AQo", "KQo", "QQ", "QJs", "QTs", "Q9s", "Q8s", "Q7s", "Q6s", "Q5s", "Q4s", "Q3s", "Q2s"],
        ["AJo", "KJo", "QJo", "JJ", "JTs", "J9s", "J8s", "J7s", "J6s", "J5s", "J4s", "J3s", "J2s"],
        ["ATo", "KTo", "QTo", "JTo", "TT", "T9s", "T8s", "T7s", "T6s", "T5s", "T4s", "T3s", "T2s"],
        ["A9o", "K9o", "Q9o", "J9o", "T9o", "99", "98s", "97s", "96s", "95s", "94s", "93s", "92s"],
        ["A8o", "K8o", "Q8o", "J8o", "T8o", "98o", "88", "87s", "86s", "85s", "84s", "83s", "82s"],
        ["A7o", "K7o", "Q7o", "J7o", "T7o", "97o", "87o", "77", "76s", "75s", "74s", "73s", "72s"],
        ["A6o", "K6o", "Q6o", "J6o", "T6o", "96o", "86o", "76o", "66", "65s", "64s", "63s", "62s"],
        ["A5o", "K5o", "Q5o", "J5o", "T5o", "95o", "85o", "75o", "65o", "55", "54s", "53s", "52s"],
        ["A4o", "K4o", "Q4o", "J4o", "T4o", "94o", "84o", "74o", "64o", "54o", "44", "43s", "42s"],
        ["A3o", "K3o", "Q3o", "J3o", "T3o", "93o", "83o", "73o", "63o", "53o", "43o", "33", "32s"],
        ["A2o", "K2o", "Q2o", "J2o", "T2o", "92o", "82o", "72o", "62o", "52o", "42o", "32o", "22"]
    ]
    
    def __init__(self, actions: Dict[str, HandAction], title: str = "Poker Hand Chart"):
        """Initialize matrix with actions for each hand."""
        self.actions = actions
        self.title = title
        self.width = 80
        self.height = 20
    
    def get_hand_at_position(self, row: int, col: int) -> str:
        """Get hand string at matrix position."""
        if 0 <= row < 13 and 0 <= col < 13:
            return self.HAND_MATRIX[row][col]
        return ""
    
    def get_action_for_hand(self, hand: str) -> Optional[HandAction]:
        """Get action for specific hand."""
        return self.actions.get(hand)
    
    def render(self, use_colors: bool = True, compact: bool = False) -> str:
        """Render the matrix as a string."""
        if compact:
            return self._render_compact(use_colors)
        else:
            return self._render_full(use_colors)
    
    def _render_full(self, use_colors: bool) -> str:
        """Render full-size matrix with borders."""
        lines = []
        
        # Top border with title
        border_len = min(len(self.title) + 4, 66)
        lines.append("╔" + "═" * border_len + "╗")
        lines.append(f"║ {self.title:<{border_len-2}} ║")
        lines.append("╠" + "═" * border_len + "╣")
        
        # Header row
        header = "║     " + "".join(f"{rank:>4}" for rank in self.RANKS) + " ║"
        lines.append(header)
        
        # Matrix rows
        for i, rank in enumerate(self.RANKS):
            row_parts = [f"║ {rank} "]
            
            for j in range(13):
                hand = self.get_hand_at_position(i, j)
                action = self.get_action_for_hand(hand)
                
                if action and use_colors:
                    if i == j:  # Pocket pairs - use brackets
                        cell = f"{action.bg_color}[{hand}]{Color.RESET}"
                    else:
                        cell = f"{action.color}{hand:>3}{Color.RESET}"
                else:
                    if i == j:  # Pocket pairs
                        cell = f"[{hand}]"
                    else:
                        cell = f"{hand:>3}"
                
                row_parts.append(f"{cell:>4}")
            
            row_parts.append(" ║")
            lines.append("".join(row_parts))
        
        # Statistics footer
        lines.append("╠" + "═" * border_len + "╣")
        stats = self._calculate_statistics()
        for stat_line in stats:
            lines.append(f"║ {stat_line:<{border_len-2}} ║")
        
        # Bottom border
        lines.append("╚" + "═" * border_len + "╝")
        
        return "\n".join(lines)
    
    def _render_compact(self, use_colors: bool) -> str:
        """Render compact matrix without borders."""
        lines = []
        
        # Title
        lines.append(f"\n{self.title}")
        lines.append("=" * len(self.title))
        
        # Header
        header = "     " + "".join(f"{rank:>3}" for rank in self.RANKS)
        lines.append(header)
        
        # Matrix rows
        for i, rank in enumerate(self.RANKS):
            row_parts = [f" {rank} "]
            
            for j in range(13):
                hand = self.get_hand_at_position(i, j)
                action = self.get_action_for_hand(hand)
                
                if action and use_colors:
                    cell = f"{action.color}{hand}{Color.RESET}"
                else:
                    cell = hand
                
                row_parts.append(f"{cell:>3}")
            
            lines.append("".join(row_parts))
        
        # Statistics
        lines.append("")
        stats = self._calculate_statistics()
        lines.extend(stats)
        
        return "\n".join(lines)
    
    def _calculate_statistics(self) -> List[str]:
        """Calculate and format statistics."""
        stats = {}
        total_combos = 0
        
        for hand in self.actions:
            action = self.actions[hand]
            action_name = action.action.value.title()
            
            if action_name not in stats:
                stats[action_name] = 0
            
            # Calculate combinations for this hand
            if hand.endswith('s') or hand.endswith('o'):
                # Suited/offsuit non-pairs
                combos = 4 if hand.endswith('s') else 12
            elif len(set(hand[:2])) == 1:
                # Pocket pairs
                combos = 6
            else:
                combos = 1
            
            stats[action_name] += combos
            total_combos += combos
        
        result = []
        for action_name, combos in stats.items():
            percentage = (combos / 1326) * 100 if total_combos > 0 else 0
            result.append(f"▓ {action_name}: {percentage:.1f}% ({combos} combos)")
        
        return result
    
    def export_to_text(self, filepath: str) -> None:
        """Export matrix to text file."""
        with open(filepath, 'w') as f:
            f.write(self.render(use_colors=False))
    
    def get_hand_details(self, hand: str) -> str:
        """Get detailed information about a specific hand."""
        action = self.get_action_for_hand(hand)
        if not action:
            return f"No action defined for {hand}"
        
        details = [
            f"Hand: {hand}",
            f"Action: {action.action.value.title()}",
            f"Frequency: {action.frequency:.1%}"
        ]
        
        if action.ev is not None:
            details.append(f"EV: {action.ev:+.2f}bb")
        
        if action.notes:
            details.append(f"Notes: {action.notes}")
        
        return "\n".join(details)


class MultiRangeDisplay:
    """Display multiple position ranges in a grid."""
    
    def __init__(self, ranges: Dict[str, Dict[str, HandAction]]):
        """Initialize with ranges for different positions."""
        self.ranges = ranges
    
    def render_grid(self, positions: List[str], use_colors: bool = True) -> str:
        """Render multiple ranges in a 2x3 or 3x2 grid."""
        if len(positions) > 6:
            positions = positions[:6]
        
        # Create mini matrices for each position
        matrices = {}
        for pos in positions:
            if pos in self.ranges:
                matrix = HandMatrix(self.ranges[pos], title=pos)
                matrices[pos] = matrix
        
        # Arrange in grid
        if len(positions) <= 3:
            rows = 1
            cols = len(positions)
        else:
            rows = 2
            cols = 3
        
        lines = []
        
        for row in range(rows):
            row_positions = positions[row * cols:(row + 1) * cols]
            row_matrices = [matrices[pos] for pos in row_positions if pos in matrices]
            
            if not row_matrices:
                continue
            
            # Render each matrix in compact mode
            rendered_matrices = [matrix.render(use_colors=use_colors, compact=True).split('\n') 
                               for matrix in row_matrices]
            
            # Find max height
            max_height = max(len(rendered) for rendered in rendered_matrices)
            
            # Pad matrices to same height
            for rendered in rendered_matrices:
                while len(rendered) < max_height:
                    rendered.append("")
            
            # Combine side by side
            for line_idx in range(max_height):
                line_parts = []
                for rendered in rendered_matrices:
                    line_parts.append(f"{rendered[line_idx]:<30}")
                lines.append("  ".join(line_parts))
            
            lines.append("")  # Spacing between rows
        
        return "\n".join(lines)


class FrequencyHeatMap:
    """Shows call/raise/fold frequencies with gradient colors."""
    
    def __init__(self, frequencies: Dict[str, float]):
        """Initialize with frequency data for each hand."""
        self.frequencies = frequencies
    
    def gradient_color(self, frequency: float) -> str:
        """Get gradient color based on frequency (0.0 to 1.0)."""
        if frequency < 0.33:
            # Dark blue to green
            return Color.BLUE
        elif frequency < 0.66:
            # Green to yellow
            return Color.GREEN
        else:
            # Yellow to red
            return Color.RED
    
    def render_heatmap(self, title: str = "Frequency Heatmap") -> str:
        """Render frequency heatmap using the hand matrix."""
        actions = {}
        for hand, freq in self.frequencies.items():
            color = self.gradient_color(freq)
            # Create pseudo-action for coloring
            actions[hand] = HandAction(ChartAction.MIXED, frequency=freq)
        
        matrix = HandMatrix(actions, title)
        return matrix.render(use_colors=True)


class ChartComparison:
    """Compare two ranges side by side."""
    
    def __init__(self, range1: Dict[str, HandAction], range2: Dict[str, HandAction],
                 name1: str = "Range 1", name2: str = "Range 2"):
        """Initialize with two ranges to compare."""
        self.range1 = range1
        self.range2 = range2
        self.name1 = name1
        self.name2 = name2
    
    def find_differences(self) -> Dict[str, Tuple[Optional[ChartAction], Optional[ChartAction]]]:
        """Find differences between the two ranges."""
        differences = {}
        all_hands = set(self.range1.keys()) | set(self.range2.keys())
        
        for hand in all_hands:
            action1 = self.range1.get(hand)
            action2 = self.range2.get(hand)
            
            if action1 is None and action2 is not None:
                differences[hand] = (None, action2.action)
            elif action1 is not None and action2 is None:
                differences[hand] = (action1.action, None)
            elif action1 and action2 and action1.action != action2.action:
                differences[hand] = (action1.action, action2.action)
        
        return differences
    
    def calculate_accuracy(self) -> float:
        """Calculate accuracy percentage between ranges."""
        all_hands = set(self.range1.keys()) | set(self.range2.keys())
        if not all_hands:
            return 100.0
        
        matches = 0
        for hand in all_hands:
            action1 = self.range1.get(hand)
            action2 = self.range2.get(hand)
            
            if action1 is None and action2 is None:
                matches += 1
            elif action1 and action2 and action1.action == action2.action:
                matches += 1
        
        return (matches / len(all_hands)) * 100
    
    def render_comparison(self, use_colors: bool = True) -> str:
        """Render side-by-side comparison with proper formatting."""
        # Create a simplified comparison format that's easier to read
        lines = []

        # Header with chart names
        lines.append(f"{'=' * 60}")
        lines.append(f"📊 CHART COMPARISON")
        lines.append(f"{'=' * 60}")
        lines.append(f"LEFT:  {self.name1}")
        lines.append(f"RIGHT: {self.name2}")
        lines.append("")

        # Get basic statistics for both ranges
        stats1 = self._get_range_stats(self.range1)
        stats2 = self._get_range_stats(self.range2)

        # Display statistics comparison
        lines.append("📈 RANGE STATISTICS:")
        lines.append("-" * 60)
        lines.append(f"{'Category':<12} {'Left':<15} {'Right':<15} {'Difference'}")
        lines.append("-" * 60)

        categories = ['Total Hands', 'Raise %', 'Call %', 'Mixed %', 'Fold %']
        for cat in categories:
            val1 = stats1.get(cat, 0)
            val2 = stats2.get(cat, 0)
            if isinstance(val1, float):
                val1_str = f"{val1:.1f}%"
                val2_str = f"{val2:.1f}%"
                diff = f"{val1 - val2:+.1f}%"
            else:
                val1_str = str(val1)
                val2_str = str(val2)
                diff = f"{val1 - val2:+d}"
            lines.append(f"{cat:<12} {val1_str:<15} {val2_str:<15} {diff}")

        # Overall accuracy
        differences = self.find_differences()
        accuracy = self.calculate_accuracy()
        lines.append("")
        lines.append(f"🎯 OVERALL ACCURACY: {accuracy:.1f}%")
        lines.append(f"🔍 TOTAL DIFFERENCES: {len(differences)} hands")

        # Show key differences
        if differences:
            lines.append("")
            lines.append("🔍 SIGNIFICANT DIFFERENCES:")
            lines.append("-" * 60)

            # Sort by significance
            hand_ranks = {
                'AA': 1, 'KK': 2, 'QQ': 3, 'JJ': 4, 'TT': 5, '99': 6, '88': 7, '77': 8,
                'AKs': 9, 'AKo': 10, 'AQs': 11, 'AQo': 12, 'AJs': 13, 'AJo': 14,
                'ATs': 15, 'KQs': 16, 'KJs': 17, 'QJs': 18, 'JTs': 19, 'T9s': 20
            }

            sorted_diffs = sorted(differences.items(),
                                key=lambda x: hand_ranks.get(x[0], 99))

            for i, (hand, (action1, action2)) in enumerate(sorted_diffs[:20]):
                action1_str = action1.value if action1 else "❌"
                action2_str = action2.value if action2 else "❌"
                lines.append(f"  {i+1:2d}. {hand}: {action1_str} → {action2_str}")

            if len(differences) > 20:
                lines.append(f"      ... and {len(differences) - 20} more differences")

        # Show detailed hand-by-hand comparison for key areas
        lines.append("")
        lines.append("🎴 DETAILED HAND COMPARISON:")
        lines.append("-" * 60)

        # Group hands by strength for better organization
        hand_groups = [
            ("Premium Pairs", ['AA', 'KK', 'QQ', 'JJ', 'TT']),
            ("Strong Pairs", ['99', '88', '77', '66']),
            ("Premium Aces", ['AKs', 'AKo', 'AQs', 'AQo', 'AJs', 'AJo']),
            ("Strong Aces", ['ATs', 'ATo', 'A9s', 'A8s']),
            ("Broadways", ['KQs', 'KJs', 'QJs', 'QTs', 'JTs', 'T9s']),
            ("Suited Connectors", ['98s', '87s', '76s', '65s'])
        ]

        for group_name, hands in hand_groups:
            group_diffs = []
            for hand in hands:
                if hand in differences:
                    action1, action2 = differences[hand]
                    action1_str = action1.value if action1 else "❌"
                    action2_str = action2.value if action2 else "❌"
                    group_diffs.append(f"{hand}({action1_str}→{action2_str})")

            if group_diffs:
                lines.append(f"\n{group_name}:")
                # Show differences in a more compact format
                diff_text = ", ".join(group_diffs[:8])  # Limit to 8 per line
                lines.append(f"  {diff_text}")
                if len(group_diffs) > 8:
                    remaining = ", ".join(group_diffs[8:])
                    lines.append(f"  {remaining}")

        return "\n".join(lines)

    def _get_range_stats(self, range_data: Dict[str, HandAction]) -> Dict[str, float]:
        """Get statistics for a range."""
        total_hands = len(range_data)
        if total_hands == 0:
            return {'Total Hands': 0, 'Raise %': 0.0, 'Call %': 0.0, 'Mixed %': 0.0, 'Fold %': 0.0}

        raise_count = sum(1 for a in range_data.values() if a.action == ChartAction.RAISE)
        call_count = sum(1 for a in range_data.values() if a.action == ChartAction.CALL)
        mixed_count = sum(1 for a in range_data.values() if a.action == ChartAction.MIXED)
        fold_count = sum(1 for a in range_data.values() if a.action == ChartAction.FOLD)

        return {
            'Total Hands': total_hands,
            'Raise %': (raise_count / total_hands) * 100,
            'Call %': (call_count / total_hands) * 100,
            'Mixed %': (mixed_count / total_hands) * 100,
            'Fold %': (fold_count / total_hands) * 100
        }


# Example usage and test data
def create_sample_range() -> Dict[str, HandAction]:
    """Create a comprehensive sample GTO range for testing."""
    # Check memory manager cache first
    try:
        from ..core.performance import get_memory_manager
        memory_manager = get_memory_manager()
        cached_range = memory_manager.get_chart_data("sample_range")
        if cached_range:
            return cached_range
    except ImportError:
        pass

    # Create new sample range
    sample_range = {}
    # Use the GTO library to create a standard BTN vs BB chart
    from ...gto_library import GTOChartLibrary
    sample_range = GTOChartLibrary.create_position_chart("BTN", "BB", 100)

    # Cache it for future use
    try:
        memory_manager.cache_chart_data("sample_range", sample_range, strong_ref=True)
    except (ImportError, NameError):
        pass

    return sample_range


def create_sample_range_lightweight() -> Dict[str, HandAction]:
    """Create a lightweight sample range for memory-constrained environments."""
    # Check memory manager cache first
    try:
        from ..core.performance import get_memory_manager
        memory_manager = get_memory_manager()
        cached_range = memory_manager.get_chart_data("sample_range_lightweight")
        if cached_range:
            return cached_range
    except ImportError:
        pass

    # Create a smaller sample range with fewer hands
    sample_range = {}
    # Use the GTO library to create a smaller chart
    from ...gto_library import GTOChartLibrary
    sample_range = GTOChartLibrary.create_position_chart("BTN", "BB", 50)  # Half the size

    # Cache it for future use
    try:
        memory_manager.cache_chart_data("sample_range_lightweight", sample_range, strong_ref=True)
    except (ImportError, NameError):
        pass

    return sample_range


def demo_chart_rendering():
    """Demonstrate chart rendering capabilities."""
    print("Holdem CLI Chart Rendering Demo")
    print("=" * 40)
    
    # Create sample range
    sample_range = create_sample_range()
    
    # Basic matrix
    print("\n1. Basic Hand Matrix:")
    matrix = HandMatrix(sample_range, "BTN vs BB 3-Bet Defense")
    print(matrix.render())
    
    # Compact version
    print("\n2. Compact Matrix:")
    print(matrix.render(compact=True))
    
    # Hand details
    print("\n3. Hand Details:")
    print(matrix.get_hand_details("AKs"))
    
    # Frequency heatmap
    print("\n4. Frequency Heatmap:")
    frequencies = {hand: action.frequency for hand, action in sample_range.items()}
    heatmap = FrequencyHeatMap(frequencies)
    print(heatmap.render_heatmap("Action Frequencies"))
    
    # Range comparison
    print("\n5. Range Comparison:")
    # Create a slightly different range for comparison
    user_range = sample_range.copy()
    user_range["99"] = HandAction(ChartAction.FOLD, frequency=1.0)  # Different action
    user_range["88"] = HandAction(ChartAction.CALL, frequency=1.0)  # Different action
    
    comparison = ChartComparison(sample_range, user_range, "GTO Range", "User Range")
    print(comparison.render_comparison())


if __name__ == "__main__":
    demo_chart_rendering()