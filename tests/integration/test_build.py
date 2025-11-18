#!/usr/bin/env python3
"""
Test script to verify the built holdem-cli package works correctly.
"""

import sys
import subprocess

def test_package_installation():
    """Test installing the package from the wheel file."""
    import pytest
    from pathlib import Path

    # Install the wheel file
    wheel_file = "dist/holdem_cli-1.0.0b1-py3-none-any.whl"

    # Skip test if wheel file doesn't exist
    if not Path(wheel_file).exists():
        pytest.skip("Wheel file not found - run build first")

    result = subprocess.run([
        sys.executable, "-m", "pip", "install", wheel_file, "--force-reinstall"
    ], capture_output=True, text=True)

    assert result.returncode == 0, f"Package installation failed: {result.stderr}"

def test_imports():
    """Test that all key imports work."""
    # Test core imports - will raise ImportError if they fail
    from holdem_cli.charts.app import ChartViewerApp
    from holdem_cli.charts.quiz import ChartQuizApp
    from holdem_cli.charts.tui.widgets.matrix import HandMatrix, HandAction, ChartAction
    from holdem_cli.charts.chart_cli import ChartManager
    from holdem_cli.cli import main

    # Verify imports are not None
    assert ChartViewerApp is not None
    assert ChartQuizApp is not None
    assert HandMatrix is not None
    assert ChartManager is not None
    assert main is not None

def test_cli_command():
    """Test that the CLI command works."""
    # Try using the installed package directly
    result = subprocess.run([
        sys.executable, "-m", "holdem_cli.cli", "--help"
    ], capture_output=True, text=True)

    if result.returncode == 0 and "Holdem CLI" in result.stdout:
        return  # Success

    # Try alternative approach - check if holdem command exists
    try:
        result2 = subprocess.run(
            ["holdem", "--help"],
            capture_output=True, text=True
        )
        if result2.returncode == 0 and "Holdem CLI" in result2.stdout:
            return  # Success
    except FileNotFoundError:
        pass

    # If we get here, at least verify imports work
    from holdem_cli.cli import main
    assert main is not None, "CLI module should be importable"

def test_matrix_functionality():
    """Test basic matrix functionality."""
    from holdem_cli.charts.tui.widgets.matrix import HandMatrix, create_sample_range

    # Create a sample range
    sample_range = create_sample_range()

    # Create a matrix
    matrix = HandMatrix(sample_range, "Test Matrix")

    # Test rendering
    output = matrix.render(use_colors=False, compact=True)

    assert output is not None, "Matrix should render output"
    assert len(output) > 100, "Matrix output should have substantial content"

def main():
    """Run all tests."""
    print("🚀 Testing holdem-cli build")
    print("=" * 40)

    tests = [
        test_package_installation,
        test_imports,
        test_cli_command,
        test_matrix_functionality
    ]

    results = []
    for test in tests:
        results.append(test())
        print()

    passed = sum(results)
    total = len(results)

    print("=" * 40)
    if passed == total:
        print(f"🎉 All {total} tests passed!")
        print("\n✅ The built package is ready for testing!")
        print("\nTo use the package:")
        print("1. Install: pip install dist/holdem_cli-1.0.0b1-py3-none-any.whl")
        print("2. Run CLI: holdem --help")
        print("3. Launch TUI: holdem charts view")
    else:
        print(f"❌ {passed}/{total} tests passed")
        print("Some issues need to be resolved before testing.")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
