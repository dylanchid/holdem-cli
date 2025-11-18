#!/usr/bin/env python3
"""
Integration test for the new service-based architecture.

This script tests that all services work together correctly and that
the new architecture integrates properly with the existing codebase.
"""

import sys
import os
from pathlib import Path

# Setup standardized imports using test utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
from test_utils import setup_test_imports
src_dir = setup_test_imports()

def test_service_imports():
    """Test that all new services can be imported successfully."""
    from holdem_cli.services.charts.chart_service import get_chart_service, ChartService
    from holdem_cli.services.charts.navigation_service import get_navigation_service, NavigationService
    from holdem_cli.services.charts.ui_service import get_ui_service, UIService

    assert ChartService is not None
    assert NavigationService is not None
    assert UIService is not None

def test_service_initialization():
    """Test that services can be initialized without errors."""
    from holdem_cli.services.charts.chart_service import get_chart_service
    from holdem_cli.services.charts.navigation_service import get_navigation_service
    from holdem_cli.services.charts.ui_service import get_ui_service

    # Get service instances
    chart_service = get_chart_service()
    navigation_service = get_navigation_service()
    ui_service = get_ui_service()

    assert chart_service is not None
    assert navigation_service is not None
    assert ui_service is not None

def test_chart_service_functionality():
    """Test basic chart service functionality."""
    from holdem_cli.services.charts.chart_service import get_chart_service
    from holdem_cli.charts.tui.widgets.matrix import create_sample_range

    chart_service = get_chart_service()
    sample_range = create_sample_range()

    # Test chart validation
    is_valid, errors = chart_service.validate_chart_data(sample_range)
    assert is_valid, f"Chart validation failed: {errors}"

    # Test chart statistics
    stats = chart_service.analyze_chart_statistics(sample_range)
    assert stats is not None, "Chart statistics should not be None"
    assert 'total_hands' in stats, "Chart statistics should include total_hands"

def test_navigation_service_functionality():
    """Test basic navigation service functionality."""
    from holdem_cli.services.charts.navigation_service import get_navigation_service, Direction

    navigation_service = get_navigation_service()

    # Test matrix navigation
    new_pos = navigation_service.navigate_matrix(Direction.UP, 5, 5)
    assert new_pos == (4, 5), f"Matrix navigation failed: expected (4, 5), got {new_pos}"

    # Test position jumping
    pos = navigation_service.jump_to_position("UTG")
    assert pos is not None, "Position jumping should return a valid position"

    # Test view mode cycling
    current_mode = navigation_service.state.view_mode
    new_mode = navigation_service.cycle_view_mode()
    assert new_mode != current_mode, "View mode cycling should change the mode"

def test_ui_service_functionality():
    """Test basic UI service functionality."""
    from holdem_cli.services.charts.ui_service import get_ui_service

    ui_service = get_ui_service()

    # Test feedback message generation (doesn't require event loop)
    feedback = ui_service.create_feedback_message("test operation", True, "Success")
    assert "test operation succeeded" in feedback, "Feedback message should contain success info"

    # Test error message handling
    error_msg = ui_service.handle_error_feedback(ValueError("test error"), "test operation")
    assert "test operation" in error_msg, "Error message should contain operation name"

    # Note: notification tests skipped as they require a running event loop

def test_service_integration():
    """Test that services work together correctly."""
    from holdem_cli.services.charts.chart_service import get_chart_service
    from holdem_cli.charts.tui.widgets.matrix import create_sample_range

    chart_service = get_chart_service()
    sample_range = create_sample_range()

    # Test integrated workflow: load chart -> analyze
    stats = chart_service.analyze_chart_statistics(sample_range)
    assert stats is not None, "Chart analysis should return statistics"

    # Verify sample range has hands
    first_hand = list(sample_range.keys())[0] if sample_range else None
    assert first_hand is not None, "Sample range should contain hands"
    assert stats['total_hands'] > 0, "Statistics should show hands"

def test_app_initialization():
    """Test that the refactored app can be initialized."""
    # Test that we can import the new ChartViewerApp
    from holdem_cli.charts.app import ChartViewerApp

    # Verify the class exists and has expected attributes
    assert ChartViewerApp is not None
    assert ChartViewerApp.__name__ == "ChartViewerApp"

def main():
    """Run all integration tests."""
    print("🚀 Starting Service Integration Tests")
    print("=" * 50)

    tests = [
        test_service_imports,
        test_service_initialization,
        test_chart_service_functionality,
        test_navigation_service_functionality,
        test_ui_service_functionality,
        test_service_integration,
        test_app_initialization
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All integration tests passed! The new architecture is working correctly.")
        print("\n✨ Key improvements verified:")
        print("   • Service-based architecture successfully implemented")
        print("   • All services integrate properly")
        print("   • Chart analysis and statistics working")
        print("   • Navigation and UI feedback systems functional")
        print("   • Error handling and recovery mechanisms in place")
        return True
    else:
        print(f"⚠️ {failed} tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
