# src/holdem_cli/cli/chart_gto_commands.py
"""GTO chart CLI commands: library, create-gto, batch-create."""

import click
from typing import Optional

from holdem_cli.storage import init_database
from holdem_cli.charts.tui.widgets.matrix import ChartAction
from holdem_cli.charts.chart_cli import ChartManager
from holdem_cli.charts.gto_library import GTOChartLibrary


def register_gto_commands(charts_group: click.Group) -> None:
    """Register GTO chart commands to the charts group."""

    @charts_group.command('library')
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

    @charts_group.command('create-gto')
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

    @charts_group.command('batch-create')
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
