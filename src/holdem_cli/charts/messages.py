"""
Message classes for TUI communication.

This module contains all the message classes used for communication
between TUI components via the Textual messaging system.
"""

from textual.message import Message


class HandSelected(Message):
    """Message sent when a hand is selected."""

    def __init__(self, hand: str) -> None:
        self.hand = hand
        super().__init__()


class LoadChartRequested(Message):
    """Message sent when chart loading is requested."""
    pass


class SaveChartRequested(Message):
    """Message sent when chart saving is requested."""
    pass


class CompareChartsRequested(Message):
    """Message sent when chart comparison is requested."""
    pass


class ExportChartRequested(Message):
    """Message sent when chart export is requested."""
    pass


class ViewModeChanged(Message):
    """Message sent when view mode is changed."""

    def __init__(self, mode: str) -> None:
        self.mode = mode
        super().__init__()


class ChartTabSwitched(Message):
    """Message sent when switching between chart tabs."""

    def __init__(self, tab_id: str) -> None:
        self.tab_id = tab_id
        super().__init__()


class SearchQueryEntered(Message):
    """Message sent when a search query is entered."""

    def __init__(self, query: str) -> None:
        self.query = query
        super().__init__()


class RangeBuilderToggled(Message):
    """Message sent when range builder mode is toggled."""

    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled
        super().__init__()


class HandRangeModified(Message):
    """Message sent when a hand is added or removed from custom range."""

    def __init__(self, hand: str, action: str) -> None:
        self.hand = hand
        self.action = action  # "add" or "remove"
        super().__init__()


class ChartDataUpdated(Message):
    """Message sent when chart data is updated."""

    def __init__(self, chart_name: str) -> None:
        self.chart_name = chart_name
        super().__init__()


class QuizAnswerSelected(Message):
    """Message sent when a quiz answer is selected."""

    def __init__(self, answer: str) -> None:
        self.answer = answer
        super().__init__()


class QuizQuestionRequested(Message):
    """Message sent when a new quiz question is requested."""
    pass


class ImportDialogClosed(Message):
    """Message sent when the import dialog is closed."""

    def __init__(self, success: bool, file_path: str = "", format_type: str = "") -> None:
        self.success = success
        self.file_path = file_path
        self.format_type = format_type
        super().__init__()
