# src/holdem_cli/cli/equity_commands.py
"""Equity calculation CLI commands."""

import click
import json
import sys
from typing import Optional

from holdem_cli.engine.equity import EquityCalculator, parse_hand_string


@click.command()
@click.argument('hand1')
@click.argument('hand2')
@click.option('--board', help='Board cards (e.g., 2c7s)')
@click.option('--iterations', default=25000, help='Monte Carlo iterations')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.option('--seed', type=int, help='Random seed for deterministic results')
def equity(hand1: str, hand2: str, board: Optional[str], iterations: int,
          output_json: bool, seed: Optional[int]) -> None:
    """Calculate equity between two hands.

    Examples:
      holdem equity AsKs 7h7d
      holdem equity AsKs 7h7d --board 2c7s
      holdem equity AsKs 7h7d --iterations 50000 --json
    """
    try:
        # Parse hands
        hand1_cards = parse_hand_string(hand1)
        hand2_cards = parse_hand_string(hand2)

        if len(hand1_cards) != 2 or len(hand2_cards) != 2:
            click.echo("Error: Each hand must have exactly 2 cards")
            sys.exit(1)

        # Parse board if provided
        board_cards = []
        if board:
            board_cards = parse_hand_string(board)

        # Calculate equity
        calculator = EquityCalculator(seed=seed)
        result = calculator.calculate_equity(
            hand1_cards, hand2_cards, board_cards, iterations
        )

        if output_json:
            # JSON output for programmatic use
            output = {
                "hand1": hand1,
                "hand2": hand2,
                "board": board or "",
                "equity": result.to_dict()
            }
            click.echo(json.dumps(output, indent=2))
        else:
            # Human-readable output
            click.echo("\nEquity calculation:")
            click.echo(f"Hand 1: {hand1}")
            click.echo(f"Hand 2: {hand2}")
            if board:
                click.echo(f"Board:  {board}")
            click.echo(f"Iterations: {iterations:,}")
            click.echo()
            click.echo(f"Hand 1 equity: {result.hand1_win:.1f}% win, "
                      f"{result.hand1_tie:.1f}% tie, {result.hand1_lose:.1f}% lose")
            click.echo(f"Hand 2 equity: {result.hand2_win:.1f}% win, "
                      f"{result.hand2_tie:.1f}% tie, {result.hand2_lose:.1f}% lose")

    except ValueError as e:
        click.echo(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}")
        sys.exit(1)
