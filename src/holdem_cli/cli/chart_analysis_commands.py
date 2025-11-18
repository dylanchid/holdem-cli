# src/holdem_cli/cli/chart_analysis_commands.py
"""Chart analysis CLI commands: analyze, compare, quiz."""

import click
import random

from holdem_cli.storage import init_database
from holdem_cli.charts.tui.widgets.matrix import (
    ChartAction, ChartComparison, create_sample_range
)
from holdem_cli.charts.utils import launch_chart_quiz
from holdem_cli.charts.chart_cli import ChartManager


def register_analysis_commands(charts_group):
    """Register chart analysis commands to the charts group."""

    @charts_group.command('quiz')
    @click.argument('chart_name')
    @click.option('--count', '-c', default=20, help='Number of questions')
    @click.option('--interactive', '-i', is_flag=True, help='Interactive quiz mode')
    @click.option('--profile', default='default', help='Profile to save results')
    def charts_quiz(chart_name: str, count: int, interactive: bool, profile: str):
        """Quiz yourself on a chart.

        Examples:
          holdem charts quiz sample
          holdem charts quiz "BTN vs BB" --interactive
          holdem charts quiz my-chart --count 50
        """
        try:
            db = init_database()
            manager = ChartManager(db)
            actions = manager.load_chart_by_name(chart_name)

            if not actions:
                if chart_name.lower() in ['sample', 'demo']:
                    actions = create_sample_range()
                    chart_name = "Sample Chart"
                else:
                    click.echo(f"Chart '{chart_name}' not found.")
                    return

            if interactive:
                # Launch interactive quiz TUI
                click.echo(f"Starting interactive quiz for '{chart_name}'...")
                launch_chart_quiz(actions)
            else:
                # Simple terminal quiz
                click.echo(f"Starting chart quiz for '{chart_name}'...")
                _run_simple_chart_quiz(actions, count, profile, chart_name, db)

            db.close()
        except Exception as e:
            click.echo(f"Error running quiz: {e}")

    @charts_group.command('analyze')
    @click.argument('chart_name')
    @click.option('--detailed', '-d', is_flag=True, help='Show detailed analysis')
    def charts_analyze(chart_name: str, detailed: bool):
        """Analyze a GTO chart and provide insights."""
        try:
            db = init_database()
            manager = ChartManager(db)
            actions = manager.load_chart_by_name(chart_name)

            if not actions:
                click.echo(f"Chart '{chart_name}' not found.")
                return

            click.echo(f"GTO Chart Analysis: {chart_name}")
            click.echo("=" * 50)

            # Basic statistics
            total_hands = len(actions)
            raise_hands = [h for h, a in actions.items() if a.action == ChartAction.RAISE]
            call_hands = [h for h, a in actions.items() if a.action == ChartAction.CALL]
            mixed_hands = [h for h, a in actions.items() if a.action == ChartAction.MIXED]
            fold_hands = [h for h, a in actions.items() if a.action == ChartAction.FOLD]

            click.echo(f"Total hands in range: {total_hands}")
            click.echo(f"Raise hands: {len(raise_hands)} ({len(raise_hands)/total_hands*100:.1f}%)")
            click.echo(f"Call hands: {len(call_hands)} ({len(call_hands)/total_hands*100:.1f}%)")
            click.echo(f"Mixed hands: {len(mixed_hands)} ({len(mixed_hands)/total_hands*100:.1f}%)")
            click.echo(f"Fold hands: {len(fold_hands)} ({len(fold_hands)/total_hands*100:.1f}%)")

            if detailed:
                click.echo("\nDetailed Analysis:")
                click.echo("-" * 30)

                # Analyze by hand category
                pocket_pairs = [h for h in actions.keys() if len(h) == 2 and h[0] == h[1]]
                suited_aces = [h for h in actions.keys() if len(h) == 3 and h[0] == 'A' and h[2] == 's']
                offsuit_aces = [h for h in actions.keys() if len(h) == 3 and h[0] == 'A' and h[2] == 'o']
                suited_broadways = [h for h in actions.keys()
                                    if len(h) == 3 and h[2] == 's' and h[0] != 'A'
                                    and h[1] in 'KQJT98765432']

                click.echo(f"Pocket pairs: {len([h for h in pocket_pairs if actions[h].action in [ChartAction.RAISE, ChartAction.MIXED]])}/{len(pocket_pairs)} raising")
                click.echo(f"Suited aces: {len([h for h in suited_aces if actions[h].action in [ChartAction.RAISE, ChartAction.MIXED]])}/{len(suited_aces)} raising")
                click.echo(f"Offsuit aces: {len([h for h in offsuit_aces if actions[h].action in [ChartAction.RAISE, ChartAction.MIXED]])}/{len(offsuit_aces)} raising")
                click.echo(f"Suited broadways: {len([h for h in suited_broadways if actions[h].action in [ChartAction.RAISE, ChartAction.MIXED]])}/{len(suited_broadways)} raising")

                # EV analysis
                total_ev = sum(action.ev for action in actions.values() if action.ev is not None)
                avg_ev = total_ev / total_hands
                click.echo("\nEV Analysis:")
                click.echo(f"Average EV per hand: {avg_ev:.2f}")
                click.echo(f"Total EV for range: {total_ev:.2f}")

            db.close()

        except Exception as e:
            click.echo(f"Error analyzing chart: {e}")

    @charts_group.command('compare')
    @click.argument('chart1')
    @click.argument('chart2')
    @click.option('--interactive', '-i', is_flag=True, help='Interactive comparison')
    def charts_compare(chart1: str, chart2: str, interactive: bool):
        """Compare two charts."""
        try:
            db = init_database()
            manager = ChartManager(db)

            actions1 = manager.load_chart_by_name(chart1)
            actions2 = manager.load_chart_by_name(chart2)

            if not actions1:
                click.echo(f"Chart '{chart1}' not found.")
                return
            if not actions2:
                click.echo(f"Chart '{chart2}' not found.")
                return

            comparison = ChartComparison(actions1, actions2, chart1, chart2)

            if interactive:
                # Launch interactive comparison (would need separate TUI)
                click.echo("Interactive comparison not yet implemented.")
                click.echo("Showing text comparison instead:\n")

            # Show text comparison
            output = comparison.render_comparison(use_colors=True)
            click.echo(output)

            db.close()
        except Exception as e:
            click.echo(f"Error comparing charts: {e}")


def _run_simple_chart_quiz(actions, count, profile, chart_name, db):
    """Run a simple terminal-based chart quiz."""
    hands = list(actions.keys())
    if len(hands) < count:
        count = len(hands)

    quiz_hands = random.sample(hands, count)
    correct = 0

    # Check user exists
    user = db.get_user(profile)
    if not user:
        click.echo(f"Profile '{profile}' not found.")
        return

    click.echo(f"{chart_name} Quiz - {count} questions")
    click.echo("=" * 50)

    scenarios = [
        "You're on the button vs big blind 3-bet",
        "You're in cutoff vs UTG raise",
        "You're in big blind vs button raise",
        "You're under the gun opening"
    ]

    for i, hand in enumerate(quiz_hands, 1):
        correct_action = actions[hand]
        scenario = random.choice(scenarios)

        click.echo(f"\nQuestion {i}/{count}")
        click.echo(f"Situation: {scenario}")
        click.echo(f"Your hand: {hand}")
        click.echo("What's your action?")
        click.echo("1) Raise  2) Call  3) Fold")

        while True:
            try:
                answer = click.prompt("Your choice (1-3)", type=int)
                if 1 <= answer <= 3:
                    break
                click.echo("Please enter 1, 2, or 3")
            except click.Abort:
                click.echo("\nQuiz cancelled.")
                return

        action_map = {1: "raise", 2: "call", 3: "fold"}
        user_action = action_map[answer]

        if user_action == correct_action.action.value:
            click.echo("Correct!")
            correct += 1
        else:
            click.echo(f"Wrong. Correct answer: {correct_action.action.value.title()}")
            if correct_action.notes:
                click.echo(f"   {correct_action.notes}")
            else:
                click.echo(f"   Frequency: {correct_action.frequency:.0%}")

    accuracy = (correct / count) * 100
    click.echo("\nQuiz Complete!")
    click.echo(f"Score: {correct}/{count} ({accuracy:.1f}%)")

    if accuracy >= 90:
        click.echo("Excellent! You know this chart well.")
    elif accuracy >= 75:
        click.echo("Good job! Keep practicing.")
    elif accuracy >= 60:
        click.echo("Not bad, but there's room for improvement.")
    else:
        click.echo("Consider studying this chart more.")

    # Save quiz results
    try:
        session_id = db.create_quiz_session(
            user['id'], f'chart-{chart_name}', correct, count, 'medium'
        )
        click.echo(f"\nResults saved to profile '{profile}'")
    except Exception as e:
        click.echo(f"Could not save results: {e}")
