# src/holdem_cli/cli/main.py
"""Main CLI entry point and core commands."""

import click
from pathlib import Path

from holdem_cli.storage import init_database, get_database_path
from .quiz_commands import quiz
from .equity_commands import equity
from .simulate_commands import simulate
from .profile_commands import profile
from .chart_commands import charts


@click.group()
@click.version_option(version="1.0.0")
def main() -> None:
    """Holdem CLI - A terminal-based poker training tool with chart support."""
    pass


# Register command groups
main.add_command(quiz)
main.add_command(equity)
main.add_command(simulate)
main.add_command(profile)
main.add_command(charts)


@main.command()
@click.option('--profile', default='default', help='Profile name to use')
def init(profile: str) -> None:
    """Initialize Holdem CLI with a new profile."""
    from holdem_cli.charts.tui.widgets.matrix import create_sample_range
    from holdem_cli.charts.chart_cli import ChartManager

    db_path = get_database_path()

    # Create directory if it doesn't exist
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Initialize database
    db = init_database()

    # Check if user exists
    user = db.get_user(profile)
    if user:
        click.echo(f"Profile '{profile}' already exists.")
    else:
        # Create new user
        user_id = db.create_user(profile)
        click.echo(f"Created new profile: {profile}")

    click.echo(f"Database initialized at: {db_path}")
    click.echo("\nQuick start:")
    click.echo("  holdem quiz hand-ranking    # Take a hand ranking quiz")
    click.echo("  holdem equity AsKs 7h7d     # Calculate hand equity")
    click.echo("  holdem charts view sample   # View sample chart")
    click.echo("  holdem charts list          # List all charts")
    click.echo("  holdem profile list         # List all profiles")

    # Create sample chart for new users
    if not user:
        try:
            manager = ChartManager(db)
            sample_actions = create_sample_range()
            manager.save_chart(
                "Sample GTO Chart",
                "BTN vs BB 3-bet defense",
                sample_actions,
                100,
                "BTN",
                "BB"
            )
            click.echo("  Sample chart created")
        except Exception as e:
            click.echo(f"  Could not create sample chart: {e}")

    db.close()


if __name__ == '__main__':
    main()
