"""
Utility functions and helpers for the TUI.

This module contains utility functions, CLI integration functions,
and helper methods used across the TUI components.

Note: This module re-exports functions from submodules for backwards compatibility.
The functionality has been split into:
- loaders.py: File loading functions
- operations.py: Chart manipulation and analysis
"""

import signal
import sys
from typing import Dict, Optional

from .app import ChartViewerApp
from .quiz import ChartQuizApp
from .constants import DEFAULT_CHART_NAME
from .tui.widgets.matrix import create_sample_range
from holdem_cli.types import HandAction
from holdem_cli.utils.error_handling import log_error_and_continue
from holdem_cli.utils.logging_utils import get_logger

# Re-export from loaders module
from .loaders import (
    create_chart_from_file,
    load_json_chart,
    load_simple_chart,
    load_pio_chart,
    load_gto_wizard_chart,
)

# Re-export from operations module
from .operations import (
    merge_charts,
    filter_chart_by_action,
    filter_chart_by_frequency,
    get_chart_statistics,
    export_chart_statistics,
    validate_chart,
    save_chart_to_db,
    load_chart_from_db,
)


def run_chart_viewer(chart_name: str = DEFAULT_CHART_NAME) -> None:
    """Run the chart viewer application."""
    app = ChartViewerApp(chart_name)
    app.run()


def launch_interactive_chart_viewer(
    chart_name: Optional[str] = None,
    chart_data: Optional[Dict[str, HandAction]] = None
) -> None:
    """Launch the interactive chart viewer from CLI."""
    if chart_data is None:
        chart_data = create_sample_range()

    if chart_name is None:
        chart_name = "Interactive Chart"

    app = ChartViewerApp(chart_name)
    app.current_chart = chart_data
    app.run()


def launch_chart_quiz(chart_data: Optional[Dict[str, HandAction]] = None) -> None:
    """Launch the chart training quiz from CLI."""
    if chart_data is None:
        chart_data = create_sample_range()

    app = ChartQuizApp(chart_data)
    app.run()


def demo_tui() -> None:
    """Demonstrate the TUI components."""
    logger = get_logger()

    def signal_handler(sig, frame):
        """Handle interrupt signals gracefully."""
        logger.info("Shutting down TUI gracefully...")
        sys.exit(0)

    # Set up signal handlers for better terminal handling
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("Starting Holdem CLI Chart TUI Demo...")
    logger.info("Press Ctrl+C to exit gracefully")

    try:
        # Create sample data
        sample_chart = create_sample_range()

        # Run the chart viewer
        run_chart_viewer("Demo Chart")
    except KeyboardInterrupt:
        logger.info("TUI interrupted by user")
    except Exception as e:
        log_error_and_continue(e, operation="demo_tui")
        logger.error(f"TUI error: {e}")
    finally:
        logger.info("TUI demo completed")


def demo_quiz() -> None:
    """Demonstrate the quiz functionality."""
    logger = get_logger()
    logger.info("Starting Chart Quiz Demo...")

    sample_chart = create_sample_range()
    quiz_app = ChartQuizApp(sample_chart)
    quiz_app.run()


# Backwards compatibility aliases for private functions
# These are deprecated but kept for compatibility
_load_json_chart = load_json_chart
_load_simple_chart = load_simple_chart
_load_pio_chart = load_pio_chart
_load_gto_wizard_chart = load_gto_wizard_chart
