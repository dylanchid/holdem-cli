# src/holdem_cli/cli/chart_commands.py
"""Chart-related CLI commands - main entry point.

This module composes all chart subcommands from:
- chart_core_commands: list, view, create, import, export
- chart_gto_commands: library, create-gto, batch-create
- chart_analysis_commands: analyze, compare, quiz
"""

import click

from .chart_core_commands import register_core_commands
from .chart_gto_commands import register_gto_commands
from .chart_analysis_commands import register_analysis_commands


@click.group()
def charts() -> None:
    """Chart viewing and analysis commands."""
    pass


# Register all subcommand groups
register_core_commands(charts)
register_gto_commands(charts)
register_analysis_commands(charts)
