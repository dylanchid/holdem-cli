#!/usr/bin/env python3
"""
Performance testing script for Holdem CLI.

This script tests the performance of key operations and generates
comprehensive performance reports.
"""

import sys
import time
import gc
from pathlib import Path

# Setup standardized imports
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent  # dev/testing -> dev -> project_root
src_dir = project_root / 'src'

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from holdem_cli.charts.tui.core.performance import get_performance_optimizer, log_performance_metrics
from holdem_cli.charts.tui.widgets.matrix import create_sample_range
from holdem_cli.services.holdem_service import HoldemService
from holdem_cli.charts.tui.services.chart_service import ChartService
import json

def test_chart_creation_performance():
    """Test performance of chart creation and manipulation."""
    print("🔧 Testing Chart Creation Performance...")
    optimizer = get_performance_optimizer()

    # Test sample range creation
    start_time = time.time()
    sample_range = create_sample_range()
    creation_time = time.time() - start_time

    print(".3f")
    print(f"   📊 Hands in range: {len(sample_range)}")

    # Test multiple range creations
    print("   📈 Testing multiple range creations...")
    for i in range(10):
        range_data = create_sample_range()
        optimizer.metrics.add_render_time(time.time() - start_time)

    print("   ✅ Chart creation test completed")

def test_equity_calculation_performance():
    """Test performance of equity calculations."""
    print("🧮 Testing Equity Calculation Performance...")
    optimizer = get_performance_optimizer()

    try:
        with HoldemService() as service:
            # Test simple equity calculation
            print("   📊 Testing simple equity calculation...")

            start_time = time.time()
            result = service.calculate_equity("AhKs", "QsQd", iterations=10000)
            equity_time = time.time() - start_time

            print(".3f")
            if result['success']:
                equity_data = result['equity']
                print(".1f")
                print(".1f")
            else:
                print(f"   ❌ Equity calculation failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"   ❌ Equity calculation test failed: {e}")

def test_memory_usage():
    """Test memory usage and optimization."""
    print("💾 Testing Memory Usage...")
    optimizer = get_performance_optimizer()

    # Force garbage collection
    gc.collect()

    # Measure initial memory
    initial_memory = optimizer.measure_memory_usage()
    print(".1f")

    # Create some objects to test memory
    ranges = []
    for i in range(50):
        ranges.append(create_sample_range())

    # Measure memory after object creation
    after_creation_memory = optimizer.measure_memory_usage()
    print(".1f")

    # Force optimization
    optimizer.optimize_memory()

    # Measure memory after optimization
    optimized_memory = optimizer.measure_memory_usage()
    print(".1f")
    print(".1f")

    # Clear objects
    del ranges
    gc.collect()

def test_caching_performance():
    """Test caching system performance."""
    print("🚀 Testing Caching Performance...")
    optimizer = get_performance_optimizer()

    # Test render caching
    def dummy_render():
        time.sleep(0.001)  # Simulate render time
        return f"Rendered at {time.time()}"

    # First render (cache miss)
    start_time = time.time()
    result1 = optimizer.cached_render("test_component", dummy_render)
    first_render_time = time.time() - start_time

    # Second render (cache hit)
    start_time = time.time()
    result2 = optimizer.cached_render("test_component", dummy_render)
    second_render_time = time.time() - start_time

    print(".3f")
    print(".3f")
    print(".2f")

    # Test multiple cache operations
    for i in range(20):
        optimizer.cached_render(f"component_{i}", dummy_render)

    cache_hit_rate = optimizer.metrics.get_cache_hit_rate()
    print(".1%")

def run_comprehensive_performance_test():
    """Run comprehensive performance test suite."""
    print("=" * 60)
    print("🏃‍♂️ HOLDEM CLI PERFORMANCE TEST SUITE")
    print("=" * 60)

    optimizer = get_performance_optimizer()
    optimizer.enable_optimization(True)

    # Run individual tests
    test_chart_creation_performance()
    print()

    test_equity_calculation_performance()
    print()

    test_memory_usage()
    print()

    test_caching_performance()
    print()

    # Generate final performance report
    print("📊 FINAL PERFORMANCE REPORT")
    print("=" * 40)

    try:
        log_performance_metrics()
    except Exception as e:
        print(f"❌ Could not generate full report: {e}")

        # Fallback: basic metrics
        metrics = optimizer.metrics.get_performance_summary()
        print(f"📈 Average Render Time: {metrics['average_render_time_ms']:.2f}ms")
        print(f"🎯 Cache Hit Rate: {metrics['cache_hit_rate']:.1%}")
        print(f"🧮 Total Renders: {metrics['total_renders']}")
        print(".0f")

    print("=" * 60)
    print("✅ Performance testing completed!")

def main():
    """Main performance testing function."""
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        if test_name == "chart":
            test_chart_creation_performance()
        elif test_name == "equity":
            test_equity_calculation_performance()
        elif test_name == "memory":
            test_memory_usage()
        elif test_name == "cache":
            test_caching_performance()
        else:
            print(f"Unknown test: {test_name}")
            print("Available tests: chart, equity, memory, cache")
    else:
        run_comprehensive_performance_test()

if __name__ == "__main__":
    main()
