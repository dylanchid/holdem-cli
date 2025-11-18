"""
Tests for chart services (chart_service, navigation_service, ui_service).

This module tests the service layer for chart-related operations.
"""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from test_utils import setup_test_imports
setup_test_imports()

from holdem_cli.services.charts.chart_service import (
    ChartService, ChartMetadata, get_chart_service, reset_chart_service
)
from holdem_cli.services.charts.navigation_service import (
    NavigationService, NavigationState, NavigationContext,
    NavigationMode, Direction, get_navigation_service, reset_navigation_service
)
from holdem_cli.services.charts.ui_service import (
    UIService, UIState, Notification, Dialog, NotificationType, DialogType,
    get_ui_service, reset_ui_service
)
from holdem_cli.charts.tui.widgets.matrix import HandAction, ChartAction, create_sample_range


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def chart_service():
    """Create a chart service for testing."""
    reset_chart_service()
    return ChartService()


@pytest.fixture
def navigation_service():
    """Create a navigation service for testing."""
    reset_navigation_service()
    return NavigationService()


@pytest.fixture
def ui_service():
    """Create a UI service for testing."""
    reset_ui_service()
    return UIService()


@pytest.fixture
def sample_actions():
    """Create sample chart actions."""
    return {
        "AA": HandAction(action=ChartAction.RAISE, frequency=1.0, ev=2.5, notes="Premium"),
        "KK": HandAction(action=ChartAction.RAISE, frequency=1.0, ev=2.0, notes="Premium"),
        "QQ": HandAction(action=ChartAction.RAISE, frequency=0.9, ev=1.5, notes="Strong"),
        "AKs": HandAction(action=ChartAction.RAISE, frequency=0.8, ev=1.0, notes="Suited"),
        "72o": HandAction(action=ChartAction.FOLD, frequency=1.0, ev=-0.5, notes="Trash"),
    }


# =============================================================================
# ChartMetadata Tests
# =============================================================================

class TestChartMetadata:
    def test_metadata_creation(self):
        metadata = ChartMetadata(
            id="test-123",
            name="Test Chart",
            description="Test description",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            version="1.0",
            tags=["test"],
            statistics={"total_hands": 5}
        )
        assert metadata.id == "test-123"
        assert metadata.name == "Test Chart"
        assert metadata.version == "1.0"


# =============================================================================
# ChartService Tests
# =============================================================================

class TestChartService:
    def test_initialization(self, chart_service):
        assert chart_service is not None
        assert chart_service.db is None

    def test_validate_chart_data_valid(self, chart_service, sample_actions):
        is_valid, errors = chart_service.validate_chart_data(sample_actions)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_chart_data_empty(self, chart_service):
        is_valid, errors = chart_service.validate_chart_data({})
        assert is_valid is False
        assert len(errors) > 0

    def test_analyze_chart_statistics(self, chart_service, sample_actions):
        stats = chart_service.analyze_chart_statistics(sample_actions)
        assert stats is not None
        assert 'total_hands' in stats
        assert stats['total_hands'] == 5

    def test_analyze_chart_statistics_actions(self, chart_service, sample_actions):
        stats = chart_service.analyze_chart_statistics(sample_actions)
        # Check for action distribution in statistics
        assert 'action_distribution' in stats or 'actions' in stats
        if 'action_distribution' in stats:
            action_count = sum(stats['action_distribution'].values())
        else:
            action_count = sum(stats['actions'].values())
        assert action_count == 5

    def test_search_charts_empty(self, chart_service):
        results = chart_service.search_charts("test")
        assert results == []

    def test_generate_chart_id(self, chart_service, sample_actions):
        chart_id = chart_service._generate_chart_id("Test Chart", sample_actions)
        assert chart_id is not None
        assert len(chart_id) == 8  # MD5 hash truncated to 8 chars


class TestChartServiceImport:
    def test_import_file_not_found(self, chart_service):
        with pytest.raises(FileNotFoundError):
            chart_service.import_chart("/nonexistent/file.json", "json")

    def test_import_json_internal(self, chart_service):
        # Test the internal import method directly
        import json
        test_data = {
            "ranges": {
                "AA": {"action": "raise", "frequency": 1.0},
                "KK": {"action": "raise", "frequency": 1.0}
            }
        }

        with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode='w') as f:
            json.dump(test_data, f)
            filepath = f.name

        try:
            actions = chart_service._import_json(Path(filepath))
            assert "AA" in actions
            assert "KK" in actions
            assert actions["AA"].action == ChartAction.RAISE
        finally:
            os.unlink(filepath)

    def test_import_csv_internal(self, chart_service):
        # Test the internal CSV import method
        csv_content = "Hand,Action,Frequency,EV,Notes\nAA,raise,1.0,,Premium\nKK,raise,1.0,,Premium"

        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode='w') as f:
            f.write(csv_content)
            filepath = f.name

        try:
            actions = chart_service._import_csv(Path(filepath))
            assert "AA" in actions
            assert actions["AA"].action == ChartAction.RAISE
        finally:
            os.unlink(filepath)

    def test_import_txt_internal(self, chart_service):
        # Test the internal txt import method
        txt_content = "AA raise 1.0\nKK raise 1.0\n72o fold 1.0"

        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w') as f:
            f.write(txt_content)
            filepath = f.name

        try:
            actions = chart_service._import_txt(Path(filepath))
            assert "AA" in actions
            assert "72o" in actions
            assert actions["72o"].action == ChartAction.FOLD
        finally:
            os.unlink(filepath)


class TestChartServiceComparison:
    def test_calculate_similarity_identical(self, chart_service):
        actions = create_sample_range()
        similarity = chart_service._calculate_similarity(actions, actions)
        assert similarity == 1.0

    def test_calculate_similarity_different(self, chart_service, sample_actions):
        actions1 = sample_actions
        actions2 = {
            "AA": HandAction(action=ChartAction.FOLD, frequency=1.0),
            "KK": HandAction(action=ChartAction.FOLD, frequency=1.0),
        }
        similarity = chart_service._calculate_similarity(actions1, actions2)
        assert 0 <= similarity <= 1

    def test_analyze_differences(self, chart_service, sample_actions):
        actions1 = sample_actions
        actions2 = {
            "AA": HandAction(action=ChartAction.FOLD, frequency=1.0),  # Different
            "22": HandAction(action=ChartAction.RAISE, frequency=1.0),  # Only in 2
        }
        differences = chart_service._analyze_differences(actions1, actions2)
        assert 'only_in_chart1' in differences
        assert 'only_in_chart2' in differences
        assert 'different_actions' in differences


class TestGlobalChartService:
    def test_get_chart_service(self):
        reset_chart_service()
        service = get_chart_service()
        assert service is not None
        assert isinstance(service, ChartService)

        # Same instance
        service2 = get_chart_service()
        assert service is service2

        reset_chart_service()


# =============================================================================
# NavigationService Tests
# =============================================================================

class TestNavigationState:
    def test_default_state(self):
        state = NavigationState()
        assert state.mode == NavigationMode.MATRIX
        assert state.current_position == (0, 0)
        assert state.view_mode == "range"
        assert state.search_active is False

    def test_reset_search(self):
        state = NavigationState()
        state.search_active = True
        state.search_query = "test"
        state.search_results = ["AA", "KK"]
        state.search_index = 1

        state.reset_search()

        assert state.search_active is False
        assert state.search_query == ""
        assert state.search_results == []
        assert state.search_index == -1

    def test_next_search_result(self):
        state = NavigationState()
        state.search_results = ["AA", "KK", "QQ"]
        state.search_index = 0

        result = state.next_search_result()
        assert result == "KK"
        assert state.search_index == 1

        result = state.next_search_result()
        assert result == "QQ"

        # Wrap around
        result = state.next_search_result()
        assert result == "AA"

    def test_previous_search_result(self):
        state = NavigationState()
        state.search_results = ["AA", "KK", "QQ"]
        state.search_index = 2

        result = state.previous_search_result()
        assert result == "KK"

        # Wrap around
        state.search_index = 0
        result = state.previous_search_result()
        assert result == "QQ"


class TestNavigationService:
    def test_initialization(self, navigation_service):
        assert navigation_service is not None
        assert navigation_service.state is not None
        assert navigation_service.context is not None

    def test_navigate_matrix_up(self, navigation_service):
        new_pos = navigation_service.navigate_matrix(Direction.UP, 5, 5)
        assert new_pos == (4, 5)

    def test_navigate_matrix_down(self, navigation_service):
        new_pos = navigation_service.navigate_matrix(Direction.DOWN, 5, 5)
        assert new_pos == (6, 5)

    def test_navigate_matrix_left(self, navigation_service):
        new_pos = navigation_service.navigate_matrix(Direction.LEFT, 5, 5)
        assert new_pos == (5, 4)

    def test_navigate_matrix_right(self, navigation_service):
        new_pos = navigation_service.navigate_matrix(Direction.RIGHT, 5, 5)
        assert new_pos == (5, 6)

    def test_navigate_matrix_bounds_top(self, navigation_service):
        new_pos = navigation_service.navigate_matrix(Direction.UP, 0, 5)
        assert new_pos == (0, 5)  # Can't go above 0

    def test_navigate_matrix_bounds_bottom(self, navigation_service):
        new_pos = navigation_service.navigate_matrix(Direction.DOWN, 12, 5)
        assert new_pos == (12, 5)  # Can't go below 12

    def test_navigate_matrix_bounds_left(self, navigation_service):
        new_pos = navigation_service.navigate_matrix(Direction.LEFT, 5, 0)
        assert new_pos == (5, 0)  # Can't go left of 0

    def test_navigate_matrix_bounds_right(self, navigation_service):
        new_pos = navigation_service.navigate_matrix(Direction.RIGHT, 5, 12)
        assert new_pos == (5, 12)  # Can't go right of 12

    def test_jump_to_position(self, navigation_service):
        pos = navigation_service.jump_to_position("UTG")
        assert pos == (0, 0)

        pos = navigation_service.jump_to_position("BTN")
        assert pos == (12, 12)

        pos = navigation_service.jump_to_position("INVALID")
        assert pos is None

    def test_cycle_view_mode(self, navigation_service):
        initial_mode = navigation_service.state.view_mode
        new_mode = navigation_service.cycle_view_mode()
        assert new_mode != initial_mode

    def test_perform_search(self, navigation_service, sample_actions):
        results = navigation_service.perform_search("raise", sample_actions, None)
        assert len(results) == 4  # AA, KK, QQ, AKs

    def test_perform_search_hand_name(self, navigation_service, sample_actions):
        results = navigation_service.perform_search("AA", sample_actions, None)
        assert "AA" in results

    def test_perform_search_suited(self, navigation_service, sample_actions):
        results = navigation_service.perform_search("suited", sample_actions, None)
        assert "AKs" in results

    def test_perform_search_empty_query(self, navigation_service, sample_actions):
        results = navigation_service.perform_search("", sample_actions, None)
        assert results == []

    def test_get_navigation_info(self, navigation_service):
        info = navigation_service.get_navigation_info()
        assert 'mode' in info
        assert 'position' in info
        assert 'view_mode' in info
        assert 'context' in info

    def test_register_navigation_handler(self, navigation_service):
        def test_handler():
            pass

        navigation_service.register_navigation_handler("test", test_handler)
        handler = navigation_service.get_navigation_handler("test")
        assert handler is test_handler

    def test_handle_quick_navigation_position(self, navigation_service):
        pos = navigation_service.handle_quick_navigation('1')
        assert pos == (0, 0)  # UTG

        pos = navigation_service.handle_quick_navigation('4')
        assert pos == (12, 12)  # BTN

    def test_handle_quick_navigation_corners(self, navigation_service):
        pos = navigation_service.handle_quick_navigation('home')
        assert pos == (0, 0)

        pos = navigation_service.handle_quick_navigation('end')
        assert pos == (12, 12)

    def test_get_movement_feedback(self, navigation_service):
        action = HandAction(action=ChartAction.RAISE, frequency=0.8)
        feedback = navigation_service.get_movement_feedback((0, 0), (1, 0), "AA", action)
        assert "AA" in feedback
        assert "Raise" in feedback

    def test_get_movement_feedback_no_action(self, navigation_service):
        feedback = navigation_service.get_movement_feedback((0, 0), (1, 0), None, None)
        assert "Position" in feedback

    def test_update_context(self, navigation_service):
        navigation_service.update_context(chart_size=200, visible_rows=20)
        assert navigation_service.context.chart_size == 200
        assert navigation_service.context.visible_rows == 20

    def test_reset_to_defaults(self, navigation_service):
        navigation_service.state.search_active = True
        navigation_service.state.view_mode = "ev"

        navigation_service.reset_to_defaults()

        assert navigation_service.state.search_active is False
        assert navigation_service.state.view_mode == "range"

    def test_get_statistics(self, navigation_service):
        stats = navigation_service.get_statistics()
        assert 'navigation_mode' in stats
        assert 'registered_handlers' in stats


class TestNavigationServiceSearch:
    def test_is_connector(self, navigation_service):
        assert navigation_service._is_connector("JT") is True
        assert navigation_service._is_connector("98") is True
        assert navigation_service._is_connector("AK") is True
        assert navigation_service._is_connector("A2") is False

    def test_is_premium_hand(self, navigation_service):
        assert navigation_service._is_premium_hand("AA") is True
        assert navigation_service._is_premium_hand("KK") is True
        assert navigation_service._is_premium_hand("AKs") is True
        assert navigation_service._is_premium_hand("72o") is False


class TestGlobalNavigationService:
    def test_get_navigation_service(self):
        reset_navigation_service()
        service = get_navigation_service()
        assert service is not None
        assert isinstance(service, NavigationService)

        service2 = get_navigation_service()
        assert service is service2

        reset_navigation_service()


# =============================================================================
# UIService Tests
# =============================================================================

class TestNotification:
    def test_notification_creation(self):
        notification = Notification(
            message="Test message",
            type=NotificationType.INFO
        )
        assert notification.message == "Test message"
        assert notification.type == NotificationType.INFO
        assert notification.dismissed is False

    def test_notification_dismiss(self):
        notification = Notification(message="Test")
        notification.dismiss()
        assert notification.dismissed is True


class TestDialog:
    def test_dialog_creation(self):
        dialog = Dialog(
            type=DialogType.HELP,
            title="Help",
            content="Help content"
        )
        assert dialog.type == DialogType.HELP
        assert dialog.title == "Help"
        assert dialog.buttons == ["OK"]


class TestUIState:
    def test_default_state(self):
        state = UIState()
        assert state.notifications == []
        assert state.active_dialog is None
        assert state.loading is False
        assert state.current_screen == "main"

    def test_add_notification(self):
        state = UIState()
        notification = Notification(message="Test")
        state.add_notification(notification)
        assert len(state.notifications) == 1

    def test_add_notification_limit(self):
        state = UIState()
        # Add more than 10 notifications
        for i in range(15):
            state.add_notification(Notification(message=f"Test {i}"))
        assert len(state.notifications) == 10

    def test_dismiss_notification(self):
        state = UIState()
        state.add_notification(Notification(message="Test"))
        state.dismiss_notification(0)
        assert state.notifications[0].dismissed is True

    def test_clear_dismissed_notifications(self):
        state = UIState()
        n1 = Notification(message="Keep")
        n2 = Notification(message="Dismiss")
        state.add_notification(n1)
        state.add_notification(n2)
        state.dismiss_notification(1)
        state.clear_dismissed_notifications()
        assert len(state.notifications) == 1
        assert state.notifications[0].message == "Keep"

    def test_set_loading(self):
        state = UIState()
        state.set_loading(True, "Loading...")
        assert state.loading is True
        assert state.loading_message == "Loading..."

    def test_set_progress(self):
        state = UIState()
        state.set_progress(0.5, "Halfway")
        assert state.progress == 0.5
        assert state.status_message == "Halfway"

    def test_set_progress_bounds(self):
        state = UIState()
        state.set_progress(1.5)  # Over 1.0
        assert state.progress == 1.0

        state.set_progress(-0.5)  # Under 0.0
        assert state.progress == 0.0


class TestUIService:
    def test_initialization(self, ui_service):
        assert ui_service is not None
        assert ui_service.state is not None

    def test_register_ui_handler(self, ui_service):
        def handler():
            pass

        ui_service.register_ui_handler("test", handler)
        assert ui_service.get_ui_handler("test") is handler

    def test_register_notification_handler(self, ui_service):
        def handler(notification):
            pass

        ui_service.register_notification_handler(NotificationType.ERROR, handler)
        assert NotificationType.ERROR in ui_service._notification_handlers

    def test_get_ui_state(self, ui_service):
        state = ui_service.get_ui_state()
        assert 'current_screen' in state
        assert 'loading' in state
        assert 'progress' in state

    def test_create_feedback_message_success(self, ui_service):
        message = ui_service.create_feedback_message("Save", True, "File saved")
        assert "succeeded" in message
        assert "File saved" in message

    def test_create_feedback_message_failure(self, ui_service):
        message = ui_service.create_feedback_message("Save", False)
        assert "failed" in message

    def test_handle_error_feedback_custom(self, ui_service):
        error = ValueError("Test error")
        message = ui_service.handle_error_feedback(error, "save", "Custom error")
        assert "Custom error" in message

    def test_handle_error_feedback_auto(self, ui_service):
        error = FileNotFoundError("Not found")
        message = ui_service.handle_error_feedback(error, "load")
        assert "File not found" in message

    def test_handle_error_feedback_permission(self, ui_service):
        error = PermissionError("Permission denied")
        message = ui_service.handle_error_feedback(error, "write")
        assert "Permission denied" in message

    def test_handle_error_feedback_value(self, ui_service):
        error = ValueError("Invalid value")
        message = ui_service.handle_error_feedback(error, "parse")
        assert "Invalid input" in message

    def test_get_default_help_content(self, ui_service):
        help_content = ui_service._get_default_help_content()
        assert "Navigation" in help_content
        assert "Help" in help_content

    def test_get_active_notifications_empty(self, ui_service):
        active = ui_service.get_active_notifications()
        assert active == []

    def test_state_notifications_directly(self, ui_service):
        # Test state management directly without event bus
        notification = Notification(message="Test", type=NotificationType.INFO)
        ui_service.state.add_notification(notification)
        assert len(ui_service.state.notifications) == 1

        ui_service.state.dismiss_notification(0)
        assert ui_service.state.notifications[0].dismissed is True

        ui_service.state.clear_dismissed_notifications()
        assert len(ui_service.state.notifications) == 0

    def test_state_loading_directly(self, ui_service):
        # Test loading state directly
        ui_service.state.set_loading(True, "Loading...")
        assert ui_service.state.loading is True
        assert ui_service.state.loading_message == "Loading..."

    def test_state_progress_directly(self, ui_service):
        # Test progress state directly
        ui_service.state.set_progress(0.5, "Halfway")
        assert ui_service.state.progress == 0.5
        assert ui_service.state.status_message == "Halfway"

    def test_clear_all_notifications(self, ui_service):
        # Add notifications directly to state
        ui_service.state.add_notification(Notification(message="Test 1"))
        ui_service.state.add_notification(Notification(message="Test 2"))
        ui_service.clear_all_notifications()
        assert len(ui_service.state.notifications) == 0


class TestGlobalUIService:
    def test_get_ui_service(self):
        reset_ui_service()
        service = get_ui_service()
        assert service is not None
        assert isinstance(service, UIService)

        service2 = get_ui_service()
        assert service is service2

        reset_ui_service()


# =============================================================================
# Integration Tests
# =============================================================================

class TestServicesIntegration:
    def test_services_work_together(self, chart_service, navigation_service, ui_service, sample_actions):
        """Test that services can work together in a typical workflow."""
        # 1. Analyze chart
        stats = chart_service.analyze_chart_statistics(sample_actions)
        assert stats['total_hands'] == 5

        # 2. Search for hands
        results = navigation_service.perform_search("raise", sample_actions, None)
        assert len(results) > 0

        # 3. Navigate to first result
        navigation_service.state.search_index = 0
        first_result = navigation_service.state.search_results[0]

        # 4. Create feedback message (without event bus)
        action = sample_actions.get(first_result)
        if action:
            message = ui_service.create_feedback_message(
                f"Found {first_result}",
                True,
                action.action.value
            )
            assert first_result in message
            assert "succeeded" in message

    def test_chart_validation_and_statistics(self, chart_service, sample_actions):
        """Test chart validation followed by statistics analysis."""
        # Validate chart
        is_valid, errors = chart_service.validate_chart_data(sample_actions)
        assert is_valid is True

        # Get statistics
        stats = chart_service.analyze_chart_statistics(sample_actions)
        assert stats['total_hands'] == len(sample_actions)

    def test_navigation_search_workflow(self, navigation_service, sample_actions):
        """Test complete search workflow."""
        # Perform search
        results = navigation_service.perform_search("raise", sample_actions, None)
        assert len(results) > 0

        # Navigate through results
        first = navigation_service.state.next_search_result()
        assert first is not None

        second = navigation_service.state.next_search_result()
        assert second is not None
        assert second != first

        # Reset search
        navigation_service.state.reset_search()
        assert navigation_service.state.search_active is False
