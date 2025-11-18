# src/holdem_cli/cli/chart_core_commands.py
"""Core chart CLI commands: list, view, create, import, export."""

import click
import json
from pathlib import Path
from typing import Optional

from holdem_cli.storage import init_database
from holdem_cli.charts.tui.widgets.matrix import (
    HandMatrix, HandAction, ChartAction, create_sample_range
)
from holdem_cli.charts.utils import launch_interactive_chart_viewer, create_chart_from_file
from holdem_cli.charts.chart_cli import ChartManager


def register_core_commands(charts_group):
    """Register core chart commands to the charts group."""

    @charts_group.command('list')
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

    @charts_group.command('view')
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

    @charts_group.command('create')
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

    @charts_group.command('import')
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

    @charts_group.command('export')
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


# Helper functions for templates

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
