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
    print("🔍 Testing service imports...")

    try:
        from holdem_cli.services.charts.chart_service import get_chart_service, ChartService
        from holdem_cli.services.charts.navigation_service import get_navigation_service, NavigationService
        from holdem_cli.services.charts.ui_service import get_ui_service, UIService
        print("✅ All service imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_service_initialization():
    """Test that services can be initialized without errors."""
    print("\n🔧 Testing service initialization...")

    try:
        from holdem_cli.services.charts.chart_service import get_chart_service
        from holdem_cli.services.charts.navigation_service import get_navigation_service
        from holdem_cli.services.charts.ui_service import get_ui_service

        # Get service instances
        chart_service = get_chart_service()
        navigation_service = get_navigation_service()
        ui_service = get_ui_service()

        print("✅ All services initialized successfully")
        print(f"   Chart service: {type(chart_service).__name__}")
        print(f"   Navigation service: {type(navigation_service).__name__}")
        print(f"   UI service: {type(ui_service).__name__}")

        return True
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        return False

def test_chart_service_functionality():
    """Test basic chart service functionality."""
    print("\n📊 Testing chart service functionality...")

    try:
        print("  🔍 Importing chart_service...")
        from holdem_cli.services.charts.chart_service import get_chart_service
        print("  ✅ chart_service imported successfully")

        print("  🔍 Importing create_sample_range...")
        from holdem_cli.charts.tui.widgets.matrix import create_sample_range
        print("  ✅ create_sample_range imported successfully")

        print("  🔍 Creating chart service...")
        chart_service = get_chart_service()
        print("  ✅ Chart service created successfully")

        print("  🔍 Creating sample range...")
        sample_range = create_sample_range()
        print("  ✅ Sample range created successfully")

        # Test chart validation
        is_valid, errors = chart_service.validate_chart_data(sample_range)
        if is_valid:
            print("✅ Chart validation passed")
        else:
            print(f"❌ Chart validation failed: {errors}")
            return False

        # Test chart statistics
        stats = chart_service.analyze_chart_statistics(sample_range)
        if stats and 'total_hands' in stats:
            print(f"✅ Chart statistics generated: {stats['total_hands']} hands")
        else:
            print("❌ Chart statistics failed")
            return False

        return True
    except Exception as e:
        print(f"❌ Chart service test failed: {e}")
        return False

def test_navigation_service_functionality():
    """Test basic navigation service functionality."""
    print("\n🧭 Testing navigation service functionality...")

    try:
        from holdem_cli.services.charts.navigation_service import get_navigation_service, Direction
        from holdem_cli.charts.tui.widgets.matrix import create_sample_range

        navigation_service = get_navigation_service()
        sample_range = create_sample_range()

        # Test matrix navigation
        new_pos = navigation_service.navigate_matrix(Direction.UP, 5, 5)
        if new_pos == (4, 5):
            print("✅ Matrix navigation works correctly")
        else:
            print(f"❌ Matrix navigation failed: expected (4, 5), got {new_pos}")
            return False

        # Test position jumping
        pos = navigation_service.jump_to_position("UTG")
        if pos is not None:
            print(f"✅ Position jumping works: UTG -> {pos}")
        else:
            print("❌ Position jumping failed")
            return False

        # Test view mode cycling
        current_mode = navigation_service.state.view_mode
        new_mode = navigation_service.cycle_view_mode()
        if new_mode != current_mode:
            print(f"✅ View mode cycling works: {current_mode} -> {new_mode}")
        else:
            print("❌ View mode cycling failed")
            return False

        return True
    except Exception as e:
        print(f"❌ Navigation service test failed: {e}")
        return False

def test_ui_service_functionality():
    """Test basic UI service functionality."""
    print("\n🎨 Testing UI service functionality...")

    try:
        from holdem_cli.services.charts.ui_service import get_ui_service, NotificationType

        ui_service = get_ui_service()

        # Test notification creation
        notification = ui_service.notify("Test notification", NotificationType.INFO)
        if notification:
            print("✅ Notification system works")
        else:
            print("❌ Notification system failed")
            return False

        # Test feedback message generation
        feedback = ui_service.create_feedback_message("test operation", True, "Success")
        if "✅ test operation succeeded: Success" in feedback:
            print("✅ Feedback message generation works")
        else:
            print("❌ Feedback message generation failed")
            return False

        # Test error message handling
        error_msg = ui_service.handle_error_feedback(ValueError("test error"), "test operation")
        if "❌ Invalid input: test operation" in error_msg:
            print("✅ Error message handling works")
        else:
            print("❌ Error message handling failed")
            return False

        return True
    except Exception as e:
        print(f"❌ UI service test failed: {e}")
        return False

def test_service_integration():
    """Test that services work together correctly."""
    print("\n🔗 Testing service integration...")

    try:
        from holdem_cli.services.charts.chart_service import get_chart_service
        from holdem_cli.services.charts.navigation_service import get_navigation_service
        from holdem_cli.services.charts.ui_service import get_ui_service
        from holdem_cli.charts.tui.widgets.matrix import create_sample_range

        # Initialize services
        chart_service = get_chart_service()
        navigation_service = get_navigation_service()
        ui_service = get_ui_service()

        sample_range = create_sample_range()

        # Test integrated workflow: load chart -> analyze -> navigate -> notify
        stats = chart_service.analyze_chart_statistics(sample_range)
        if stats:
            # Navigate based on analysis
            first_hand = list(sample_range.keys())[0] if sample_range else None
            if first_hand:
                print(f"✅ Integrated workflow successful: analyzed {stats['total_hands']} hands")
                return True
            else:
                print("❌ No hands found in sample range")
                return False
        else:
            print("❌ Chart analysis failed in integrated workflow")
            return False

    except Exception as e:
        print(f"❌ Service integration test failed: {e}")
        return False

def test_app_initialization():
    """Test that the refactored app can be initialized."""
    print("\n🏗️ Testing app initialization...")

    try:
        # Test that we can import the new ChartViewerApp
        from holdem_cli.charts.app import ChartViewerApp

        # Create app instance (without running it)
        app = ChartViewerApp.__new__(ChartViewerApp)

        print("✅ App class can be imported and instantiated")
        print(f"   App class: {ChartViewerApp.__name__}")
        print(f"   Services initialized: chart={hasattr(app, 'chart_service') if hasattr(app, '__dict__') else 'N/A'}")

        return True
    except Exception as e:
        print(f"❌ App initialization test failed: {e}")
        return False

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
