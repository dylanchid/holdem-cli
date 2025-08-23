"""
Rich terminal interface for interactive chart viewing.

⚠️  DEPRECATED - This module is deprecated and will be removed in v1.0.0

MIGRATION GUIDE:
- OLD: from holdem_cli.charts.tui import ChartViewerApp
- NEW: from holdem_cli.charts.tui import ChartViewerApp

This module provides backward compatibility by re-exporting all components
from the new modular tui package structure.

All components are available directly from: holdem_cli.charts.tui

Available components:
- Apps: ChartViewerApp, ChartQuizApp
- Widgets: HelpDialog, HandMatrixWidget, HandDetailsWidget, ChartControlsWidget, ChartImportDialog
- Messages: Various message classes for inter-component communication
- Utils: Chart loading, demo functions, and utility functions

TIMELINE:
- v0.2.0: Added deprecation warning
- v1.0.0: This file will be removed
"""
import warnings

# Issue deprecation warning
warnings.warn(
    "holdem_cli.charts.tui is deprecated. "
    "Import from holdem_cli.charts.tui package instead: "
    "from holdem_cli.charts.tui import ChartViewerApp",
    DeprecationWarning,
    stacklevel=2
)

from .tui.app import ChartViewerApp, ChartQuizApp
from .tui.widgets import (
    HelpDialog,
    HandMatrixWidget,
    HandDetailsWidget,
    ChartControlsWidget,
    ChartImportDialog,
    ErrorBoundaryWidget,
    QuizLauncherWidget
)
from .tui.messages import (
    HandSelected,
    LoadChartRequested,
    SaveChartRequested,
    CompareChartsRequested,
    ExportChartRequested,
    ViewModeChanged
)
from .tui.utils import (
    run_chart_viewer,
    launch_interactive_chart_viewer,
    launch_chart_quiz,
    create_chart_from_file,
    demo_tui,
    demo_quiz
)