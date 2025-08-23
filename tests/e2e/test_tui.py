
#!/usr/bin/env python3


"""Quick test script for TUI functionality."""

import sys
import os
from pathlib import Path

# Setup standardized imports using test utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
from test_utils import setup_test_imports
src_dir = setup_test_imports()

try:
    from holdem_cli.tui import HoldemApp

    # Create app instance
    app = HoldemApp()

    # Test that the app can be created and screens are available
    print("✅ TUI app created successfully")

    # Test that chart management screen can be created
    from holdem_cli.charts.tui.screens.chart_management import ChartManagementScreen
    screen = ChartManagementScreen()
    print("✅ Chart management screen created successfully")

    # Test that equity calculator screen can be created
    from holdem_cli.charts.tui.screens.equity_calculator import EquityCalculatorScreen
    screen = EquityCalculatorScreen()
    print("✅ Equity calculator screen created successfully")

    # Test that simulator screen can be created
    from holdem_cli.charts.tui.screens.simulator import SimulatorScreen
    screen = SimulatorScreen()
    print("✅ Simulator screen created successfully")

    print("✅ All TUI screens can be instantiated successfully")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

