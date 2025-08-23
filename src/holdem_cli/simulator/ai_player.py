"""AI player implementation for poker simulation."""

import random
from typing import List, Dict, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

from ..engine.cards import Card, HandEvaluator, HandStrength
from ..engine.equity import EquityCalculator
from ..utils.random_utils import get_global_random


class Action(Enum):
    """Possible poker actions."""
    FOLD = "fold"
    CALL = "call"
    RAISE = "raise"
    CHECK = "check"
    BET = "bet"


@dataclass
class GameState:
    """Current state of the poker game."""
    pot_size: int
    bet_to_call: int
    current_bet: int
    position: str  # 'early', 'middle', 'late', 'button'
    street: str   # 'preflop', 'flop', 'turn', 'river'
    board: List[Card]
    num_players: int
    num_active_players: int


@dataclass
class PlayerAction:
    """An action taken by a player."""
    action: Action
    amount: int = 0  # For bets/raises
    reasoning: str = ""


class AIPlayer:
    """AI player with different difficulty levels."""
    
    def __init__(self, difficulty: str = 'easy', name: str = "AI", seed: Optional[int] = None):
        """Initialize AI player with difficulty level."""
        self.difficulty = difficulty
        self.name = name
        self.evaluator = HandEvaluator()
        self.equity_calculator = EquityCalculator(seed=seed)
        self._random = get_global_random()

        if seed is not None:
            self._random.seed(seed)

        # AI personality parameters based on difficulty
        self._set_personality()
    
    def _set_personality(self):
        """Set AI behavior parameters based on difficulty."""
        if self.difficulty == 'easy':
            self.aggression = 0.3      # Low aggression
            self.bluff_frequency = 0.05 # Rarely bluffs
            self.fold_threshold = 0.35  # Folds often
            self.bet_sizing = 0.5       # Small bets
            self.calculation_accuracy = 0.7  # Sometimes makes mistakes
        elif self.difficulty == 'medium':
            self.aggression = 0.5
            self.bluff_frequency = 0.15
            self.fold_threshold = 0.25
            self.bet_sizing = 0.75
            self.calculation_accuracy = 0.85
        else:  # hard
            self.aggression = 0.7
            self.bluff_frequency = 0.25
            self.fold_threshold = 0.15
            self.bet_sizing = 1.0
            self.calculation_accuracy = 0.95
    
    def _evaluate_hand_strength(self, hole_cards: List[Card], board: List[Card]) -> float:
        """Evaluate hand strength on a scale of 0-1."""
        if len(board) == 0:
            # Preflop hand strength estimation
            return self._preflop_hand_strength(hole_cards)
        
        # Post-flop evaluation
        all_cards = hole_cards + board
        if len(all_cards) >= 5:
            hand_strength = self.evaluator.evaluate_hand(all_cards)
            # Convert to 0-1 scale (rough approximation)
            strength_values = {
                'High Card': 0.1,
                'Pair': 0.2,
                'Two Pair': 0.35,
                'Three of a Kind': 0.5,
                'Straight': 0.65,
                'Flush': 0.75,
                'Full House': 0.85,
                'Four of a Kind': 0.95,
                'Straight Flush': 1.0,
                'Royal Flush': 1.0
            }
            return strength_values.get(hand_strength.description.split(' ')[0], 0.1)
        
        return 0.3  # Default for incomplete boards
    
    def _preflop_hand_strength(self, hole_cards: List[Card]) -> float:
        """Evaluate preflop hand strength."""
        if len(hole_cards) != 2:
            return 0.1
        
        card1, card2 = hole_cards
        
        # Pocket pairs
        if card1.rank == card2.rank:
            pair_strength = {
                14: 1.0,   # AA
                13: 0.95,  # KK
                12: 0.9,   # QQ
                11: 0.85,  # JJ
                10: 0.8,   # TT
                9: 0.7,    # 99
                8: 0.6,    # 88
                7: 0.5,    # 77
                6: 0.4,    # 66
                5: 0.3,    # 55
                4: 0.25,   # 44
                3: 0.2,    # 33
                2: 0.15    # 22
            }
            return pair_strength.get(card1.rank.numeric_value, 0.15)
        
        # Suited/unsuited hands
        suited = card1.suit == card2.suit
        high_card = max(card1.rank.numeric_value, card2.rank.numeric_value)
        low_card = min(card1.rank.numeric_value, card2.rank.numeric_value)
        gap = high_card - low_card
        
        # Base strength for high cards
        base_strength = (high_card + low_card) / 28.0  # Normalized
        
        # Bonuses
        if suited:
            base_strength += 0.1
        if gap <= 1:  # Connected
            base_strength += 0.05
        if high_card >= 12:  # Face cards
            base_strength += 0.1
        
        return min(base_strength, 0.85)  # Cap at 0.85 for non-pairs
    
    def _calculate_pot_odds(self, game_state: GameState) -> float:
        """Calculate pot odds for calling."""
        if game_state.bet_to_call == 0:
            return 0.0
        return game_state.bet_to_call / (game_state.pot_size + game_state.bet_to_call)
    
    def _should_bluff(self, game_state: GameState) -> bool:
        """Determine if AI should attempt a bluff."""
        # Bluff more on later streets and in good position
        bluff_chance = self.bluff_frequency
        
        if game_state.street in ['turn', 'river']:
            bluff_chance *= 1.5
        if game_state.position in ['button', 'late']:
            bluff_chance *= 1.3
        if game_state.num_active_players <= 2:
            bluff_chance *= 1.2
        
        return random.random() < bluff_chance
    
    def _calculate_bet_size(self, game_state: GameState, hand_strength: float) -> int:
        """Calculate appropriate bet size."""
        pot_size = game_state.pot_size
        
        # Base bet as fraction of pot
        base_bet = int(pot_size * self.bet_sizing)
        
        # Adjust based on hand strength
        if hand_strength > 0.8:
            # Strong hand - bet bigger
            bet_size = int(base_bet * 1.5)
        elif hand_strength > 0.6:
            # Good hand - standard bet
            bet_size = base_bet
        else:
            # Marginal hand - smaller bet or bluff
            bet_size = int(base_bet * 0.7)
        
        # Ensure minimum bet
        return max(bet_size, game_state.current_bet + 10)
    
    def decide_action(self, hole_cards: List[Card], game_state: GameState) -> PlayerAction:
        """Decide what action to take given the current game state."""
        hand_strength = self._evaluate_hand_strength(hole_cards, game_state.board)
        
        # Add some randomness to simulate calculation errors
        if random.random() > self.calculation_accuracy:
            hand_strength += random.uniform(-0.2, 0.2)
            hand_strength = max(0.0, min(1.0, hand_strength))
        
        pot_odds = self._calculate_pot_odds(game_state)
        
        # Decision logic
        if game_state.bet_to_call == 0:
            # No bet to call - decide between check and bet
            if hand_strength > (0.6 - self.aggression * 0.3):
                # Strong enough to bet
                bet_size = self._calculate_bet_size(game_state, hand_strength)
                return PlayerAction(
                    action=Action.BET,
                    amount=bet_size,
                    reasoning=f"Betting {bet_size} with hand strength {hand_strength:.2f}"
                )
            elif self._should_bluff(game_state):
                # Bluff attempt
                bet_size = self._calculate_bet_size(game_state, 0.3)
                return PlayerAction(
                    action=Action.BET,
                    amount=bet_size,
                    reasoning=f"Bluffing with bet of {bet_size}"
                )
            else:
                # Check
                return PlayerAction(
                    action=Action.CHECK,
                    reasoning=f"Checking with hand strength {hand_strength:.2f}"
                )
        
        else:
            # There's a bet to call
            call_threshold = self.fold_threshold + (self.aggression * 0.2)
            
            if hand_strength < call_threshold and pot_odds > 0.3:
                # Weak hand, fold
                return PlayerAction(
                    action=Action.FOLD,
                    reasoning=f"Folding weak hand (strength: {hand_strength:.2f}, threshold: {call_threshold:.2f})"
                )
            elif hand_strength > (0.7 + self.aggression * 0.1):
                # Strong hand, consider raising
                if random.random() < self.aggression:
                    raise_size = self._calculate_bet_size(game_state, hand_strength)
                    return PlayerAction(
                        action=Action.RAISE,
                        amount=raise_size,
                        reasoning=f"Raising to {raise_size} with strong hand (strength: {hand_strength:.2f})"
                    )
                else:
                    return PlayerAction(
                        action=Action.CALL,
                        reasoning=f"Calling with strong hand (strength: {hand_strength:.2f})"
                    )
            elif self._should_bluff(game_state) and game_state.num_active_players <= 2:
                # Bluff raise
                raise_size = self._calculate_bet_size(game_state, 0.4)
                return PlayerAction(
                    action=Action.RAISE,
                    amount=raise_size,
                    reasoning=f"Bluff raising to {raise_size}"
                )
            else:
                # Call
                return PlayerAction(
                    action=Action.CALL,
                    reasoning=f"Calling with hand strength {hand_strength:.2f}"
                )
