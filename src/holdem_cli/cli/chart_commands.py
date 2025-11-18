# src/holdem_cli/cli/chart_commands.py
"""Chart-related CLI commands."""

import click
import json
import random
from pathlib import Path
from typing import Optional

from holdem_cli.storage import init_database
from holdem_cli.charts.tui.widgets.matrix import (
    HandMatrix, HandAction, ChartAction, ChartComparison, create_sample_range
)
from holdem_cli.charts.chart_tui import launch_interactive_chart_viewer, launch_chart_quiz
from holdem_cli.charts.chart_cli import ChartManager
from holdem_cli.charts.gto_library import GTOChartLibrary


@click.group()
def charts() -> None:
    """Chart viewing and analysis commands."""
    pass


@charts.command('list')
def charts_list():
    """List all saved charts."""
    try:
        db = init_database()
        manager = ChartManager(db)
        charts_data = manager.list_charts()

        if not charts_data:
            click.echo("No charts found. Import or create some charts first.")
            click.echo("\nTry:")
            click.echo("  holdem charts view sample    # View sample chart")
            click.echo("  holdem charts create my-chart # Create new chart")
            return

        click.echo("\nSaved Charts:")
        click.echo("=" * 80)

        for chart in charts_data:
            click.echo(f"{chart['name']}")
            click.echo(f"   ID: {chart['id']}")
            click.echo(f"   Spot: {chart['spot']}")
            click.echo(f"   Stack: {chart['stack_depth']}bb")
            if chart['position_hero'] and chart['position_villain']:
                click.echo(f"   Matchup: {chart['position_hero']} vs {chart['position_villain']}")
            click.echo(f"   Created: {chart['created_at']}")
            click.echo("-" * 40)

        db.close()
    except Exception as e:
        click.echo(f"Error listing charts: {e}")


@charts.command('view')
@click.argument('chart_name')
@click.option('--interactive', '-i', is_flag=True, help='Launch interactive TUI')
@click.option('--compact', is_flag=True, help='Use compact display')
@click.option('--no-color', is_flag=True, help='Disable colors')
def charts_view(chart_name: str, interactive: bool, compact: bool, no_color: bool):
    """View a specific chart.

    Examples:
      holdem charts view sample
      holdem charts view "BTN vs BB" --interactive
      holdem charts view my-chart --compact --no-color
    """
    try:
        db = init_database()
        manager = ChartManager(db)

        # Try to load from database first
        actions = manager.load_chart_by_name(chart_name)

        if not actions:
            # Try loading sample charts
            if chart_name.lower() in ['sample', 'demo', 'test']:
                actions = create_sample_range()
                chart_name = "Sample GTO Chart"
            else:
                click.echo(f"Chart '{chart_name}' not found.")
                click.echo("Use 'holdem charts list' to see available charts.")
                click.echo("Try 'holdem charts view sample' for a demo.")
                return

        if interactive:
            # Launch TUI
            click.echo(f"Launching interactive viewer for '{chart_name}'...")
            launch_interactive_chart_viewer(chart_name, actions)
        else:
            # Terminal display
            matrix = HandMatrix(actions, chart_name)
            output = matrix.render(use_colors=not no_color, compact=compact)
            click.echo(output)

        db.close()
    except Exception as e:
        click.echo(f"Error viewing chart: {e}")


@charts.command('quiz')
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


@charts.command('import')
@click.argument('filepath')
@click.option('--format', '-f',
              type=click.Choice(['json', 'simple']),
              default='json', help='Input file format')
@click.option('--name', help='Chart name (default: filename)')
@click.option('--spot', help='Poker spot description')
@click.option('--depth', default=100, help='Stack depth in BB')
def charts_import(filepath: str, format: str, name: Optional[str],
                 spot: Optional[str], depth: int):
    """Import chart from file.

    Supported formats:
      json   - Standard JSON format
      simple - Text format: hand action frequency

    Examples:
      holdem charts import my_chart.json
      holdem charts import ranges.txt --format simple --name "My Range"
    """
    try:
        from holdem_cli.charts.chart_tui import create_chart_from_file

        actions = create_chart_from_file(filepath, format)

        if not actions:
            click.echo("No valid chart data found in file.")
            return

        # Generate name if not provided
        if not name:
            name = Path(filepath).stem.replace('_', ' ').title()

        if not spot:
            spot = f"Imported from {Path(filepath).name}"

        # Save to database
        db = init_database()
        manager = ChartManager(db)
        chart_id = manager.save_chart(name, spot, actions, depth)

        click.echo("Chart imported successfully!")
        click.echo(f"   Name: {name}")
        click.echo(f"   ID: {chart_id}")
        click.echo(f"   Hands: {len(actions)}")
        click.echo(f"   Spot: {spot}")
        click.echo(f"\nView with: holdem charts view \"{name}\"")

        db.close()
    except FileNotFoundError:
        click.echo(f"File not found: {filepath}")
    except Exception as e:
        click.echo(f"Error importing chart: {e}")


@charts.command('export')
@click.argument('chart_name')
@click.argument('output_path')
@click.option('--format', '-f',
              type=click.Choice(['json', 'txt', 'csv']),
              default='txt', help='Output format')
def charts_export(chart_name: str, output_path: str, format: str):
    """Export chart to file.

    Examples:
      holdem charts export sample my_chart.txt
      holdem charts export "BTN vs BB" ranges.json --format json
      holdem charts export my-chart data.csv --format csv
    """
    try:
        db = init_database()
        manager = ChartManager(db)
        actions = manager.load_chart_by_name(chart_name)

        if not actions:
            click.echo(f"Chart '{chart_name}' not found.")
            return

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        if format == 'json':
            # Export as JSON
            export_data = {
                "name": chart_name,
                "export_format": "holdem-cli-v1",
                "ranges": {
                    hand: {
                        "action": action.action.value,
                        "frequency": action.frequency,
                        "ev": action.ev,
                        "notes": action.notes
                    }
                    for hand, action in actions.items()
                }
            }

            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2)

        elif format == 'txt':
            # Export as text matrix
            matrix = HandMatrix(actions, chart_name)
            matrix.export_to_text(str(output_file))

        elif format == 'csv':
            # Export as CSV
            import csv
            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Hand', 'Action', 'Frequency', 'EV', 'Notes'])

                for hand, action in actions.items():
                    writer.writerow([
                        hand,
                        action.action.value,
                        action.frequency,
                        action.ev or '',
                        action.notes
                    ])

        click.echo(f"Chart exported to: {output_file}")
        click.echo(f"Format: {format.upper()}")
        click.echo(f"Hands: {len(actions)}")

        db.close()
    except Exception as e:
        click.echo(f"Error exporting chart: {e}")


@charts.command('create')
@click.argument('name')
@click.option('--spot', help='Poker spot description')
@click.option('--depth', default=100, help='Stack depth in BB')
@click.option('--template', type=click.Choice(['tight', 'loose', 'balanced']),
              help='Use a template as starting point')
def charts_create(name: str, spot: Optional[str], depth: int, template: Optional[str]):
    """Create a new chart.

    Examples:
      holdem charts create "My BTN Range"
      holdem charts create "UTG Range" --template tight
      holdem charts create "Loose 3bet" --template loose --depth 200
    """
    try:
        # Create base chart
        if template == 'tight':
            actions = _create_tight_template()
        elif template == 'loose':
            actions = _create_loose_template()
        elif template == 'balanced':
            actions = create_sample_range()
        else:
            actions = {}

        if not spot:
            spot = f"Custom chart - {name}"

        # Save to database
        db = init_database()
        manager = ChartManager(db)
        chart_id = manager.save_chart(name, spot, actions, depth)

        click.echo("Chart created successfully!")
        click.echo(f"   Name: {name}")
        click.echo(f"   ID: {chart_id}")
        click.echo(f"   Template: {template or 'empty'}")
        click.echo(f"   Hands: {len(actions)}")
        click.echo(f"   Stack: {depth}bb")
        click.echo(f"\nView with: holdem charts view \"{name}\"")

        db.close()
    except Exception as e:
        click.echo(f"Error creating chart: {e}")


@charts.command('library')
@click.option('--hero', '-h', help='Hero position (UTG, HJ, CO, BTN, SB, BB)')
@click.option('--villain', '-v', help='Villain position (UTG, HJ, CO, BTN, SB, BB)')
@click.option('--depth', '-d', type=int, help='Stack depth in BB')
@click.option('--scenario', '-s',
              type=click.Choice(GTOChartLibrary.get_available_scenarios()),
              default='open_raise', help='Scenario type')
def charts_library(hero: Optional[str], villain: Optional[str], depth: Optional[int], scenario: Optional[str]):
    """Browse and search the GTO chart library."""
    try:
        if hero or villain or depth or scenario:
            # Search specific charts
            charts_data = GTOChartLibrary.search_charts(
                hero_pos=hero,
                villain_pos=villain,
                min_depth=depth,
                max_depth=depth,
                scenario=scenario
            )
        else:
            # List all available charts
            charts_data = GTOChartLibrary.list_available_charts()

        if not charts_data:
            click.echo("No charts found matching criteria.")
            return

        click.echo(f"\nGTO Chart Library - {len(charts_data)} charts available")
        click.echo("=" * 70)

        # Group by hero position
        by_hero = {}
        for chart in charts_data:
            hero_pos = chart['hero_position']
            if hero_pos not in by_hero:
                by_hero[hero_pos] = []
            by_hero[hero_pos].append(chart)

        for hero_pos, hero_charts in sorted(by_hero.items()):
            click.echo(f"\n{hero_pos} Position:")
            click.echo("-" * 40)

            for chart in sorted(hero_charts, key=lambda x: (x['villain_position'], x['stack_depth'])):
                click.echo(f"  vs {chart['villain_position']:3} @ {chart['stack_depth']:3}bb - {chart['scenario']}")

        click.echo("\nUse 'holdem charts create-gto' to add charts to your database")

    except Exception as e:
        click.echo(f"Error browsing chart library: {e}")


@charts.command('create-gto')
@click.option('--hero', '-h', required=True, help='Hero position (UTG, HJ, CO, BTN, SB, BB)')
@click.option('--villain', '-v', required=True, help='Villain position (UTG, HJ, CO, BTN, SB, BB)')
@click.option('--depth', '-d', type=int, default=100, help='Stack depth in BB')
@click.option('--scenario', '-s',
              type=click.Choice(GTOChartLibrary.get_available_scenarios()),
              default='open_raise', help='Scenario type')
@click.option('--name', help='Custom chart name (auto-generated if not provided)')
def charts_create_gto(hero: str, villain: str, depth: int, scenario: str, name: Optional[str]):
    """Create a GTO chart from the library and add it to your database."""
    try:
        # Validate positions
        available_positions = GTOChartLibrary.get_available_positions()
        if hero not in available_positions:
            click.echo(f"Invalid hero position: {hero}")
            click.echo(f"   Available: {', '.join(available_positions)}")
            return
        if villain not in available_positions:
            click.echo(f"Invalid villain position: {villain}")
            click.echo(f"   Available: {', '.join(available_positions)}")
            return

        # Create the chart
        click.echo(f"Generating GTO chart: {hero} vs {villain} ({depth}bb) - {scenario}")
        actions = GTOChartLibrary.create_position_chart(hero, villain, depth, scenario)

        # Generate chart name if not provided
        if not name:
            scenario_name = scenario.replace('_', ' ').title()
            name = f"{hero} vs {villain} {scenario_name} ({depth}bb)"

        # Generate spot description
        spot = f"{hero} vs {villain} {scenario.replace('_', ' ')}"

        # Save to database
        db = init_database()
        manager = ChartManager(db)
        chart_id = manager.save_chart(name, spot, actions, depth,
                                    position_hero=hero, position_villain=villain)

        click.echo("GTO Chart created successfully!")
        click.echo(f"   Name: {name}")
        click.echo(f"   ID: {chart_id}")
        click.echo(f"   Hands: {len(actions)}")
        click.echo(f"   Scenario: {scenario}")
        click.echo(f"   Stack: {depth}bb")

        # Show chart statistics
        raise_count = sum(1 for a in actions.values() if a.action == ChartAction.RAISE)
        call_count = sum(1 for a in actions.values() if a.action == ChartAction.CALL)
        mixed_count = sum(1 for a in actions.values() if a.action == ChartAction.MIXED)
        fold_count = sum(1 for a in actions.values() if a.action == ChartAction.FOLD)

        click.echo("\nRange Composition:")
        if raise_count > 0:
            click.echo(f"   Raise: {raise_count} hands")
        if call_count > 0:
            click.echo(f"   Call: {call_count} hands")
        if mixed_count > 0:
            click.echo(f"   Mixed: {mixed_count} hands")
        if fold_count > 0:
            click.echo(f"   Fold: {fold_count} hands")

        click.echo(f"\nUse 'holdem charts view \"{name}\"' to view the chart")
        click.echo(f"Use 'holdem charts quiz \"{name}\"' to practice with it")

        db.close()

    except Exception as e:
        click.echo(f"Error creating GTO chart: {e}")


@charts.command('batch-create')
@click.option('--positions', help='Comma-separated list of positions (default: all)')
@click.option('--depths', help='Comma-separated list of stack depths (default: 50,100,200)')
@click.option('--scenarios', help='Comma-separated list of scenarios (default: open_raise)')
@click.option('--confirm', is_flag=True, help='Confirm batch creation')
def charts_batch_create(positions: Optional[str], depths: Optional[str],
                       scenarios: Optional[str], confirm: bool):
    """Create multiple GTO charts at once."""
    try:
        # Parse parameters
        if positions:
            hero_positions = [p.strip() for p in positions.split(',')]
        else:
            hero_positions = GTOChartLibrary.get_available_positions()

        if depths:
            stack_depths = [int(d.strip()) for d in depths.split(',')]
        else:
            stack_depths = [50, 100, 200]

        if scenarios:
            scenario_list = [s.strip() for s in scenarios.split(',')]
        else:
            scenario_list = ['open_raise']

        # Generate villain positions (focus on common matchups)
        villain_positions = ['BB', 'BTN', 'CO']  # Most common opponents

        # Calculate total charts
        total_charts = len(hero_positions) * len(villain_positions) * len(stack_depths) * len(scenario_list)

        click.echo("Batch Chart Creation Plan:")
        click.echo(f"   Hero positions: {', '.join(hero_positions)}")
        click.echo(f"   Villain positions: {', '.join(villain_positions)}")
        click.echo(f"   Stack depths: {', '.join(map(str, stack_depths))}bb")
        click.echo(f"   Scenarios: {', '.join(scenario_list)}")
        click.echo(f"   Total charts: {total_charts}")

        if not confirm:
            click.echo("\nUse --confirm to proceed with creation")
            return

        click.echo(f"\nCreating {total_charts} GTO charts...")

        created_count = 0
        db = init_database()
        manager = ChartManager(db)

        for hero_pos in hero_positions:
            for villain_pos in villain_positions:
                if hero_pos == villain_pos:
                    continue  # Skip same position

                for stack_depth in stack_depths:
                    for scenario in scenario_list:
                        try:
                            # Create chart
                            actions = GTOChartLibrary.create_position_chart(
                                hero_pos, villain_pos, stack_depth, scenario
                            )

                            # Generate name
                            scenario_name = scenario.replace('_', ' ').title()
                            name = f"{hero_pos} vs {villain_pos} {scenario_name} ({stack_depth}bb)"

                            # Generate spot
                            spot = f"{hero_pos} vs {villain_pos} {scenario.replace('_', ' ')}"

                            # Save to database
                            chart_id = manager.save_chart(
                                name, spot, actions, stack_depth,
                                position_hero=hero_pos, position_villain=villain_pos
                            )

                            created_count += 1

                            if created_count % 10 == 0:
                                click.echo(f"   Progress: {created_count}/{total_charts} charts created...")

                        except Exception as e:
                            click.echo(f"   Error creating {hero_pos} vs {villain_pos} {scenario}: {e}")

        click.echo("\nBatch creation complete!")
        click.echo(f"   Created: {created_count} charts")
        click.echo("   Use 'holdem charts list' to view all charts")

        db.close()

    except Exception as e:
        click.echo(f"Error in batch creation: {e}")


@charts.command('analyze')
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


@charts.command('compare')
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


# Helper functions

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


def _create_tight_template():
    """Create a tight range template."""
    actions = {}

    # Very premium hands
    premium = ["AA", "KK", "QQ", "JJ", "AKs", "AKo"]
    for hand in premium:
        actions[hand] = HandAction(ChartAction.RAISE, frequency=1.0, ev=3.0,
                                  notes="Premium hand, always raise")

    # Strong pairs
    strong_pairs = ["TT", "99"]
    for hand in strong_pairs:
        actions[hand] = HandAction(ChartAction.CALL, frequency=1.0, ev=1.0,
                                  notes="Strong pair, call for set value")

    return actions


def _create_loose_template():
    """Create a loose range template."""
    actions = {}

    # Many raising hands
    raise_hands = ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66",
                   "AKs", "AKo", "AQs", "AQo", "AJs", "AJo", "ATs", "A9s"]
    for hand in raise_hands:
        actions[hand] = HandAction(ChartAction.RAISE, frequency=0.8, ev=1.5,
                                  notes="Aggressive line")

    # Calling hands
    call_hands = ["55", "44", "33", "22", "KQs", "KQo", "KJs", "KTs",
                  "QJs", "QTs", "JTs", "A8s", "A7s", "A6s", "A5s"]
    for hand in call_hands:
        actions[hand] = HandAction(ChartAction.CALL, frequency=1.0, ev=0.5,
                                  notes="Call for value/position")

    return actions
