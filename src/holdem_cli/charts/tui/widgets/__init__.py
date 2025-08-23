"""
TUI Widgets package for Holdem CLI chart viewing.

This package contains all the widget components used in the terminal
user interface for interactive poker chart viewing and analysis.

Widgets:
    HandMatrixWidget: Interactive 13x13 poker hand matrix display
    HandDetailsWidget: Shows detailed information for selected hands
    ChartControlsWidget: Control panel for chart operations
    HelpDialog: Interactive help system
    ChartImportDialog: Dialog for importing charts from files

Each widget is designed to be modular, reusable, and follows Textual
best practices for performance and user experience.
"""

from .matrix_widget import HandMatrixWidget
from .details import HandDetailsWidget
from .controls import ChartControlsWidget
from .dialogs import HelpDialog, ChartImportDialog
from .error_boundary import ErrorBoundaryWidget
# from .quiz_integration import QuizLauncherWidget, QuizProgressWidget, QuizResultsWidget

# Re-export matrix classes for convenience
from .matrix import HandMatrix, HandAction, ChartAction, create_sample_range

__all__ = [
    "HandMatrixWidget",
    "HandDetailsWidget",
    "ChartControlsWidget",
    "HelpDialog",
    "ChartImportDialog",
    "ErrorBoundaryWidget",
    "QuizLauncherWidget",
    "QuizProgressWidget",
    "QuizResultsWidget",
    "HandMatrix",
    "HandAction",
    "ChartAction",
    "create_sample_range"
]
