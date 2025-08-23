"""Monte Carlo equity calculator for poker hands."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass
from itertools import combinations

from .cards import Card, Deck, HandEvaluator, HandStrength
from ..utils.random_utils import get_global_random, set_global_seed


@dataclass
class EquityResult:
    """Results from an equity calculation."""
    hand1_win: float
    hand1_tie: float
    hand1_lose: float
    hand2_win: float
    hand2_tie: float
    hand2_lose: float
    iterations: int
    
    def to_dict(self) -> Dict[str, Union[Dict[str, float], int]]:
        """Convert to dictionary for JSON serialization."""
        return {
            "hand1": {
                "win": self.hand1_win,
                "tie": self.hand1_tie,
                "lose": self.hand1_lose
            },
            "hand2": {
                "win": self.hand2_win,
                "tie": self.hand2_tie,
                "lose": self.hand2_lose
            },
            "iterations": self.iterations
        }


class EquityCalculator:
    """Calculate poker hand equity using Monte Carlo simulation."""

    def __init__(self, seed: Optional[int] = None) -> None:
        """Initialize with optional deterministic seeding for tests."""
        self._random = get_global_random()
        if seed is not None:
            self._random.seed(seed)
        self._seed = seed
    
    def calculate_equity(
        self, 
        hand1: List[Card], 
        hand2: List[Card],
        board: Optional[List[Card]] = None,
        iterations: int = 25000
    ) -> EquityResult:
        """
        Calculate equity between two hands with optional board cards.
        
        Args:
            hand1: First player's hole cards
            hand2: Second player's hole cards  
            board: Community cards (0-5 cards)
            iterations: Number of Monte Carlo simulations
            
        Returns:
            EquityResult with win/tie/lose percentages
        """
        if len(hand1) != 2 or len(hand2) != 2:
            raise ValueError("Each hand must have exactly 2 cards")
        
        if board is None:
            board = []
        
        if len(board) > 5:
            raise ValueError("Board cannot have more than 5 cards")
        
        # Check for duplicate cards
        all_cards = hand1 + hand2 + board
        if len(all_cards) != len(set(all_cards)):
            raise ValueError("Duplicate cards detected")
        
        hand1_wins = 0
        hand2_wins = 0
        ties = 0
        
        for _ in range(iterations):
            # Create deck without known cards
            deck = Deck(seed=self._seed)
            deck.cards = [c for c in deck.cards if c not in all_cards]
            deck.shuffle()
            
            # Complete the board to 5 cards
            sim_board = board.copy()
            cards_needed = 5 - len(sim_board)
            if cards_needed > 0:
                sim_board.extend(deck.deal(cards_needed))
            
            # Evaluate both hands
            hand1_strength = HandEvaluator.evaluate_hand(hand1 + sim_board)
            hand2_strength = HandEvaluator.evaluate_hand(hand2 + sim_board)
            
            # Compare results
            if hand1_strength > hand2_strength:
                hand1_wins += 1
            elif hand2_strength > hand1_strength:
                hand2_wins += 1
            else:
                ties += 1
        
        # Calculate percentages
        total = iterations
        hand1_win_pct = (hand1_wins / total) * 100
        hand1_tie_pct = (ties / total) * 100
        hand1_lose_pct = (hand2_wins / total) * 100
        
        return EquityResult(
            hand1_win=hand1_win_pct,
            hand1_tie=hand1_tie_pct,
            hand1_lose=hand1_lose_pct,
            hand2_win=hand1_lose_pct,  # hand2_win = hand1_lose
            hand2_tie=hand1_tie_pct,
            hand2_lose=hand1_win_pct,  # hand2_lose = hand1_win
            iterations=iterations
        )

    async def calculate_equity_async(
        self,
        hand1: List[Card],
        hand2: List[Card],
        board: Optional[List[Card]] = None,
        iterations: int = 25000
    ) -> EquityResult:
        """
        Calculate equity between two hands asynchronously.

        This method runs the equity calculation in a thread pool to avoid
        blocking the main event loop, making it suitable for UI applications.

        Args:
            hand1: First player's hole cards
            hand2: Second player's hole cards
            board: Community cards (0-5 cards)
            iterations: Number of Monte Carlo simulations

        Returns:
            EquityResult with win/tie/lose percentages
        """
        loop = asyncio.get_event_loop()

        # Run the synchronous calculation in a thread pool
        with ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(
                executor,
                self.calculate_equity,
                hand1, hand2, board, iterations
            )

        return result

    def calculate_equity_batch(
        self,
        hand_pairs: List[Tuple[List[Card], List[Card]]],
        board: Optional[List[Card]] = None,
        iterations: int = 10000
    ) -> List[EquityResult]:
        """
        Calculate equity for multiple hand pairs efficiently.

        This method batches multiple equity calculations and can be used
        to pre-compute equities for common hand matchups.

        Args:
            hand_pairs: List of tuples containing (hand1, hand2) pairs
            board: Community cards (0-5 cards)
            iterations: Number of Monte Carlo simulations per pair

        Returns:
            List of EquityResult objects corresponding to input pairs
        """
        results = []
        for hand1, hand2 in hand_pairs:
            try:
                result = self.calculate_equity(hand1, hand2, board, iterations)
                results.append(result)
            except Exception as e:
                # Return a default result for failed calculations
                results.append(EquityResult(
                    hand1_win=0, hand1_tie=0, hand1_lose=0,
                    hand2_win=0, hand2_tie=0, hand2_lose=0,
                    iterations=0
                ))
        return results

    async def calculate_equity_batch_async(
        self,
        hand_pairs: List[Tuple[List[Card], List[Card]]],
        board: Optional[List[Card]] = None,
        iterations: int = 10000
    ) -> List[EquityResult]:
        """
        Calculate equity for multiple hand pairs asynchronously.

        Args:
            hand_pairs: List of tuples containing (hand1, hand2) pairs
            board: Community cards (0-5 cards)
            iterations: Number of Monte Carlo simulations per pair

        Returns:
            List of EquityResult objects corresponding to input pairs
        """
        loop = asyncio.get_event_loop()

        # Run batch calculation in thread pool
        with ThreadPoolExecutor() as executor:
            results = await loop.run_in_executor(
                executor,
                self.calculate_equity_batch,
                hand_pairs, board, iterations
            )

        return results
    
    def calculate_range_equity(
        self,
        hand: List[Card],
        opponent_range: List[List[Card]],
        board: Optional[List[Card]] = None,
        iterations: int = 10000
    ) -> EquityResult:
        """
        Calculate equity of a specific hand against a range of hands.
        
        Args:
            hand: Specific 2-card hand
            opponent_range: List of 2-card hands representing opponent's range
            board: Community cards
            iterations: Iterations per opponent hand
            
        Returns:
            EquityResult averaged across the range
        """
        if len(hand) != 2:
            raise ValueError("Hand must have exactly 2 cards")
        
        if board is None:
            board = []
        
        total_hand_wins = 0
        total_hand_ties = 0
        total_hand_loses = 0
        total_iterations = 0
        
        for opponent_hand in opponent_range:
            if len(opponent_hand) != 2:
                continue
                
            # Skip if hands share cards
            if any(card in hand + board for card in opponent_hand):
                continue
            
            # Calculate equity against this specific hand
            equity = self.calculate_equity(
                hand, opponent_hand, board, iterations
            )
            
            total_hand_wins += equity.hand1_win * iterations
            total_hand_ties += equity.hand1_tie * iterations
            total_hand_loses += equity.hand1_lose * iterations
            total_iterations += iterations
        
        if total_iterations == 0:
            raise ValueError("No valid opponent hands in range")
        
        # Average the results
        avg_hand_win = (total_hand_wins / total_iterations)
        avg_hand_tie = (total_hand_ties / total_iterations)
        avg_hand_lose = (total_hand_loses / total_iterations)
        
        return EquityResult(
            hand1_win=avg_hand_win,
            hand1_tie=avg_hand_tie,
            hand1_lose=avg_hand_lose,
            hand2_win=avg_hand_lose,
            hand2_tie=avg_hand_tie,
            hand2_lose=avg_hand_win,
            iterations=total_iterations
        )


def parse_hand_string(hand_str: str) -> List[Card]:
    """Parse hand string like 'AsKs' or 'As Ks' into Card objects."""
    # Remove spaces and split into 2-character card strings
    clean_str = hand_str.replace(" ", "")
    if len(clean_str) % 2 != 0:
        raise ValueError(f"Invalid hand string: {hand_str}")
    
    cards = []
    for i in range(0, len(clean_str), 2):
        card_str = clean_str[i:i+2]
        cards.append(Card.from_string(card_str))
    
    return cards


def parse_range_string(range_str: str) -> List[List[Card]]:
    """
    Parse range strings like 'AA,KK,QQ' or 'JJ+' into list of hand combinations.
    
    For MVP, supports:
    - Specific pairs: AA, KK, etc.
    - Pair ranges: JJ+ (JJ, QQ, KK, AA)
    - Specific hands: AKs, AKo
    
    Future: Add more complex range notation
    """
    from .cards import Rank, Suit
    
    hands = []
    range_parts = [part.strip() for part in range_str.split(',')]
    
    for part in range_parts:
        if part.endswith('+'):
            # Range notation like JJ+
            base_rank_str = part[0]
            if part[1] == base_rank_str:  # Pair range
                base_rank = None
                for rank in Rank:
                    if rank.symbol == base_rank_str:
                        base_rank = rank
                        break
                
                if base_rank is None:
                    continue
                
                # Add all pairs from base_rank to Ace
                for rank in Rank:
                    if rank.numeric_value >= base_rank.numeric_value:
                        # Generate all suit combinations for this pair
                        for suit1, suit2 in combinations(Suit, 2):
                            hands.append([
                                Card(rank, suit1),
                                Card(rank, suit2)
                            ])
        else:
            # Specific hand notation
            if len(part) == 2 and part[0] == part[1]:
                # Pair like AA
                rank_str = part[0]
                rank = None
                for r in Rank:
                    if r.symbol == rank_str:
                        rank = r
                        break
                
                if rank is not None:
                    # Generate all suit combinations for this pair
                    for suit1, suit2 in combinations(Suit, 2):
                        hands.append([
                            Card(rank, suit1),
                            Card(rank, suit2)
                        ])
            elif len(part) == 3:
                # AKs or AKo notation
                rank1_str, rank2_str, suited = part[0], part[1], part[2]
                
                rank1 = rank2 = None
                for rank in Rank:
                    if rank.symbol == rank1_str:
                        rank1 = rank
                    if rank.symbol == rank2_str:
                        rank2 = rank
                
                if rank1 is not None and rank2 is not None:
                    if suited.lower() == 's':
                        # Suited - same suit
                        for suit in Suit:
                            hands.append([
                                Card(rank1, suit),
                                Card(rank2, suit)
                            ])
                    elif suited.lower() == 'o':
                        # Offsuit - different suits
                        for suit1 in Suit:
                            for suit2 in Suit:
                                if suit1 != suit2:
                                    hands.append([
                                        Card(rank1, suit1),
                                        Card(rank2, suit2)
                                    ])
    
    return hands
