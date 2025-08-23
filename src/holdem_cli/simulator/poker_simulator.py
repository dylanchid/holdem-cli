"""Poker hand simulation engine."""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from ..engine.cards import Card, Deck, HandEvaluator
from ..utils.random_utils import get_global_random
from .ai_player import AIPlayer, GameState, Action, PlayerAction


@dataclass
class PlayerState:
    """State of a player in the game."""
    name: str
    cards: List[Card]
    chips: int
    current_bet: int = 0
    has_folded: bool = False
    has_acted: bool = False


@dataclass
class BettingRound:
    """Information about a betting round."""
    street: str
    actions: List[Dict] = field(default_factory=list)
    pot_before: int = 0
    pot_after: int = 0


@dataclass
class HandResult:
    """Result of a simulated poker hand."""
    winner: str
    pot_size: int
    player_cards: List[Card]
    ai_cards: List[Card]
    board: List[Card]
    action_history: List[Dict]
    final_hands: Dict[str, str]
    reasoning: List[str]
    betting_rounds: List[BettingRound] = field(default_factory=list)
    showdown_occurred: bool = False


class PokerSimulator:
    """Simulate poker hands against AI opponents."""
    
    def __init__(self, ai_level: str = 'easy', seed: Optional[int] = None):
        """Initialize poker simulator."""
        self.ai_level = ai_level
        self.ai_player = AIPlayer(difficulty=ai_level, name="AI", seed=seed)
        self.evaluator = HandEvaluator()
        self.hand_history = []
        self._random = get_global_random()

        if seed is not None:
            self._random.seed(seed)
    
    def _deal_starting_hands(self, deck: Deck) -> Tuple[List[Card], List[Card]]:
        """Deal starting hands for player and AI."""
        player_cards = deck.deal(2)
        ai_cards = deck.deal(2)
        return player_cards, ai_cards
    
    def _deal_board(self, deck: Deck, street: str) -> List[Card]:
        """Deal board cards for specific street."""
        if street == 'flop':
            return deck.deal(3)
        elif street in ['turn', 'river']:
            return deck.deal(1)
        else:
            return []
    
    def _get_user_action(self, game_state: GameState, player_cards: List[Card], 
                        player_chips: int, current_bet: int) -> PlayerAction:
        """Get action from human player."""
        import click
        
        # Display current situation
        click.echo(f"\n--- {game_state.street.title()} ---")
        click.echo(f"Your cards: {', '.join(str(c) for c in player_cards)}")
        if game_state.board:
            click.echo(f"Board: {', '.join(str(c) for c in game_state.board)}")
        click.echo(f"Pot size: ${game_state.pot_size}")
        click.echo(f"Your chips: ${player_chips}")
        
        if current_bet > 0:
            click.echo(f"Your current bet: ${current_bet}")
        
        if game_state.bet_to_call > 0:
            call_amount = game_state.bet_to_call - current_bet
            click.echo(f"Amount to call: ${call_amount}")
        
        # Available actions
        available_actions = []
        if game_state.bet_to_call > current_bet:
            available_actions.extend(['fold', 'call'])
            if player_chips > game_state.bet_to_call - current_bet:
                available_actions.append('raise')
        else:
            available_actions.extend(['check', 'bet'])
        
        click.echo(f"Available actions: {', '.join(available_actions)}")
        
        while True:
            try:
                action_input = click.prompt("Your action", type=str).lower()
                
                if action_input == 'fold' and 'fold' in available_actions:
                    return PlayerAction(Action.FOLD, reasoning="Player folded")
                
                elif action_input == 'call' and 'call' in available_actions:
                    call_amount = game_state.bet_to_call - current_bet
                    return PlayerAction(Action.CALL, call_amount, f"Player called ${call_amount}")
                
                elif action_input == 'check' and 'check' in available_actions:
                    return PlayerAction(Action.CHECK, reasoning="Player checked")
                
                elif action_input in ['bet', 'raise'] and action_input in available_actions:
                    while True:
                        try:
                            amount = click.prompt(f"Enter {action_input} amount", type=int)
                            min_bet = max(game_state.current_bet * 2, 20) if action_input == 'raise' else 20
                            max_bet = player_chips
                            
                            if min_bet <= amount <= max_bet:
                                action_type = Action.RAISE if action_input == 'raise' else Action.BET
                                return PlayerAction(action_type, amount, f"Player {action_input} ${amount}")
                            else:
                                click.echo(f"Bet must be between ${min_bet} and ${max_bet}")
                        except (click.Abort, ValueError):
                            break
                
                else:
                    click.echo(f"Invalid action. Available: {', '.join(available_actions)}")
                    
            except click.Abort:
                click.echo("\nGame cancelled.")
                return PlayerAction(Action.FOLD, reasoning="Player cancelled")
    
    def _run_betting_round(self, street: str, players: List[PlayerState], 
                          board: List[Card], pot_size: int) -> Tuple[int, List[Dict], bool]:
        """Run a complete betting round and return (new_pot_size, actions, hand_over)."""
        import click
        
        actions = []
        current_bet = 0
        pot_contribution = 0
        hand_over = False
        
        # Reset betting state for new round
        for player in players:
            if not player.has_folded:
                player.current_bet = 0
                player.has_acted = False
        
        # Continue until all active players have acted and bets are equal
        betting_complete = False
        while not betting_complete and sum(1 for p in players if not p.has_folded) > 1:
            all_acted = True
            bets_equal = True
            
            for player in players:
                if player.has_folded:
                    continue
                    
                # Check if player needs to act
                if not player.has_acted or player.current_bet < current_bet:
                    all_acted = False
                    
                    game_state = GameState(
                        pot_size=pot_size + pot_contribution,
                        bet_to_call=current_bet,
                        current_bet=current_bet,
                        position='button' if player.name == 'Human' else 'early',
                        street=street,
                        board=board,
                        num_players=2,
                        num_active_players=sum(1 for p in players if not p.has_folded)
                    )
                    
                    if player.name == 'Human':
                        action = self._get_user_action(game_state, player.cards, 
                                                     player.chips, player.current_bet)
                    else:
                        action = self.ai_player.decide_action(player.cards, game_state)
                    
                    # Process action
                    if action.action == Action.FOLD:
                        player.has_folded = True
                        actions.append({
                            "player": player.name,
                            "action": "fold",
                            "amount": 0,
                            "reasoning": action.reasoning
                        })
                        if sum(1 for p in players if not p.has_folded) <= 1:
                            hand_over = True
                            break
                    
                    elif action.action == Action.CALL:
                        call_amount = current_bet - player.current_bet
                        actual_call = min(call_amount, player.chips)
                        player.current_bet += actual_call
                        player.chips -= actual_call
                        pot_contribution += actual_call
                        player.has_acted = True
                        
                        actions.append({
                            "player": player.name,
                            "action": "call",
                            "amount": actual_call,
                            "reasoning": action.reasoning
                        })
                        
                        if player.name == 'Human':
                            click.echo(f"You called ${actual_call}")
                        else:
                            click.echo(f"AI called ${actual_call}")
                    
                    elif action.action == Action.CHECK:
                        player.has_acted = True
                        actions.append({
                            "player": player.name,
                            "action": "check",
                            "amount": 0,
                            "reasoning": action.reasoning
                        })
                        
                        if player.name == 'Human':
                            click.echo("You checked")
                        else:
                            click.echo("AI checked")
                    
                    elif action.action in [Action.BET, Action.RAISE]:
                        bet_amount = min(action.amount, player.chips)
                        additional_bet = bet_amount - player.current_bet
                        player.current_bet = bet_amount
                        player.chips -= additional_bet
                        pot_contribution += additional_bet
                        current_bet = bet_amount
                        player.has_acted = True
                        
                        # Reset other players' acted status since there's a new bet
                        for other_player in players:
                            if other_player != player and not other_player.has_folded:
                                other_player.has_acted = False
                        
                        action_name = "bet" if action.action == Action.BET else "raise"
                        actions.append({
                            "player": player.name,
                            "action": action_name,
                            "amount": bet_amount,
                            "reasoning": action.reasoning
                        })
                        
                        if player.name == 'Human':
                            click.echo(f"You {action_name} ${bet_amount}")
                        else:
                            click.echo(f"AI {action_name} ${bet_amount}")
                    
                    if hand_over:
                        break
            
            # Check if betting is complete
            if all_acted and all(p.current_bet == current_bet or p.has_folded for p in players):
                betting_complete = True
        
        return pot_size + pot_contribution, actions, hand_over
    
    def _determine_winner(self, players: List[PlayerState], board: List[Card]) -> Tuple[str, Dict[str, str]]:
        """Determine winner and hand descriptions."""
        active_players = [p for p in players if not p.has_folded]
        
        if len(active_players) == 1:
            # One player remaining
            winner = active_players[0].name or "Unknown"
            hands = {}
            for player in players:
                if player.has_folded:
                    hands[player.name or "Unknown"] = "Folded"
                else:
                    hands[player.name or "Unknown"] = "Winner by fold"
            return winner, hands
        
        # Showdown
        best_hand = None
        winner = None
        hands = {}
        
        for player in active_players:
            hand_strength = self.evaluator.evaluate_hand(player.cards + board)
            hands[player.name or "Unknown"] = f"{hand_strength.description} ({', '.join(str(c) for c in hand_strength.cards)})"

            if best_hand is None or hand_strength > best_hand:
                best_hand = hand_strength
                winner = player.name or "Unknown"

        return winner or "Unknown", hands
    
    def simulate_hand(self, player_cards: Optional[List[Card]] = None, 
                     starting_chips: int = 1000) -> HandResult:
        """Simulate a complete poker hand with full betting rounds."""
        import click
        
        # Initialize deck and deal cards
        deck = Deck()
        deck.shuffle()
        
        if player_cards is None:
            human_cards, ai_cards = self._deal_starting_hands(deck)
        else:
            # Remove player cards from deck
            for card in player_cards:
                deck.cards.remove(card)
            deck.shuffle()
            human_cards = player_cards
            ai_cards = deck.deal(2)
        
        # Initialize players
        players = [
            PlayerState("Human", human_cards, starting_chips),
            PlayerState("AI", ai_cards, starting_chips)
        ]
        
        # Game state
        pot_size = 30  # Blinds: small blind (10) + big blind (20)
        players[0].chips -= 10  # Human posts small blind
        players[1].chips -= 20  # AI posts big blind
        players[0].current_bet = 10
        players[1].current_bet = 20
        
        action_history = []
        reasoning = []
        betting_rounds = []
        board = []
        
        click.echo(f"\n🎰 Starting new hand against {self.ai_level} AI")
        click.echo(f"💰 Starting pot: ${pot_size} (blinds posted)")
        click.echo(f"Your cards: {', '.join(str(c) for c in human_cards)}")
        
        # Preflop betting round
        click.echo(f"\n=== PREFLOP ===")
        pot_size, preflop_actions, hand_over = self._run_betting_round(
            'preflop', players, board, pot_size
        )
        betting_rounds.append(BettingRound('preflop', preflop_actions, 30, pot_size))
        action_history.extend(preflop_actions)
        
        if hand_over:
            winner, final_hands = self._determine_winner(players, board)
            return HandResult(
                winner=winner,
                pot_size=pot_size,
                player_cards=human_cards,
                ai_cards=ai_cards,
                board=board,
                action_history=action_history,
                final_hands=final_hands,
                reasoning=reasoning,
                betting_rounds=betting_rounds,
                showdown_occurred=False
            )
        
        # Flop
        board.extend(self._deal_board(deck, 'flop'))
        click.echo(f"\n=== FLOP ===")
        click.echo(f"🃏 Board: {', '.join(str(c) for c in board)}")
        
        pot_before_flop = pot_size
        pot_size, flop_actions, hand_over = self._run_betting_round(
            'flop', players, board, pot_size
        )
        betting_rounds.append(BettingRound('flop', flop_actions, pot_before_flop, pot_size))
        action_history.extend(flop_actions)
        
        if hand_over:
            winner, final_hands = self._determine_winner(players, board)
            return HandResult(
                winner=winner,
                pot_size=pot_size,
                player_cards=human_cards,
                ai_cards=ai_cards,
                board=board,
                action_history=action_history,
                final_hands=final_hands,
                reasoning=reasoning,
                betting_rounds=betting_rounds,
                showdown_occurred=False
            )
        
        # Turn
        board.extend(self._deal_board(deck, 'turn'))
        click.echo(f"\n=== TURN ===")
        click.echo(f"🃏 Board: {', '.join(str(c) for c in board)}")
        
        pot_before_turn = pot_size
        pot_size, turn_actions, hand_over = self._run_betting_round(
            'turn', players, board, pot_size
        )
        betting_rounds.append(BettingRound('turn', turn_actions, pot_before_turn, pot_size))
        action_history.extend(turn_actions)
        
        if hand_over:
            winner, final_hands = self._determine_winner(players, board)
            return HandResult(
                winner=winner,
                pot_size=pot_size,
                player_cards=human_cards,
                ai_cards=ai_cards,
                board=board,
                action_history=action_history,
                final_hands=final_hands,
                reasoning=reasoning,
                betting_rounds=betting_rounds,
                showdown_occurred=False
            )
        
        # River
        board.extend(self._deal_board(deck, 'river'))
        click.echo(f"\n=== RIVER ===")
        click.echo(f"🃏 Board: {', '.join(str(c) for c in board)}")
        
        pot_before_river = pot_size
        pot_size, river_actions, hand_over = self._run_betting_round(
            'river', players, board, pot_size
        )
        betting_rounds.append(BettingRound('river', river_actions, pot_before_river, pot_size))
        action_history.extend(river_actions)
        
        # Showdown (unless someone folded)
        winner, final_hands = self._determine_winner(players, board)
        showdown_occurred = not hand_over
        
        if showdown_occurred:
            click.echo(f"\n=== SHOWDOWN ===")
            for player in players:
                if not player.has_folded:
                    click.echo(f"{player.name}: {final_hands[player.name]}")
        
        click.echo(f"\n🏆 Winner: {winner}")
        click.echo(f"💰 Pot size: ${pot_size}")
        
        result = HandResult(
            winner=winner,
            pot_size=pot_size,
            player_cards=human_cards,
            ai_cards=ai_cards,
            board=board,
            action_history=action_history,
            final_hands=final_hands,
            reasoning=reasoning,
            betting_rounds=betting_rounds,
            showdown_occurred=showdown_occurred
        )
        
        self.hand_history.append(result)
        return result
    
    def export_hand_history(self, filename: str, format: str = 'json') -> None:
        """Export hand history to file with enhanced formatting options."""
        import json
        from datetime import datetime
        from pathlib import Path

        if format.lower() == 'txt':
            self._export_hand_history_txt(filename)
        elif format.lower() == 'json':
            self._export_hand_history_json(filename)
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'txt' or 'json'")

    def _export_hand_history_json(self, filename: str) -> None:
        """Export hand history to enhanced JSON format."""
        import json
        from datetime import datetime

        export_data = {
            "export_info": {
                "export_date": datetime.now().isoformat(),
                "ai_level": self.ai_level,
                "export_format": "holdem-cli-v2",
                "version": "1.0"
            },
            "session_summary": {
                "total_hands": len(self.hand_history),
                "player_wins": sum(1 for h in self.hand_history if h.winner == "Human"),
                "ai_wins": sum(1 for h in self.hand_history if h.winner == "AI"),
                "ties": sum(1 for h in self.hand_history if h.winner == "Tie"),
                "showdowns": sum(1 for h in self.hand_history if h.showdown_occurred),
                "average_pot_size": sum(h.pot_size for h in self.hand_history) / len(self.hand_history) if self.hand_history else 0
            },
            "hands": []
        }

        for i, hand in enumerate(self.hand_history):
            hand_data = {
                "hand_number": i + 1,
                "timestamp": datetime.now().isoformat(),
                "winner": hand.winner,
                "pot_size": hand.pot_size,
                "starting_chips": 1000,  # Default starting chips
                "final_chips": {
                    "human": 1000 + (hand.pot_size if hand.winner == "Human" else -hand.pot_size if hand.winner == "AI" else 0),
                    "ai": 1000 + (hand.pot_size if hand.winner == "AI" else -hand.pot_size if hand.winner == "Human" else 0)
                },
                "cards": {
                    "player": [str(c) for c in hand.player_cards],
                    "ai": [str(c) for c in hand.ai_cards],
                    "board": [str(c) for c in hand.board]
                },
                "showdown_occurred": hand.showdown_occurred,
                "betting_rounds": [
                    {
                        "street": br.street,
                        "pot_before": br.pot_before,
                        "pot_after": br.pot_after,
                        "actions": br.actions
                    }
                    for br in hand.betting_rounds
                ],
                "action_history": hand.action_history,
                "final_hands": hand.final_hands,
                "reasoning": hand.reasoning
            }
            export_data["hands"].append(hand_data)

        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)

        print(f"Exported {len(self.hand_history)} hands to {filename} (JSON format)")

    def _export_hand_history_txt(self, filename: str) -> None:
        """Export hand history to human-readable text format."""
        from datetime import datetime

        with open(filename, 'w') as f:
            # Write header
            f.write("Poker Hand History Export\n")
            f.write("=" * 50 + "\n")
            f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"AI Level: {self.ai_level}\n")
            f.write(f"Total Hands: {len(self.hand_history)}\n")
            f.write(f"Format: holdem-cli-v2\n\n")

            # Write session summary
            if self.hand_history:
                player_wins = sum(1 for h in self.hand_history if h.winner == "Human")
                ai_wins = sum(1 for h in self.hand_history if h.winner == "AI")
                ties = sum(1 for h in self.hand_history if h.winner == "Tie")
                showdowns = sum(1 for h in self.hand_history if h.showdown_occurred)
                avg_pot = sum(h.pot_size for h in self.hand_history) / len(self.hand_history)

                f.write("Session Summary:\n")
                f.write(f"  Player Wins: {player_wins}\n")
                f.write(f"  AI Wins: {ai_wins}\n")
                f.write(f"  Ties: {ties}\n")
                f.write(f"  Showdowns: {showdowns}\n")
                f.write(f"  Average Pot Size: ${avg_pot:.2f}\n")
                f.write(f"  Win Rate: {player_wins/len(self.hand_history)*100:.1f}%\n\n")

            # Write individual hands
            for i, hand in enumerate(self.hand_history, 1):
                f.write(f"Hand #{i}\n")
                f.write("-" * 30 + "\n")
                f.write(f"Winner: {hand.winner}\n")
                f.write(f"Final Pot: ${hand.pot_size}\n")
                f.write(f"Showdown: {'Yes' if hand.showdown_occurred else 'No'}\n\n")

                # Cards
                f.write("Cards:\n")
                f.write(f"  Player: {', '.join(str(c) for c in hand.player_cards)}\n")
                f.write(f"  AI: {', '.join(str(c) for c in hand.ai_cards)}\n")
                if hand.board:
                    f.write(f"  Board: {', '.join(str(c) for c in hand.board)}\n")
                f.write("\n")

                # Final hands
                if hand.final_hands:
                    f.write("Final Hands:\n")
                    for player, hand_desc in hand.final_hands.items():
                        f.write(f"  {player}: {hand_desc}\n")
                    f.write("\n")

                # Betting rounds
                f.write("Betting Action:\n")
                for br in hand.betting_rounds:
                    f.write(f"  {br.street.title()} (Pot: ${br.pot_before} -> ${br.pot_after}):\n")
                    for action in br.actions:
                        f.write(f"    {action['player']}: {action['action']}")
                        if action['amount'] > 0:
                            f.write(f" ${action['amount']}")
                        if action['reasoning']:
                            f.write(f" ({action['reasoning']})")
                        f.write("\n")
                    f.write("\n")

                # Action history summary
                if hand.action_history:
                    f.write("Action Summary:\n")
                    actions_by_player = {"Human": [], "AI": []}
                    for action in hand.action_history:
                        actions_by_player[action['player']].append(f"{action['action']}")
                        if action['amount'] > 0:
                            actions_by_player[action['player'][-1]] = actions_by_player[action['player'][:-1]] + [f"{action['action']} ${action['amount']}"]

                    for player, actions in actions_by_player.items():
                        if actions:
                            f.write(f"  {player}: {', '.join(actions)}\n")
                    f.write("\n")

                f.write("=" * 50 + "\n\n")

        print(f"Exported {len(self.hand_history)} hands to {filename} (Text format)")
    
    def get_session_statistics(self) -> Dict:
        """Get statistics for the current session."""
        if not self.hand_history:
            return {"total_hands": 0}
        
        total_hands = len(self.hand_history)
        player_wins = sum(1 for h in self.hand_history if h.winner == "Human")
        ai_wins = sum(1 for h in self.hand_history if h.winner == "AI")
        ties = sum(1 for h in self.hand_history if h.winner == "Tie")
        
        showdowns = sum(1 for h in self.hand_history if h.showdown_occurred)
        
        # Calculate average pot sizes by street
        total_pots = sum(h.pot_size for h in self.hand_history)
        avg_pot = total_pots / total_hands if total_hands > 0 else 0
        
        return {
            "total_hands": total_hands,
            "player_wins": player_wins,
            "ai_wins": ai_wins,
            "ties": ties,
            "win_rate": (player_wins / total_hands * 100) if total_hands > 0 else 0,
            "showdown_rate": (showdowns / total_hands * 100) if total_hands > 0 else 0,
            "average_pot_size": avg_pot
        }
