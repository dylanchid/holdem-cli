"""
Interactive TUI components for Holdem CLI chart viewing.

This package contains the Textual-based user interface components for viewing,
editing, and analyzing poker charts interactively.
"""

from .app import ChartViewerApp
from .quiz import ChartQuizApp
# from .widgets import (
#     HelpDialog,
#     HandMatrixWidget,
#     HandDetailsWidget,
#     ChartControlsWidget,
#     ChartImportDialog,
#     ErrorBoundaryWidget,
#     QuizLauncherWidget
# )
from .messages import (
    HandSelected,
    LoadChartRequested,
    SaveChartRequested,
    CompareChartsRequested,
    ExportChartRequested,
    ViewModeChanged
)
from .utils import (
    run_chart_viewer,
    launch_interactive_chart_viewer,
    launch_chart_quiz,
    create_chart_from_file,
    demo_tui,
    demo_quiz
)

# Core systems
# from .core.error_handler import get_error_handler, handle_errors, ErrorCategory, ErrorSeverity
# from .core.events import get_event_bus, EventType, Event
# from .core.performance import get_performance_optimizer
# from .core.render_optimizer import get_render_optimizer
# from .core.state import ChartViewerState

# Services
# from .services.chart_service import get_chart_service
# from .services.navigation_service import get_navigation_service
# from .services.ui_service import get_ui_service
# from .services.db_service import get_database_service
# from .services.quiz_service import get_quiz_service

# Screens
# from .screens.main import MainScreen, create_main_screen
# from .screens.quiz import QuizScreen, create_quiz_screen
# from .screens.comparison import ComparisonScreen, create_comparison_screen

__all__ = [
    # Main applications
    "ChartViewerApp",
    "ChartQuizApp",

    # Widgets
    "HelpDialog",
    "HandMatrixWidget",
    "HandDetailsWidget",
    "ChartControlsWidget",
    "ChartImportDialog",
    "ErrorBoundaryWidget",
    "QuizLauncherWidget",

    # Messages
    "HandSelected",
    "LoadChartRequested",
    "SaveChartRequested",
    "CompareChartsRequested",
    "ExportChartRequested",
    "ViewModeChanged",

    # Utilities
    "run_chart_viewer",
    "launch_interactive_chart_viewer",
    "launch_chart_quiz",
    "create_chart_from_file",
    "demo_tui",
    "demo_quiz",

    # Core systems
    "get_error_handler",
    "handle_errors",
    "ErrorCategory",
    "ErrorSeverity",
    "get_event_bus",
    "EventType",
    "Event",
    "get_performance_optimizer",
    "get_render_optimizer",
    "ChartViewerState",

    # Services
    "get_chart_service",
    "get_navigation_service",
    "get_ui_service",
    "get_database_service",
    "get_quiz_service",

    # Screens
    "MainScreen",
    "create_main_screen",
    "QuizScreen",
    "create_quiz_screen",
    "ComparisonScreen",
    "create_comparison_screen"
]
