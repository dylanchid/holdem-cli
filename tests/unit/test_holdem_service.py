"""Tests for the unified HoldemService."""

import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from holdem_cli.services.holdem_service import HoldemService, get_holdem_service
from holdem_cli.types import HandAction, ChartAction


class TestHoldemServiceInit:
    """Tests for HoldemService initialization."""

    @patch('holdem_cli.services.holdem_service.init_database')
    def test_init_creates_database(self, mock_init_db):
        """Test that service initializes database on creation."""
        mock_db = MagicMock()
        mock_init_db.return_value = mock_db

        service = HoldemService()

        mock_init_db.assert_called_once()
        assert service.db == mock_db

    @patch('holdem_cli.services.holdem_service.init_database')
    def test_context_manager_entry(self, mock_init_db):
        """Test context manager entry returns service."""
        mock_db = MagicMock()
        mock_init_db.return_value = mock_db

        with HoldemService() as service:
            assert isinstance(service, HoldemService)

    @patch('holdem_cli.services.holdem_service.init_database')
    def test_context_manager_closes_db(self, mock_init_db):
        """Test context manager closes database on exit."""
        mock_db = MagicMock()
        mock_init_db.return_value = mock_db

        with HoldemService() as service:
            pass

        mock_db.close.assert_called_once()


class TestProfileManagement:
    """Tests for profile management methods."""

    @pytest.fixture
    def service_with_mock_db(self):
        """Create service with mocked database."""
        with patch('holdem_cli.services.holdem_service.init_database') as mock_init:
            mock_db = MagicMock()
            mock_init.return_value = mock_db
            service = HoldemService()
            yield service, mock_db

    def test_create_profile_success(self, service_with_mock_db):
        """Test successful profile creation."""
        service, mock_db = service_with_mock_db
        mock_db.get_user.return_value = None  # User doesn't exist
        mock_db.create_user.return_value = 1

        success, message = service.create_profile("test_user")

        assert success is True
        assert "Successfully created" in message
        mock_db.create_user.assert_called_once_with("test_user")

    def test_create_profile_already_exists(self, service_with_mock_db):
        """Test profile creation when profile already exists."""
        service, mock_db = service_with_mock_db
        mock_db.get_user.return_value = {'id': 1, 'name': 'test_user'}

        success, message = service.create_profile("test_user")

        assert success is False
        assert "already exists" in message

    def test_create_profile_db_failure(self, service_with_mock_db):
        """Test profile creation when database returns None."""
        service, mock_db = service_with_mock_db
        mock_db.get_user.return_value = None
        mock_db.create_user.return_value = None

        success, message = service.create_profile("test_user")

        assert success is False
        assert "Failed to create" in message

    def test_list_profiles(self, service_with_mock_db):
        """Test listing profiles."""
        service, mock_db = service_with_mock_db
        mock_db.list_users.return_value = [
            {'id': 1, 'name': 'user1'},
            {'id': 2, 'name': 'user2'}
        ]

        profiles = service.list_profiles()

        assert len(profiles) == 2
        assert profiles[0]['name'] == 'user1'

    @patch('holdem_cli.services.holdem_service.log_error_and_continue')
    def test_list_profiles_exception(self, mock_log_error, service_with_mock_db):
        """Test listing profiles when exception occurs."""
        service, mock_db = service_with_mock_db
        mock_db.list_users.side_effect = Exception("DB error")

        profiles = service.list_profiles()

        assert profiles == []
        mock_log_error.assert_called_once()

    def test_get_profile_stats_success(self, service_with_mock_db):
        """Test getting profile statistics."""
        service, mock_db = service_with_mock_db
        mock_db.get_user.return_value = {'id': 1, 'name': 'test_user'}
        mock_db.get_user_quiz_stats.return_value = {
            'overall': {'total_sessions': 5},
            'by_type': {}
        }

        stats = service.get_profile_stats("test_user")

        assert stats is not None
        assert stats['overall']['total_sessions'] == 5

    def test_get_profile_stats_user_not_found(self, service_with_mock_db):
        """Test getting stats for non-existent user."""
        service, mock_db = service_with_mock_db
        mock_db.get_user.return_value = None

        stats = service.get_profile_stats("nonexistent")

        assert stats is None


class TestEquityCalculation:
    """Tests for equity calculation methods."""

    @pytest.fixture
    def service_with_mock_db(self):
        """Create service with mocked database."""
        with patch('holdem_cli.services.holdem_service.init_database') as mock_init:
            mock_db = MagicMock()
            mock_init.return_value = mock_db
            service = HoldemService()
            yield service, mock_db

    def test_calculate_equity_success(self, service_with_mock_db):
        """Test successful equity calculation."""
        service, _ = service_with_mock_db

        result = service.calculate_equity("AhKh", "QsQd", iterations=1000)

        assert result['success'] is True
        assert result['hand1'] == "AhKh"
        assert result['hand2'] == "QsQd"
        assert 'equity' in result

    def test_calculate_equity_with_board(self, service_with_mock_db):
        """Test equity calculation with board cards."""
        service, _ = service_with_mock_db

        # Use non-overlapping cards for valid calculation
        result = service.calculate_equity("AhKh", "QsQd", board="Jc7h2c", iterations=1000)

        assert result['success'] is True
        assert result['board'] == "Jc7h2c"

    def test_calculate_equity_invalid_hand(self, service_with_mock_db):
        """Test equity calculation with invalid hand."""
        service, _ = service_with_mock_db

        # Test with invalid input (single card)
        result = service.calculate_equity("Ah", "QsQd", iterations=100)

        assert result['success'] is False
        assert 'error' in result

    def test_calculate_equity_async(self, service_with_mock_db):
        """Test asynchronous equity calculation."""
        import asyncio
        service, _ = service_with_mock_db

        result = asyncio.run(service.calculate_equity_async("AhKh", "QsQd", iterations=1000))

        assert result['success'] is True
        assert 'equity' in result


class TestChartServices:
    """Tests for chart service methods."""

    @pytest.fixture
    def service_with_mock_db(self):
        """Create service with mocked database."""
        with patch('holdem_cli.services.holdem_service.init_database') as mock_init:
            mock_db = MagicMock()
            mock_init.return_value = mock_db
            service = HoldemService()
            yield service, mock_db

    @patch('holdem_cli.services.holdem_service.ChartManager')
    def test_list_charts(self, mock_manager_class, service_with_mock_db):
        """Test listing charts."""
        service, mock_db = service_with_mock_db
        mock_manager = MagicMock()
        mock_manager.list_charts.return_value = [
            {'id': 1, 'name': 'Chart 1'},
            {'id': 2, 'name': 'Chart 2'}
        ]
        mock_manager_class.return_value = mock_manager

        charts = service.list_charts()

        assert len(charts) == 2

    @patch('holdem_cli.services.holdem_service.ChartManager')
    def test_get_chart_success(self, mock_manager_class, service_with_mock_db):
        """Test getting a chart by name."""
        service, mock_db = service_with_mock_db
        mock_manager = MagicMock()
        mock_actions = {
            'AA': HandAction(ChartAction.RAISE, 1.0),
            'KK': HandAction(ChartAction.RAISE, 1.0)
        }
        mock_manager.load_chart_by_name.return_value = mock_actions
        mock_manager_class.return_value = mock_manager

        result = service.get_chart("Test Chart")

        assert result is not None
        assert result['name'] == "Test Chart"
        assert result['hand_count'] == 2

    @patch('holdem_cli.services.holdem_service.ChartManager')
    def test_get_chart_not_found_loads_sample(self, mock_manager_class, service_with_mock_db):
        """Test that sample chart is loaded for known names."""
        service, mock_db = service_with_mock_db
        mock_manager = MagicMock()
        mock_manager.load_chart_by_name.return_value = None
        mock_manager_class.return_value = mock_manager

        result = service.get_chart("sample")

        assert result is not None
        assert result['name'] == "Sample GTO Chart"

    @patch('holdem_cli.services.holdem_service.ChartManager')
    def test_save_chart_success(self, mock_manager_class, service_with_mock_db):
        """Test saving a chart."""
        service, mock_db = service_with_mock_db
        mock_manager = MagicMock()
        mock_manager.save_chart.return_value = 42
        mock_manager_class.return_value = mock_manager

        actions = {'AA': HandAction(ChartAction.RAISE, 1.0)}
        success, message = service.save_chart("Test", "BTN vs BB", actions, 100)

        assert success is True
        assert "42" in message

    @patch('holdem_cli.services.holdem_service.ChartManager')
    def test_export_chart_txt(self, mock_manager_class, service_with_mock_db):
        """Test exporting chart to text format."""
        service, mock_db = service_with_mock_db
        mock_manager = MagicMock()
        mock_actions = {
            'AA': HandAction(ChartAction.RAISE, 1.0)
        }
        mock_manager.load_chart_by_name.return_value = mock_actions
        mock_manager_class.return_value = mock_manager

        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)

                # Mock the HandMatrix export
                with patch('holdem_cli.services.holdem_service.HandMatrix') as mock_matrix:
                    mock_matrix_instance = MagicMock()
                    mock_matrix.return_value = mock_matrix_instance

                    success, message = service.export_chart("Test Chart", format='txt')

                    assert success is True
                    mock_matrix_instance.export_to_text.assert_called_once()
            finally:
                os.chdir(original_cwd)

    @patch('holdem_cli.services.holdem_service.ChartManager')
    def test_export_chart_json(self, mock_manager_class, service_with_mock_db):
        """Test exporting chart to JSON format."""
        service, mock_db = service_with_mock_db
        mock_manager = MagicMock()
        mock_actions = {
            'AA': HandAction(ChartAction.RAISE, 1.0)
        }
        mock_manager.load_chart_by_name.return_value = mock_actions
        mock_manager_class.return_value = mock_manager

        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)

                success, message = service.export_chart("Test Chart", format='json')

                assert success is True
                assert os.path.exists("test_chart.json")

                # Verify JSON content
                with open("test_chart.json") as f:
                    data = json.load(f)
                    assert data['name'] == "Test Chart"
                    assert 'AA' in data['ranges']
            finally:
                os.chdir(original_cwd)

    @patch('holdem_cli.services.holdem_service.ChartManager')
    def test_export_chart_csv(self, mock_manager_class, service_with_mock_db):
        """Test exporting chart to CSV format."""
        service, mock_db = service_with_mock_db
        mock_manager = MagicMock()
        mock_actions = {
            'AA': HandAction(ChartAction.RAISE, 1.0, ev=5.5, notes="Premium")
        }
        mock_manager.load_chart_by_name.return_value = mock_actions
        mock_manager_class.return_value = mock_manager

        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)

                success, message = service.export_chart("Test Chart", format='csv')

                assert success is True
                assert os.path.exists("test_chart.csv")

                # Verify CSV content
                with open("test_chart.csv") as f:
                    content = f.read()
                    assert 'AA' in content
                    assert 'raise' in content
            finally:
                os.chdir(original_cwd)

    @patch('holdem_cli.services.holdem_service.ChartManager')
    def test_export_chart_not_found(self, mock_manager_class, service_with_mock_db):
        """Test exporting non-existent chart."""
        service, mock_db = service_with_mock_db
        mock_manager = MagicMock()
        mock_manager.load_chart_by_name.return_value = None
        mock_manager_class.return_value = mock_manager

        success, message = service.export_chart("NonExistent")

        assert success is False
        assert "not found" in message

    @patch('holdem_cli.services.holdem_service.ChartManager')
    def test_export_chart_invalid_format(self, mock_manager_class, service_with_mock_db):
        """Test exporting with invalid format."""
        service, mock_db = service_with_mock_db
        mock_manager = MagicMock()
        mock_actions = {'AA': HandAction(ChartAction.RAISE, 1.0)}
        mock_manager.load_chart_by_name.return_value = mock_actions
        mock_manager_class.return_value = mock_manager

        success, message = service.export_chart("Test", format='invalid')

        assert success is False
        assert "Unsupported" in message


class TestQuizServices:
    """Tests for quiz service methods."""

    @pytest.fixture
    def service_with_mock_db(self):
        """Create service with mocked database."""
        with patch('holdem_cli.services.holdem_service.init_database') as mock_init:
            mock_db = MagicMock()
            mock_init.return_value = mock_db
            service = HoldemService()
            yield service, mock_db

    @patch('holdem_cli.services.holdem_service.HandRankingQuiz')
    def test_run_hand_ranking_quiz_user_not_found(self, mock_quiz_class, service_with_mock_db):
        """Test quiz returns error when user not found."""
        service, mock_db = service_with_mock_db
        mock_db.get_user.return_value = None

        result = service.run_hand_ranking_quiz("nonexistent", count=5)

        assert result['success'] is False
        assert "not found" in result['error']

    @patch('holdem_cli.services.holdem_service.PotOddsQuiz')
    def test_run_pot_odds_quiz_user_not_found(self, mock_quiz_class, service_with_mock_db):
        """Test pot odds quiz returns error when user not found."""
        service, mock_db = service_with_mock_db
        mock_db.get_user.return_value = None

        result = service.run_pot_odds_quiz("nonexistent", count=5)

        assert result['success'] is False
        assert "not found" in result['error']


class TestSimulationServices:
    """Tests for simulation service methods."""

    @pytest.fixture
    def service_with_mock_db(self):
        """Create service with mocked database."""
        with patch('holdem_cli.services.holdem_service.init_database') as mock_init:
            mock_db = MagicMock()
            mock_init.return_value = mock_db
            service = HoldemService()
            yield service, mock_db

    @patch('holdem_cli.services.holdem_service.PokerSimulator')
    def test_run_simulation_user_not_found(self, mock_sim_class, service_with_mock_db):
        """Test simulation returns error when user not found."""
        service, mock_db = service_with_mock_db
        mock_db.get_user.return_value = None

        result = service.run_simulation("nonexistent")

        assert result['success'] is False
        assert "not found" in result['error']


class TestGetHoldemService:
    """Tests for the convenience function."""

    @patch('holdem_cli.services.holdem_service.init_database')
    def test_get_holdem_service_returns_instance(self, mock_init_db):
        """Test that get_holdem_service returns a HoldemService instance."""
        mock_db = MagicMock()
        mock_init_db.return_value = mock_db

        service = get_holdem_service()

        assert isinstance(service, HoldemService)


class TestCreateSampleChart:
    """Tests for sample chart creation."""

    @pytest.fixture
    def service_with_mock_db(self):
        """Create service with mocked database."""
        with patch('holdem_cli.services.holdem_service.init_database') as mock_init:
            mock_db = MagicMock()
            mock_init.return_value = mock_db
            service = HoldemService()
            yield service, mock_db

    @patch('holdem_cli.services.holdem_service.ChartManager')
    @patch('holdem_cli.services.holdem_service.create_sample_range')
    def test_create_sample_chart_for_new_user(self, mock_create_sample, mock_manager_class, service_with_mock_db):
        """Test sample chart creation for new users."""
        service, mock_db = service_with_mock_db
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        mock_create_sample.return_value = {'AA': HandAction(ChartAction.RAISE, 1.0)}

        service._create_sample_chart_for_new_user()

        mock_manager.save_chart.assert_called_once()
        call_args = mock_manager.save_chart.call_args
        assert call_args[0][0] == "Sample GTO Chart"

    @patch('holdem_cli.services.holdem_service.log_error_and_continue')
    @patch('holdem_cli.services.holdem_service.ChartManager')
    def test_create_sample_chart_handles_exception(self, mock_manager_class, mock_log_error, service_with_mock_db):
        """Test that sample chart creation handles exceptions gracefully."""
        service, mock_db = service_with_mock_db
        mock_manager = MagicMock()
        mock_manager.save_chart.side_effect = Exception("DB error")
        mock_manager_class.return_value = mock_manager

        # Should not raise exception
        service._create_sample_chart_for_new_user()

        mock_log_error.assert_called_once()
