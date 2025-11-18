# src/holdem_cli/cli/simulate_commands.py
"""Simulation CLI commands."""

import click
from typing import Optional

from holdem_cli.storage import init_database


@click.command()
@click.option('--ai', default='easy',
              type=click.Choice(['easy', 'medium', 'hard']),
              help='AI difficulty level')
@click.option('--profile', default='default', help='Profile to use')
@click.option('--export-hand', help='Export hand history to file')
@click.option('--export-format', default='json',
              type=click.Choice(['json', 'txt']),
              help='Export format for hand history')
def simulate(ai: str, profile: str, export_hand: Optional[str], export_format: str) -> None:
    """Simulate a poker hand against AI."""
    from holdem_cli.simulator.poker_simulator import PokerSimulator
    import json

    # Initialize database and check user
    db = init_database()
    user = db.get_user(profile)
    if not user:
        click.echo(f"Profile '{profile}' not found. Run 'holdem init --profile {profile}' first.")
        db.close()
        return

    try:
        # Initialize simulator
        simulator = PokerSimulator(ai_level=ai)

        # Run simulation
        result = simulator.simulate_hand()

        # Save to database
        session_id = db.create_sim_session(
            user['id'], 'texas-holdem', ai, result.winner
        )

        # Export hand history if requested
        if export_hand:
            # Export using the simulator's enhanced export functionality
            simulator.export_hand_history(export_hand, format=export_format)

            # Also save basic data to database for compatibility
            if session_id is not None:
                hand_data = {
                    "winner": result.winner,
                    "pot_size": result.pot_size,
                    "player_cards": [str(c) for c in result.player_cards],
                    "ai_cards": [str(c) for c in result.ai_cards],
                    "board": [str(c) for c in result.board],
                    "action_history": result.action_history,
                    "final_hands": result.final_hands,
                    "reasoning": result.reasoning
                }
                db.add_hand_history(session_id, json.dumps(hand_data, indent=2))
            else:
                click.echo("Warning: Could not create simulation session in database.")

            click.echo(f"\nHand history exported to: {export_hand} ({export_format.upper()} format)")

        click.echo(f"\nSimulation results saved to profile '{profile}'.")

    except KeyboardInterrupt:
        click.echo("\nSimulation cancelled.")
    except Exception as e:
        click.echo(f"Error running simulation: {e}")
    finally:
        db.close()
