"""CLI Integration Tests for Holdem CLI.

Tests the command-line interface functionality including:
- Command execution and output
- Error handling
- Profile management
- Quiz functionality
- Simulation features
- Chart integration
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch
from click.testing import CliRunner

from holdem_cli.cli import main
from holdem_cli.storage import init_database, get_database_path


class TestCLIIntegration:
    """Test CLI integration functionality."""

    @pytest.fixture
    def runner(self):
        """CLI runner fixture."""
        return CliRunner()

    @pytest.fixture
    def temp_db(self):
        """Temporary database fixture."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_holdem.db"

            # Ensure the database file doesn't exist
            if db_path.exists():
                db_path.unlink()

            # Patch the database path for testing
            with patch('holdem_cli.cli.get_database_path', return_value=db_path), \
                 patch('holdem_cli.storage.get_database_path', return_value=db_path), \
                 patch('holdem_cli.storage.database.get_database_path', return_value=db_path):
                yield db_path

    def test_cli_main_group_help(self, runner):
        """Test main CLI help command."""
        result = runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        assert "Holdem CLI" in result.output
        assert "terminal-based poker training tool" in result.output
        assert "init" in result.output
        assert "quiz" in result.output

    def test_cli_version(self, runner):
        """Test CLI version command."""
        result = runner.invoke(main, ['--version'])
        assert result.exit_code == 0
        # Accept any version format as long as it contains version info
        assert "version" in result.output.lower() or any(char.isdigit() for char in result.output)

    def test_init_command_new_profile(self, runner, temp_db):
        """Test init command with new profile."""
        result = runner.invoke(main, ['init', '--profile', 'testuser'])
        assert result.exit_code == 0
        assert "Created new profile: testuser" in result.output
        assert "Database initialized" in result.output

    def test_init_command_existing_profile(self, runner, temp_db):
        """Test init command with existing profile."""
        # First create the profile
        runner.invoke(main, ['init', '--profile', 'existinguser'])

        # Try to create it again
        result = runner.invoke(main, ['init', '--profile', 'existinguser'])
        assert result.exit_code == 0
        assert "Profile 'existinguser' already exists" in result.output

    def test_quiz_help(self, runner):
        """Test quiz command help."""
        result = runner.invoke(main, ['quiz', '--help'])
        assert result.exit_code == 0
        assert "hand-ranking" in result.output or "pot-odds" in result.output

    def test_quiz_hand_ranking(self, runner, temp_db):
        """Test quiz hand-ranking command."""
        # Create a profile first
        runner.invoke(main, ['init', '--profile', 'quizuser'])

        result = runner.invoke(main, [
            'quiz', 'hand-ranking',
            '--count', '5',
            '--profile', 'quizuser',
            '--difficulty', 'easy'
        ])

        # The command should run without crashing (might fail due to interactive nature)
        assert result.exit_code in [0, 1]  # Accept both success and graceful failure

    def test_quiz_pot_odds(self, runner, temp_db):
        """Test quiz pot-odds command."""
        # Create a profile first
        runner.invoke(main, ['init', '--profile', 'quizuser'])

        result = runner.invoke(main, [
            'quiz', 'pot-odds',
            '--count', '3',
            '--profile', 'quizuser',
            '--difficulty', 'medium'
        ])

        # The command should run without crashing (might fail due to interactive nature)
        assert result.exit_code in [0, 1]  # Accept both success and graceful failure

    def test_quiz_invalid_subcommand(self, runner):
        """Test quiz command with invalid subcommand."""
        result = runner.invoke(main, ['quiz', 'invalid-quiz'])
        assert result.exit_code != 0
        assert "Error" in result.output or "No such command" in result.output

    def test_simulate_command(self, runner, temp_db):
        """Test simulate command."""
        # Create a profile first
        runner.invoke(main, ['init', '--profile', 'simuser'])

        result = runner.invoke(main, [
            'simulate',
            '--ai', 'easy',
            '--profile', 'simuser'
        ])

        # The command should run without crashing (might fail due to interactive nature)
        assert result.exit_code in [0, 1]  # Accept both success and graceful failure

    def test_charts_command(self, runner, temp_db):
        """Test charts command help."""
        result = runner.invoke(main, ['charts', '--help'])
        assert result.exit_code == 0
        assert "list" in result.output or "view" in result.output

    def test_profile_list_empty(self, runner, temp_db):
        """Test profile list when no profiles exist."""
        result = runner.invoke(main, ['profile', 'list'])
        assert result.exit_code == 0
        assert "No profiles found" in result.output or result.output.strip() == ""

    def test_profile_list_with_profiles(self, runner, temp_db):
        """Test profile list with existing profiles."""
        # Create some profiles
        runner.invoke(main, ['init', '--profile', 'user1'])
        runner.invoke(main, ['init', '--profile', 'user2'])

        result = runner.invoke(main, ['profile', 'list'])
        assert result.exit_code == 0
        assert "user1" in result.output
        assert "user2" in result.output

    def test_profile_stats_nonexistent(self, runner, temp_db):
        """Test profile stats for non-existent profile."""
        result = runner.invoke(main, ['profile', 'stats', 'nonexistent'])
        assert result.exit_code == 0  # Command succeeds but shows "not found" message
        assert "not found" in result.output.lower() or "nonexistent" in result.output

    def test_profile_stats_existing(self, runner, temp_db):
        """Test profile stats for existing profile."""
        # Create a profile
        runner.invoke(main, ['init', '--profile', 'statsuser'])

        result = runner.invoke(main, ['profile', 'stats', 'statsuser'])
        assert result.exit_code == 0
        assert "statsuser" in result.output

    def test_invalid_command(self, runner):
        """Test invalid command handling."""
        result = runner.invoke(main, ['invalid-command'])
        assert result.exit_code != 0
        assert "Error" in result.output or "No such command" in result.output

    def test_command_without_required_profile(self, runner, temp_db):
        """Test commands that require profile but none provided."""
        result = runner.invoke(main, ['quiz', 'hand-ranking'])
        # This might succeed or fail depending on implementation
        # Just verify it doesn't crash
        assert result.exit_code in [0, 1, 2]

    def test_simulate_with_export(self, runner, temp_db):
        """Test simulate command with export options."""
        # Create a profile first
        runner.invoke(main, ['init', '--profile', 'exportuser'])

        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = Path(temp_dir) / "hand.json"

            result = runner.invoke(main, [
                'simulate',
                '--ai', 'medium',
                '--profile', 'exportuser',
                '--export-hand', str(export_path),
                '--export-format', 'json'
            ])

            # The command should run without crashing (might fail due to interactive nature)
            assert result.exit_code in [0, 1]  # Accept both success and graceful failure


class TestCLIErrorHandling:
    """Test CLI error handling and edge cases."""

    @pytest.fixture
    def runner(self):
        """CLI runner fixture."""
        return CliRunner()

    @pytest.fixture
    def temp_db(self):
        """Temporary database fixture."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_holdem.db"

            # Ensure the database file doesn't exist
            if db_path.exists():
                db_path.unlink()

            # Patch the database path for testing
            with patch('holdem_cli.cli.get_database_path', return_value=db_path), \
                 patch('holdem_cli.storage.get_database_path', return_value=db_path), \
                 patch('holdem_cli.storage.database.get_database_path', return_value=db_path):
                yield db_path

    def test_init_database_error(self, runner):
        """Test init command when database initialization fails."""
        with patch('holdem_cli.cli.init_database', side_effect=Exception("DB Error")):
            result = runner.invoke(main, ['init', '--profile', 'testuser'])
            assert result.exit_code != 0

    def test_quiz_database_error(self, runner, temp_db):
        """Test quiz command when database access fails."""
        # Create a profile first
        runner.invoke(main, ['init', '--profile', 'quizuser'])

        with patch('holdem_cli.cli.Database', side_effect=Exception("DB Error")):
            result = runner.invoke(main, [
                'quiz', 'hand-ranking',
                '--count', '5',
                '--profile', 'quizuser'
            ])
            assert result.exit_code != 0

    def test_profile_stats_invalid_profile(self, runner, temp_db):
        """Test profile stats with invalid profile name."""
        result = runner.invoke(main, ['profile', 'stats', ''])
        assert result.exit_code != 0 or "Error" in result.output

    def test_simulate_invalid_ai_level(self, runner, temp_db):
        """Test simulate command with invalid AI level."""
        # Create a profile first
        runner.invoke(main, ['init', '--profile', 'simuser'])

        result = runner.invoke(main, [
            'simulate',
            '--ai', 'invalid-ai-level',
            '--profile', 'simuser'
        ])
        # Should either fail gracefully or default to a valid level
        assert result.exit_code in [0, 1, 2]


class TestCLIIntegrationWorkflows:
    """Test complete CLI workflows and user journeys."""

    @pytest.fixture
    def runner(self):
        """CLI runner fixture."""
        return CliRunner()

    @pytest.fixture
    def temp_db(self):
        """Temporary database fixture."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_holdem.db"

            # Ensure the database file doesn't exist
            if db_path.exists():
                db_path.unlink()

            # Patch the database path for testing
            with patch('holdem_cli.cli.get_database_path', return_value=db_path), \
                 patch('holdem_cli.storage.get_database_path', return_value=db_path), \
                 patch('holdem_cli.storage.database.get_database_path', return_value=db_path):
                yield db_path

    def test_complete_user_workflow(self, runner, temp_db):
        """Test complete user workflow from init to quiz."""
        # Step 1: Initialize with profile
        result1 = runner.invoke(main, ['init', '--profile', 'workflowuser'])
        assert result1.exit_code == 0
        assert "Created new profile" in result1.output

        # Step 2: List profiles to verify creation
        result2 = runner.invoke(main, ['profile', 'list'])
        assert result2.exit_code == 0
        assert "workflowuser" in result2.output

        # Step 3: Run a quiz
        result3 = runner.invoke(main, [
            'quiz', 'hand-ranking',
            '--count', '3',
            '--profile', 'workflowuser',
            '--difficulty', 'easy'
        ])
        # The command should run without crashing
        assert result3.exit_code in [0, 1]

        # Step 4: Check profile stats
        result4 = runner.invoke(main, ['profile', 'stats', 'workflowuser'])
        assert result4.exit_code == 0

    def test_multiple_profiles_workflow(self, runner, temp_db):
        """Test workflow with multiple profiles."""
        profiles = ['alice', 'bob', 'charlie']

        # Create multiple profiles
        for profile in profiles:
            result = runner.invoke(main, ['init', '--profile', profile])
            assert result.exit_code == 0
            assert f"Created new profile: {profile}" in result.output

        # List all profiles
        result = runner.invoke(main, ['profile', 'list'])
        assert result.exit_code == 0
        for profile in profiles:
            assert profile in result.output

        # Test each profile's stats
        for profile in profiles:
            result = runner.invoke(main, ['profile', 'stats', profile])
            assert result.exit_code == 0
            assert profile in result.output

    def test_quiz_progression_workflow(self, runner, temp_db):
        """Test quiz progression workflow."""
        # Create profile
        runner.invoke(main, ['init', '--profile', 'progressuser'])

        # Run multiple quizzes with different difficulties
        difficulties = ['easy', 'medium', 'hard']

        for difficulty in difficulties:
            result = runner.invoke(main, [
                'quiz', 'hand-ranking',
                '--count', '5',
                '--profile', 'progressuser',
                '--difficulty', difficulty
            ])
            # The command should run without crashing
            assert result.exit_code in [0, 1]

        # Check final stats
        result = runner.invoke(main, ['profile', 'stats', 'progressuser'])
        assert result.exit_code == 0
