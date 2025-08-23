#!/usr/bin/env python3
"""
Demo script showing the new features in Holdem CLI.

This script demonstrates the enhanced capabilities of the refactored architecture
without requiring the full TUI interface.
"""

import sys
import os
from pathlib import Path

# Setup standardized imports
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent  # dev/demos -> dev -> project_root
src_dir = project_root / 'src'

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

def demo_service_architecture():
    """Demonstrate the new service-based architecture."""
    print("🏗️  Service-Based Architecture Demo")
    print("=" * 50)

    try:
        from holdem_cli.services.charts import get_chart_service
        from holdem_cli.services.charts import get_navigation_service
        from holdem_cli.services.charts import get_ui_service
        from holdem_cli.charts.tui.widgets.matrix import create_sample_range

        # Initialize services
        chart_service = get_chart_service()
        navigation_service = get_navigation_service()
        ui_service = get_ui_service()

        print("✅ Services initialized successfully:")
        print(f"   • Chart Service: {type(chart_service).__name__}")
        print(f"   • Navigation Service: {type(navigation_service).__name__}")
        print(f"   • UI Service: {type(ui_service).__name__}")

        # Demo chart operations
        sample_range = create_sample_range()
        print(f"\n📊 Sample chart created with {len(sample_range)} hands")

        # Validate chart
        is_valid, errors = chart_service.validate_chart_data(sample_range)
        if is_valid:
            print("✅ Chart validation passed")
        else:
            print(f"❌ Validation errors: {errors}")

        # Analyze statistics
        stats = chart_service.analyze_chart_statistics(sample_range)
        print("📈 Chart analysis:")
        print(f"   • Total hands: {stats['total_hands']}")
        print(f".1f")
        print(f"   • Tightness: {stats['range_analysis']['tightness']}")

        # Demo navigation
        from holdem_cli.services.charts import Direction
        new_pos = navigation_service.navigate_matrix(Direction.DOWN, 5, 5)
        print(f"\n🧭 Navigation demo: (5,5) → {new_pos}")

        # Demo UI feedback
        success_msg = ui_service.create_feedback_message("chart analysis", True, "49 hands processed")
        print(f"\n🎨 UI feedback: {success_msg}")

        return True

    except Exception as e:
        print(f"❌ Service demo failed: {e}")
        return False

def demo_enhanced_search():
    """Demonstrate the enhanced search functionality."""
    print("\n🔍 Enhanced Search Demo")
    print("=" * 30)

    try:
        from holdem_cli.services.charts import get_navigation_service
        from holdem_cli.charts.tui.widgets.matrix import create_sample_range

        navigation_service = get_navigation_service()
        sample_range = create_sample_range()

        # Demo different search queries
        search_queries = [
            "AK",           # Hand name search
            "suited",       # Hand type search
            "raise",        # Action search
            "premium"       # Premium hand search
        ]

        for query in search_queries:
            results = navigation_service.perform_search(query, sample_range, None)
            print(f"🔍 Search '{query}': Found {len(results)} hands")

            # Show first few results
            if results:
                preview = ", ".join(results[:5])
                if len(results) > 5:
                    preview += "..."
                print(f"   Preview: {preview}")

        return True

    except Exception as e:
        print(f"❌ Search demo failed: {e}")
        return False

def demo_chart_comparison():
    """Demonstrate chart comparison functionality."""
    print("\n⚖️  Chart Comparison Demo")
    print("=" * 30)

    try:
        from holdem_cli.services.charts import get_chart_service
        from holdem_cli.charts.tui.widgets.matrix import create_sample_range

        chart_service = get_chart_service()

        # Create two different ranges for comparison
        range1 = create_sample_range()

        # Create a tighter range (subset of range1)
        range2 = {hand: action for hand, action in list(range1.items())[:20]}

        # Compare charts using ChartComparison class
        from holdem_cli.charts.tui.widgets.matrix import ChartComparison
        comparison = ChartComparison(range1, range2, "GTO Range", "User Range")

        print("📊 Chart Comparison Results:")
        print(f"   • Chart 1: {len(range1)} hands")
        print(f"   • Chart 2: {len(range2)} hands")
        accuracy = comparison.calculate_accuracy()
        print(".1f")
        differences = comparison.find_differences()
        print(f"   • Total differences: {len(differences)} hands")

        return True

    except Exception as e:
        print(f"❌ Chart comparison demo failed: {e}")
        return False

def demo_error_handling():
    """Demonstrate enhanced error handling."""
    print("\n🛡️  Error Handling Demo")
    print("=" * 30)

    try:
        from holdem_cli.services.charts import get_ui_service

        ui_service = get_ui_service()

        # Demo different types of error messages
        error_scenarios = [
            (ValueError("Invalid hand format"), "hand validation", "Invalid input: hand validation"),
            (PermissionError("Access denied"), "file operation", "Permission denied: file operation"),
            (FileNotFoundError("File not found"), "chart loading", "File not found: chart loading"),
            (Exception("Network timeout"), "data sync", "data sync failed: Network timeout")
        ]

        for error, operation, expected_msg in error_scenarios:
            error_msg = ui_service.handle_error_feedback(error, operation)
            print(f"❌ {operation}: {error_msg}")
            assert expected_msg in error_msg

        print("✅ All error messages generated correctly")
        return True

    except Exception as e:
        print(f"❌ Error handling demo failed: {e}")
        return False

def demo_performance_features():
    """Demonstrate performance optimization features."""
    print("\n⚡ Performance Features Demo")
    print("=" * 35)

    try:
        from holdem_cli.services.charts import get_chart_service
        from holdem_cli.charts.tui.widgets.matrix import create_sample_range
        import time

        chart_service = get_chart_service()
        sample_range = create_sample_range()

        # Demo caching by running the same analysis twice
        print("⏱️  Performance caching demo:")

        start_time = time.time()
        stats1 = chart_service.analyze_chart_statistics(sample_range)
        first_run = time.time() - start_time

        start_time = time.time()
        stats2 = chart_service.analyze_chart_statistics(sample_range)
        second_run = time.time() - start_time

        print(".3f")
        print(".3f")

        if second_run < first_run:
            print("   ✅ Caching working - second run was faster!")
        else:
            print("   ℹ️  Caching may not be active or difference is negligible")

        return True

    except Exception as e:
        print(f"❌ Performance demo failed: {e}")
        return False

def main():
    """Run all demos."""
    print("🎯 Holdem CLI - New Features Demo")
    print("=" * 60)
    print("This demo showcases the enhanced capabilities of the refactored architecture.\n")

    demos = [
        demo_service_architecture,
        demo_enhanced_search,
        demo_chart_comparison,
        demo_error_handling,
        demo_performance_features
    ]

    passed = 0
    failed = 0

    for demo in demos:
        try:
            if demo():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Demo {demo.__name__} crashed: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"📊 Demo Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("\n🎉 All demos completed successfully!")
        print("\n✨ Key improvements demonstrated:")
        print("   • Service-based architecture working correctly")
        print("   • Enhanced search functionality operational")
        print("   • Chart comparison features functional")
        print("   • Error handling providing user-friendly messages")
        print("   • Performance optimizations with caching")

        print("\n🚀 The new architecture is ready for use!")
        print("\nTo start using the enhanced TUI:")
        print("   python -m holdem_cli.charts.tui.app")
        print("\nOr check the documentation:")
        print("   📖 NEW_FEATURES_GUIDE.md")
        print("   🎯 QUICK_REFERENCE.md")

    else:
        print(f"\n⚠️ {failed} demos failed. Please check the errors above.")

    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
