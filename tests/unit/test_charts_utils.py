"""Tests for charts utility functions."""

import pytest
from unittest.mock import patch, MagicMock

from holdem_cli.charts.utils import (
    run_chart_viewer,
    launch_interactive_chart_viewer,
    launch_chart_quiz,
)
from holdem_cli.types import HandAction, ChartAction


class TestRunChartViewer:
    """Tests for run_chart_viewer function."""

    @patch('holdem_cli.charts.utils.ChartViewerApp')
    def test_run_chart_viewer_default(self, mock_app_class):
        """Test running chart viewer with default chart name."""
        mock_app = MagicMock()
        mock_app_class.return_value = mock_app

        run_chart_viewer()

        mock_app_class.assert_called_once_with("Sample Chart")
        mock_app.run.assert_called_once()

    @patch('holdem_cli.charts.utils.ChartViewerApp')
    def test_run_chart_viewer_custom_name(self, mock_app_class):
        """Test running chart viewer with custom chart name."""
        mock_app = MagicMock()
        mock_app_class.return_value = mock_app

        run_chart_viewer("My Custom Chart")

        mock_app_class.assert_called_once_with("My Custom Chart")
        mock_app.run.assert_called_once()


class TestLaunchInteractiveChartViewer:
    """Tests for launch_interactive_chart_viewer function."""

    @patch('holdem_cli.charts.utils.ChartViewerApp')
    @patch('holdem_cli.charts.utils.create_sample_range')
    def test_launch_with_defaults(self, mock_sample, mock_app_class):
        """Test launching with default parameters."""
        mock_app = MagicMock()
        mock_app_class.return_value = mock_app
        mock_sample.return_value = {'AA': HandAction(ChartAction.RAISE, 1.0)}

        launch_interactive_chart_viewer()

        mock_sample.assert_called_once()
        mock_app_class.assert_called_once_with("Interactive Chart")
        mock_app.run.assert_called_once()

    @patch('holdem_cli.charts.utils.ChartViewerApp')
    def test_launch_with_custom_data(self, mock_app_class):
        """Test launching with custom chart data."""
        mock_app = MagicMock()
        mock_app_class.return_value = mock_app

        custom_data = {'KK': HandAction(ChartAction.RAISE, 1.0)}

        launch_interactive_chart_viewer(chart_name="Test Chart", chart_data=custom_data)

        mock_app_class.assert_called_once_with("Test Chart")
        assert mock_app.current_chart == custom_data
        mock_app.run.assert_called_once()


class TestLaunchChartQuiz:
    """Tests for launch_chart_quiz function."""

    @patch('holdem_cli.charts.utils.ChartQuizApp')
    @patch('holdem_cli.charts.utils.create_sample_range')
    def test_launch_quiz_with_defaults(self, mock_sample, mock_quiz_class):
        """Test launching quiz with default sample chart."""
        mock_quiz = MagicMock()
        mock_quiz_class.return_value = mock_quiz
        mock_sample.return_value = {'AA': HandAction(ChartAction.RAISE, 1.0)}

        launch_chart_quiz()

        mock_sample.assert_called_once()
        mock_quiz_class.assert_called_once()
        mock_quiz.run.assert_called_once()

    @patch('holdem_cli.charts.utils.ChartQuizApp')
    def test_launch_quiz_with_custom_data(self, mock_quiz_class):
        """Test launching quiz with custom chart data."""
        mock_quiz = MagicMock()
        mock_quiz_class.return_value = mock_quiz

        custom_data = {'KK': HandAction(ChartAction.RAISE, 1.0)}

        launch_chart_quiz(custom_data)

        mock_quiz_class.assert_called_once_with(custom_data)
        mock_quiz.run.assert_called_once()


class TestDemoFunctions:
    """Tests for demo functions."""

    @patch('holdem_cli.charts.utils.run_chart_viewer')
    @patch('holdem_cli.charts.utils.create_sample_range')
    @patch('signal.signal')
    def test_demo_tui_runs_viewer(self, mock_signal, mock_sample, mock_viewer):
        """Test that demo_tui runs the chart viewer."""
        from holdem_cli.charts.utils import demo_tui

        mock_sample.return_value = {'AA': HandAction(ChartAction.RAISE, 1.0)}

        demo_tui()

        mock_viewer.assert_called_once_with("Demo Chart")

    @patch('holdem_cli.charts.utils.run_chart_viewer')
    @patch('holdem_cli.charts.utils.create_sample_range')
    @patch('signal.signal')
    def test_demo_tui_handles_keyboard_interrupt(self, mock_signal, mock_sample, mock_viewer):
        """Test that demo_tui handles keyboard interrupt."""
        from holdem_cli.charts.utils import demo_tui

        mock_sample.return_value = {'AA': HandAction(ChartAction.RAISE, 1.0)}
        mock_viewer.side_effect = KeyboardInterrupt()

        # Should not raise
        demo_tui()

    @patch('holdem_cli.charts.utils.ChartQuizApp')
    @patch('holdem_cli.charts.utils.create_sample_range')
    def test_demo_quiz_runs_quiz(self, mock_sample, mock_quiz_class):
        """Test that demo_quiz runs the quiz app."""
        from holdem_cli.charts.utils import demo_quiz

        mock_quiz = MagicMock()
        mock_quiz_class.return_value = mock_quiz
        mock_sample.return_value = {'AA': HandAction(ChartAction.RAISE, 1.0)}

        demo_quiz()

        mock_quiz_class.assert_called_once()
        mock_quiz.run.assert_called_once()


class TestReExports:
    """Tests for re-exported functions from submodules."""

    def test_loader_functions_available(self):
        """Test that loader functions are re-exported."""
        from holdem_cli.charts.utils import (
            create_chart_from_file,
            load_json_chart,
            load_simple_chart,
            load_pio_chart,
            load_gto_wizard_chart,
        )

        # Just verify they're callable
        assert callable(create_chart_from_file)
        assert callable(load_json_chart)
        assert callable(load_simple_chart)
        assert callable(load_pio_chart)
        assert callable(load_gto_wizard_chart)

    def test_operation_functions_available(self):
        """Test that operation functions are re-exported."""
        from holdem_cli.charts.utils import (
            merge_charts,
            filter_chart_by_action,
            filter_chart_by_frequency,
            get_chart_statistics,
            export_chart_statistics,
            validate_chart,
            save_chart_to_db,
            load_chart_from_db,
        )

        # Just verify they're callable
        assert callable(merge_charts)
        assert callable(filter_chart_by_action)
        assert callable(filter_chart_by_frequency)
        assert callable(get_chart_statistics)
        assert callable(export_chart_statistics)
        assert callable(validate_chart)
        assert callable(save_chart_to_db)
        assert callable(load_chart_from_db)


class TestBackwardsCompatibility:
    """Tests for backwards compatibility aliases."""

    def test_private_aliases_exist(self):
        """Test that private function aliases are still available."""
        from holdem_cli.charts.utils import (
            _load_json_chart,
            _load_simple_chart,
            _load_pio_chart,
            _load_gto_wizard_chart,
        )

        # Verify aliases point to the same functions
        from holdem_cli.charts.utils import (
            load_json_chart,
            load_simple_chart,
            load_pio_chart,
            load_gto_wizard_chart,
        )

        assert _load_json_chart is load_json_chart
        assert _load_simple_chart is load_simple_chart
        assert _load_pio_chart is load_pio_chart
        assert _load_gto_wizard_chart is load_gto_wizard_chart
