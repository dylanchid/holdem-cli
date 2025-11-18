# src/holdem_cli/cli/profile_commands.py
"""Profile management CLI commands."""

import click
from holdem_cli.storage import init_database


@click.group()
def profile() -> None:
    """Profile management commands."""
    pass


@profile.command('list')
def profile_list() -> None:
    """List all profiles."""
    try:
        db = init_database()
        users = db.list_users()

        if not users:
            click.echo("No profiles found. Run 'holdem init' to create one.")
        else:
            click.echo("Profiles:")
            for user in users:
                created = user['created_at']
                click.echo(f"  {user['name']} (created: {created})")

        db.close()
    except Exception as e:
        click.echo(f"Error accessing database: {e}")


@profile.command('stats')
@click.argument('name')
def profile_stats(name: str) -> None:
    """Show statistics for a profile."""
    try:
        db = init_database()
        user = db.get_user(name)

        if not user:
            click.echo(f"Profile '{name}' not found.")
            db.close()
            return

        stats = db.get_user_quiz_stats(user['id'])

        click.echo(f"Statistics for {name}:")
        click.echo(f"  Total quiz sessions: {stats['overall']['total_sessions']}")
        if stats['overall']['avg_accuracy']:
            click.echo(f"  Average accuracy: {stats['overall']['avg_accuracy']:.1f}%")
            click.echo(f"  Total questions answered: {stats['overall']['total_questions']}")

        if stats['by_type']:
            click.echo("\nBy quiz type:")
            for quiz_type, type_stats in stats['by_type'].items():
                click.echo(f"  {quiz_type}: {type_stats['avg_accuracy']:.1f}% avg "
                          f"({type_stats['sessions']} sessions)")

        db.close()
    except Exception as e:
        click.echo(f"Error: {e}")
