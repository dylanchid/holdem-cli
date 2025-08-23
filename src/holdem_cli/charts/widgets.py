"""
LEGACY COMPATIBILITY MODULE - DEPRECATED

This module provides backward compatibility for the old widgets.py structure.
All widgets have been moved to the modular widgets/ package.

⚠️  DEPRECATION WARNING:
This file is deprecated and will be removed in v1.0.0

MIGRATION GUIDE:
- OLD: from holdem_cli.charts.tui.widgets import HandMatrixWidget
- NEW: from holdem_cli.charts.tui.widgets import HandMatrixWidget

The new modular structure provides:
- Better organization and maintainability
- Improved performance with proper caching
- Enhanced functionality and features
- Cleaner separation of concerns

TIMELINE:
- v0.2.0: Added deprecation warning
- v0.3.0: Legacy compatibility layer
- v1.0.0: This file will be removed
"""

import warnings

# Issue deprecation warning
warnings.warn(
    "holdem_cli.charts.tui.widgets is deprecated. "
    "Import from holdem_cli.charts.tui.widgets package instead: "
    "from holdem_cli.charts.tui.widgets import HandMatrixWidget",
    DeprecationWarning,
    stacklevel=2
)

# Re-export all widgets from the new modular package
# from .widgets import (
#     HandMatrixWidget,
#     HandDetailsWidget,
#     ChartControlsWidget,
#     HelpDialog,
#     ChartImportDialog
# )

# Legacy compatibility - the old ImprovedHandMatrixWidget
# This is now just an alias to the new HandMatrixWidget
# ImprovedHandMatrixWidget = HandMatrixWidget

__all__ = [
    "HandMatrixWidget",
    "HandDetailsWidget", 
    "ChartControlsWidget",
    "HelpDialog",
    "ChartImportDialog",
    "ImprovedHandMatrixWidget"  # Legacy compatibility
]
