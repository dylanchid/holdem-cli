"""
Hand details widget for displaying information about selected poker hands.

This widget shows comprehensive information about a selected hand including:
- Hand strength analysis
- Action details (frequency, EV, notes)
- Position-based recommendations
- Historical statistics
"""

from textual.widgets import Static
from textual.reactive import reactive
from typing import Optional, Dict, Any, List

from .matrix import HandAction, ChartAction
from ...constants import HAND_DETAILS_CSS


class HandDetailsWidget(Static):
    """Widget showing detailed information for a selected hand."""
    
    CSS = HAND_DETAILS_CSS
    
    current_hand: reactive[str] = reactive("")
    current_action: reactive[Optional[HandAction]] = reactive(None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_hand = ""
        self.current_action = None
        self.hand_history = []  # Track recently viewed hands
        self.max_history = 10
    
    def update_hand(self, hand: str, action: Optional[HandAction]) -> None:
        """Update displayed hand details."""
        # Add to history if different hand
        if hand != self.current_hand and hand:
            self.hand_history.append(self.current_hand)
            if len(self.hand_history) > self.max_history:
                self.hand_history.pop(0)
        
        self.current_hand = hand
        self.current_action = action
        self.refresh()
    
    def render(self) -> str:
        """Render hand details."""
        if not self.current_hand:
            return self._render_empty_state()
        
        lines = [
            f"[bold]🃏 Hand: {self.current_hand}[/bold]",
            ""
        ]
        
        # Action information
        lines.extend(self._render_action_info())
        
        # Hand analysis
        lines.extend(self._render_hand_analysis())
        
        # Position recommendations
        lines.extend(self._render_position_recommendations())
        
        # Recent history
        if self.hand_history:
            lines.extend(self._render_recent_history())
        
        return "\n".join(lines)
    
    def _render_empty_state(self) -> str:
        """Render empty state when no hand is selected."""
        return """[dim]Select a hand to view details[/dim]

[bold]Navigation Tips:[/bold]
• Use arrow keys to navigate
• Press Enter to select a hand
• Press H for help
• Press Tab to switch panels

[bold]Hand Categories:[/bold]
🔴 Raise  🟢 Call  ⚫ Fold
🟡 Mixed  🔵 Bluff  🟦 Check"""
    
    def _render_action_info(self) -> List[str]:
        """Render action information section."""
        lines = []
        
        if self.current_action:
            # Action with emoji
            action_emoji = self._get_action_emoji(self.current_action.action)
            lines.extend([
                f"{action_emoji} Action: [bold]{self.current_action.action.value.title()}[/bold]",
                f"📊 Frequency: [bold]{self.current_action.frequency:.1%}[/bold]"
            ])
            
            # EV information
            if self.current_action.ev is not None:
                ev_color = "green" if self.current_action.ev > 0 else "red"
                lines.append(f"💰 Expected Value: [{ev_color}]{self.current_action.ev:+.2f}bb[/{ev_color}]")
            
            # Frequency interpretation
            freq_interpretation = self._interpret_frequency(self.current_action.frequency)
            lines.append(f"📈 Play: [dim]{freq_interpretation}[/dim]")
            
            # Notes
            if self.current_action.notes:
                lines.extend([
                    "",
                    "📝 Notes:",
                    f"[dim]{self.current_action.notes}[/dim]"
                ])
        else:
            lines.append("[dim]No action defined for this hand[/dim]")
        
        return lines
    
    def _render_hand_analysis(self) -> List[str]:
        """Render hand analysis section."""
        lines = [
            "",
            "[bold]🔍 Hand Analysis:[/bold]"
        ]
        
        if not self.current_hand:
            return lines
        
        # Hand type classification
        hand_type = self._classify_hand_type()
        lines.append(f"Type: {hand_type}")
        
        # Strength assessment
        strength = self._assess_hand_strength()
        lines.append(f"Strength: {strength}")
        
        # Playability factors
        playability = self._assess_playability()
        lines.extend(playability)
        
        return lines
    
    def _render_position_recommendations(self) -> List[str]:
        """Render position-based recommendations."""
        lines = [
            "",
            "[bold]📍 Position Play:[/bold]"
        ]
        
        recommendations = self._get_position_recommendations()
        for position, recommendation in recommendations.items():
            lines.append(f"• {position}: {recommendation}")
        
        return lines
    
    def _render_recent_history(self) -> List[str]:
        """Render recently viewed hands."""
        lines = [
            "",
            "[bold]📚 Recent:[/bold]"
        ]
        
        # Show last 5 hands
        recent_hands = [h for h in self.hand_history[-5:] if h]
        if recent_hands:
            hands_str = " → ".join(recent_hands)
            lines.append(f"[dim]{hands_str}[/dim]")
        
        return lines
    
    def _get_action_emoji(self, action: ChartAction) -> str:
        """Get emoji for action type."""
        emoji_map = {
            ChartAction.RAISE: "🔴",
            ChartAction.CALL: "🟢",
            ChartAction.FOLD: "⚫",
            ChartAction.MIXED: "🟡",
            ChartAction.BLUFF: "🔵",
            ChartAction.CHECK: "🟦"
        }
        return emoji_map.get(action, "⚪")
    
    def _interpret_frequency(self, frequency: float) -> str:
        """Interpret frequency for user understanding."""
        if frequency >= 0.9:
            return "Always or almost always"
        elif frequency >= 0.7:
            return "Most of the time"
        elif frequency >= 0.5:
            return "About half the time"
        elif frequency >= 0.3:
            return "Sometimes"
        elif frequency >= 0.1:
            return "Rarely"
        else:
            return "Almost never"
    
    def _classify_hand_type(self) -> str:
        """Classify the hand type."""
        hand = self.current_hand
        
        if len(hand) == 2 and hand[0] == hand[1]:
            # Pocket pair
            rank = hand[0]
            if rank in "AKQ":
                return f"Premium pocket pair"
            elif rank in "JT9":
                return f"Strong pocket pair"
            elif rank in "876":
                return f"Medium pocket pair"
            else:
                return f"Low pocket pair"
        
        elif hand.endswith('s'):
            # Suited
            if hand[0] == 'A':
                return "Suited ace"
            elif self._is_connected(hand[:2]):
                return "Suited connector"
            elif self._is_one_gap(hand[:2]):
                return "Suited one-gapper"
            else:
                return "Suited"
        
        elif hand.endswith('o'):
            # Offsuit
            if hand[0] == 'A':
                return "Offsuit ace"
            elif self._is_broadway(hand[:2]):
                return "Offsuit broadway"
            else:
                return "Offsuit"
        
        return "Unknown hand type"
    
    def _assess_hand_strength(self) -> str:
        """Assess overall hand strength."""
        hand = self.current_hand
        
        # Premium hands
        if hand in ["AA", "KK", "QQ", "JJ", "AKs", "AKo"]:
            return "[green]Premium[/green]"
        
        # Strong hands
        elif hand in ["TT", "99", "AQs", "AQo", "AJs", "AJo", "KQs", "KQo"]:
            return "[yellow]Strong[/yellow]"
        
        # Marginal hands
        elif (hand.startswith('A') or hand.startswith('K') or 
              hand in ["88", "77", "66", "55"]):
            return "[blue]Marginal[/blue]"
        
        # Weak hands
        else:
            return "[red]Weak[/red]"
    
    def _assess_playability(self) -> List[str]:
        """Assess hand playability factors."""
        factors = []
        hand = self.current_hand
        
        # Pocket pairs
        if len(hand) == 2 and hand[0] == hand[1]:
            factors.append("• Set potential")
            if hand[0] in "AKQJT":
                factors.append("• Strong overpair potential")
        
        # Suited hands
        if hand.endswith('s'):
            factors.append("• Flush potential")
            if self._is_connected(hand[:2]):
                factors.append("• Straight potential")
        
        # High cards
        if hand[0] in "AKQJ" or (len(hand) > 1 and hand[1] in "AKQJ"):
            factors.append("• High card strength")
        
        # Connectivity
        if self._is_connected(hand[:2]):
            factors.append("• Connected ranks")
        
        return factors if factors else ["• Limited playability"]
    
    def _get_position_recommendations(self) -> Dict[str, str]:
        """Get position-specific recommendations."""
        hand = self.current_hand
        
        recommendations = {}
        
        # Get base recommendation based on hand strength
        if hand in ["AA", "KK", "QQ", "JJ", "AKs", "AKo"]:
            base_action = "Raise"
        elif hand in ["TT", "99", "88", "AQs", "AQo", "AJs", "KQs"]:
            base_action = "Raise/Call"
        elif hand.startswith('A') or hand.startswith('K'):
            base_action = "Call/Fold"
        else:
            base_action = "Fold"
        
        # Position adjustments
        positions = ["UTG", "MP", "CO", "BTN", "SB", "BB"]
        
        for position in positions:
            if position in ["UTG", "MP"]:
                if base_action == "Call/Fold":
                    recommendations[position] = "Fold (tight)"
                else:
                    recommendations[position] = base_action
            elif position in ["CO", "BTN"]:
                if base_action == "Fold":
                    recommendations[position] = "Consider call"
                else:
                    recommendations[position] = base_action + " (wide)"
            else:  # Blinds
                recommendations[position] = base_action + " vs range"
        
        return recommendations
    
    def _is_connected(self, ranks: str) -> bool:
        """Check if two ranks are connected."""
        rank_order = 'AKQJT98765432'
        try:
            pos1 = rank_order.index(ranks[0])
            pos2 = rank_order.index(ranks[1])
            return abs(pos1 - pos2) == 1
        except (ValueError, IndexError):
            return False
    
    def _is_one_gap(self, ranks: str) -> bool:
        """Check if two ranks have one gap between them."""
        rank_order = 'AKQJT98765432'
        try:
            pos1 = rank_order.index(ranks[0])
            pos2 = rank_order.index(ranks[1])
            return abs(pos1 - pos2) == 2
        except (ValueError, IndexError):
            return False
    
    def _is_broadway(self, ranks: str) -> bool:
        """Check if hand contains broadway cards."""
        broadway_ranks = set("AKQJT")
        return any(rank in broadway_ranks for rank in ranks)
    
    def clear_details(self) -> None:
        """Clear the current hand details."""
        self.update_hand("", None)
    
    def get_hand_summary(self) -> str:
        """Get a brief summary of the current hand."""
        if not self.current_hand:
            return "No hand selected"
        
        if self.current_action:
            return f"{self.current_hand}: {self.current_action.action.value.title()} ({self.current_action.frequency:.0%})"
        else:
            return f"{self.current_hand}: No action defined"
