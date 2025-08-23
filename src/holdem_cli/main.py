#!/usr/bin/env python3
"""
Main entry point for Holdem CLI.

This module provides the primary entry point that determines whether to launch
the CLI or TUI interface based on command line arguments.

Usage:
    holdem                    # Launch TUI with mode selection
    holdem --cli              # Launch traditional CLI mode
    holdem --help             # Show help
"""

import sys
import argparse

from .tui import launch_tui
from .cli import main as cli_main


def create_parser():
    """Create argument parser for the main entry point."""
    parser = argparse.ArgumentParser(
        description="Holdem CLI - Poker Training Tool",
        prog="holdem"
    )

    parser.add_argument(
        "--cli",
        action="store_true",
        help="Launch traditional CLI mode"
    )

    parser.add_argument(
        "--version",
        action="version",
        version="1.0.0"
    )

    return parser


def main():
    """Main entry point function."""
    parser = create_parser()
    args, remaining_args = parser.parse_known_args()

    # Store remaining args for CLI mode
    if remaining_args:
        sys.argv = [sys.argv[0]] + remaining_args

    if args.cli:
        # Launch CLI mode
        cli_main()
    else:
        # Launch TUI mode
        launch_tui()


if __name__ == "__main__":
    main()
