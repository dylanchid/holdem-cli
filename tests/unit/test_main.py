"""Tests for the main entry point module."""

import pytest
import sys
from unittest.mock import patch, MagicMock

from holdem_cli.main import create_parser, main


class TestCreateParser:
    """Tests for create_parser function."""

    def test_returns_argument_parser(self):
        """Test that create_parser returns an ArgumentParser."""
        import argparse
        parser = create_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    def test_parser_prog_name(self):
        """Test that parser has correct program name."""
        parser = create_parser()
        assert parser.prog == "holdem"

    def test_parser_description(self):
        """Test that parser has correct description."""
        parser = create_parser()
        assert "Poker Training Tool" in parser.description

    def test_cli_argument_exists(self):
        """Test that --cli argument is recognized."""
        parser = create_parser()
        # Parse with --cli flag
        args = parser.parse_args(["--cli"])
        assert args.cli is True

    def test_cli_argument_default_false(self):
        """Test that --cli defaults to False."""
        parser = create_parser()
        args = parser.parse_args([])
        assert args.cli is False

    def test_version_argument_exists(self):
        """Test that --version argument is recognized."""
        parser = create_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--version"])
        # SystemExit with code 0 indicates successful version display
        assert exc_info.value.code == 0

    def test_unknown_args_with_parse_known_args(self):
        """Test that unknown arguments are captured with parse_known_args."""
        parser = create_parser()
        args, remaining = parser.parse_known_args(["--cli", "quiz", "--count", "10"])
        assert args.cli is True
        assert remaining == ["quiz", "--count", "10"]


class TestMain:
    """Tests for main function."""

    @patch('holdem_cli.main.launch_tui')
    def test_launches_tui_by_default(self, mock_tui):
        """Test that TUI is launched when no arguments provided."""
        with patch.object(sys, 'argv', ['holdem']):
            main()
        mock_tui.assert_called_once()

    @patch('holdem_cli.main.cli_main')
    def test_launches_cli_with_cli_flag(self, mock_cli):
        """Test that CLI is launched when --cli flag provided."""
        with patch.object(sys, 'argv', ['holdem', '--cli']):
            main()
        mock_cli.assert_called_once()

    @patch('holdem_cli.main.cli_main')
    def test_passes_remaining_args_to_cli(self, mock_cli):
        """Test that remaining arguments are passed to CLI mode."""
        original_argv = sys.argv.copy()
        try:
            sys.argv = ['holdem', '--cli', 'quiz', '--count', '10']
            main()
            # After main(), sys.argv should be modified to contain remaining args
            assert sys.argv == ['holdem', 'quiz', '--count', '10']
            mock_cli.assert_called_once()
        finally:
            sys.argv = original_argv

    @patch('holdem_cli.main.launch_tui')
    def test_tui_mode_with_no_remaining_args(self, mock_tui):
        """Test TUI mode doesn't modify sys.argv when no remaining args."""
        original_argv = sys.argv.copy()
        try:
            sys.argv = ['holdem']
            main()
            mock_tui.assert_called_once()
        finally:
            sys.argv = original_argv

    @patch('holdem_cli.main.cli_main')
    def test_remaining_args_without_cli_flag(self, mock_cli):
        """Test that unknown args still work with TUI mode."""
        with patch('holdem_cli.main.launch_tui') as mock_tui:
            original_argv = sys.argv.copy()
            try:
                sys.argv = ['holdem', 'some', 'args']
                main()
                # TUI should be called since --cli not provided
                mock_tui.assert_called_once()
                mock_cli.assert_not_called()
            finally:
                sys.argv = original_argv


class TestMainIntegration:
    """Integration tests for main module."""

    def test_parser_handles_help(self):
        """Test that help can be displayed without error."""
        parser = create_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--help"])
        assert exc_info.value.code == 0

    def test_parser_rejects_invalid_args(self):
        """Test that invalid arguments cause error."""
        parser = create_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--invalid-arg"])
        assert exc_info.value.code != 0
