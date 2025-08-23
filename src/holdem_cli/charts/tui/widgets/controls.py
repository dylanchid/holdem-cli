"""
Chart controls widget for managing chart operations.

This widget provides a control panel with buttons and options for:
- Loading and saving charts
- Switching view modes
- Comparing charts
- Exporting data
- Range builder tools
"""

from textual.widgets import Static, Button, Select, Label
from textual.containers import Horizontal, Vertical
from textual.containers import Container
from textual.message import Message
from textual.reactive import reactive
from textual import on
from typing import Optional, List, Dict, Any

from ...constants import CHART_CONTROLS_CSS, VIEW_MODES, VIEW_MODE_EMOJIS
from ...messages import (
    LoadChartRequested, SaveChartRequested, CompareChartsRequested,
    ExportChartRequested, ViewModeChanged
)


class ChartControlsWidget(Container):
    """Widget with chart controls and options."""
    
    CSS = CHART_CONTROLS_CSS
    
    current_view_mode: reactive[str] = reactive("range")
    range_builder_enabled: reactive[bool] = reactive(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_view_mode = "range"
        self.range_builder_enabled = False
    
    def compose(self):
        """Create the control panel layout."""
        with Vertical():
            # View mode selection
            yield Label("📊 View Mode", classes="control-section-title")
            yield Select(
                [(f"{VIEW_MODE_EMOJIS.get(mode, '📊')} {mode.title()}", mode) for mode in VIEW_MODES],
                value=self.current_view_mode,
                id="view_mode_select"
            )
            
            # Chart operations
            yield Label("💾 Chart Operations", classes="control-section-title")
            with Horizontal(classes="button-row"):
                yield Button("Load", id="load_chart", variant="primary", classes="control-button")
                yield Button("Save", id="save_chart", variant="success", classes="control-button")
            
            with Horizontal(classes="button-row"):
                yield Button("Compare", id="compare_charts", variant="warning", classes="control-button")
                yield Button("Export", id="export_chart", variant="default", classes="control-button")
            
            # Range builder tools
            yield Label("🔧 Range Builder", classes="control-section-title")
            yield Button(
                "Toggle Builder", 
                id="toggle_range_builder", 
                variant="secondary",
                classes="control-button full-width"
            )
            
            with Horizontal(classes="button-row"):
                yield Button("Add Hand", id="add_hand", variant="success", classes="control-button small")
                yield Button("Remove", id="remove_hand", variant="error", classes="control-button small")
            
            yield Button(
                "Clear Range", 
                id="clear_range", 
                variant="error", 
                classes="control-button full-width"
            )
            
            # Quick actions
            yield Label("⚡ Quick Actions", classes="control-section-title")
            with Horizontal(classes="button-row"):
                yield Button("Reset", id="reset_view", variant="default", classes="control-button")
                yield Button("Help", id="show_help", variant="primary", classes="control-button")
    
    @on(Button.Pressed, "#load_chart")
    def handle_load_chart(self, event: Button.Pressed) -> None:
        """Handle load chart button press."""
        self.post_message(LoadChartRequested())
        event.button.add_class("pressed")
        self.set_timer(0.2, lambda: event.button.remove_class("pressed"))
    
    @on(Button.Pressed, "#save_chart")
    def handle_save_chart(self, event: Button.Pressed) -> None:
        """Handle save chart button press."""
        self.post_message(SaveChartRequested())
        event.button.add_class("pressed")
        self.set_timer(0.2, lambda: event.button.remove_class("pressed"))
    
    @on(Button.Pressed, "#compare_charts")
    def handle_compare_charts(self, event: Button.Pressed) -> None:
        """Handle compare charts button press."""
        self.post_message(CompareChartsRequested())
        event.button.add_class("pressed")
        self.set_timer(0.2, lambda: event.button.remove_class("pressed"))
    
    @on(Button.Pressed, "#export_chart")
    def handle_export_chart(self, event: Button.Pressed) -> None:
        """Handle export chart button press."""
        self.post_message(ExportChartRequested())
        event.button.add_class("pressed")
        self.set_timer(0.2, lambda: event.button.remove_class("pressed"))
    
    @on(Select.Changed, "#view_mode_select")
    def handle_view_mode_change(self, event: Select.Changed) -> None:
        """Handle view mode selection change."""
        if event.value:
            self.current_view_mode = event.value
            self.post_message(ViewModeChanged(event.value))
            self._update_view_mode_indicator()
    
    @on(Button.Pressed, "#toggle_range_builder")
    def handle_toggle_range_builder(self, event: Button.Pressed) -> None:
        """Handle range builder toggle."""
        self.range_builder_enabled = not self.range_builder_enabled
        button = event.button
        
        if self.range_builder_enabled:
            button.label = "🔧 Builder ON"
            button.variant = "success"
            self._enable_range_builder_controls()
        else:
            button.label = "Toggle Builder"
            button.variant = "secondary"
            self._disable_range_builder_controls()
        
        # Notify parent application
        from ...messages import RangeBuilderToggled
        self.post_message(RangeBuilderToggled(self.range_builder_enabled))
    
    @on(Button.Pressed, "#add_hand")
    def handle_add_hand(self, event: Button.Pressed) -> None:
        """Handle add hand to range."""
        if self.range_builder_enabled:
            from ...messages import HandRangeModified
            self.post_message(HandRangeModified("", "add"))  # Hand will be determined by current selection
            self._flash_button(event.button, "success")
    
    @on(Button.Pressed, "#remove_hand")
    def handle_remove_hand(self, event: Button.Pressed) -> None:
        """Handle remove hand from range."""
        if self.range_builder_enabled:
            from ...messages import HandRangeModified
            self.post_message(HandRangeModified("", "remove"))  # Hand will be determined by current selection
            self._flash_button(event.button, "error")
    
    @on(Button.Pressed, "#clear_range")
    def handle_clear_range(self, event: Button.Pressed) -> None:
        """Handle clear custom range."""
        if self.range_builder_enabled:
            from ...messages import HandRangeModified
            self.post_message(HandRangeModified("", "clear"))
            self._flash_button(event.button, "warning")
    
    @on(Button.Pressed, "#reset_view")
    def handle_reset_view(self, event: Button.Pressed) -> None:
        """Handle reset view button."""
        # Reset to default view mode
        select = self.query_one("#view_mode_select", Select)
        select.value = "range"
        self.current_view_mode = "range"
        self.post_message(ViewModeChanged("range"))
        self._flash_button(event.button, "primary")
    
    @on(Button.Pressed, "#show_help")
    def handle_show_help(self, event: Button.Pressed) -> None:
        """Handle show help button."""
        # This will be handled by the main application
        if hasattr(self.app, 'action_help'):
            self.app.action_help()
        self._flash_button(event.button, "primary")
    
    def _enable_range_builder_controls(self) -> None:
        """Enable range builder specific controls."""
        controls = ["#add_hand", "#remove_hand", "#clear_range"]
        for control_id in controls:
            try:
                control = self.query_one(control_id, Button)
                control.disabled = False
                control.add_class("enabled")
            except:
                pass  # Control might not exist yet
    
    def _disable_range_builder_controls(self) -> None:
        """Disable range builder specific controls."""
        controls = ["#add_hand", "#remove_hand", "#clear_range"]
        for control_id in controls:
            try:
                control = self.query_one(control_id, Button)
                control.disabled = True
                control.remove_class("enabled")
            except:
                pass  # Control might not exist yet
    
    def _update_view_mode_indicator(self) -> None:
        """Update visual indicators for current view mode."""
        # This could add visual feedback for the current view mode
        pass
    
    def _flash_button(self, button: Button, flash_class: str) -> None:
        """Flash a button with a specific style class."""
        button.add_class(f"flash-{flash_class}")
        self.set_timer(0.3, lambda: button.remove_class(f"flash-{flash_class}"))
    
    def update_state(self, view_mode: str, range_builder: bool) -> None:
        """Update widget state from external source."""
        self.current_view_mode = view_mode
        self.range_builder_enabled = range_builder
        
        # Update UI elements
        try:
            select = self.query_one("#view_mode_select", Select)
            select.value = view_mode
        except:
            pass
        
        try:
            toggle_button = self.query_one("#toggle_range_builder", Button)
            if range_builder:
                toggle_button.label = "🔧 Builder ON"
                toggle_button.variant = "success"
                self._enable_range_builder_controls()
            else:
                toggle_button.label = "Toggle Builder"
                toggle_button.variant = "secondary"
                self._disable_range_builder_controls()
        except:
            pass
    
    def get_status_summary(self) -> str:
        """Get a summary of current control states."""
        mode_emoji = VIEW_MODE_EMOJIS.get(self.current_view_mode, "📊")
        builder_status = "ON" if self.range_builder_enabled else "OFF"
        
        return f"{mode_emoji} {self.current_view_mode.title()} | Builder: {builder_status}"


# Additional control widget for advanced features
class AdvancedControlsWidget(Container):
    """Advanced controls for power users."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def compose(self):
        """Create advanced controls layout."""
        with Vertical():
            yield Label("🎛️ Advanced", classes="control-section-title")
            
            # Filters
            with Horizontal(classes="button-row"):
                yield Button("Filter", id="filter_hands", variant="default", classes="control-button")
                yield Button("Search", id="search_hands", variant="primary", classes="control-button")
            
            # Analysis tools
            with Horizontal(classes="button-row"):
                yield Button("Analyze", id="analyze_range", variant="warning", classes="control-button")
                yield Button("Stats", id="show_stats", variant="success", classes="control-button")
            
            # Import/Export
            yield Label("📁 Data", classes="control-section-title")
            with Horizontal(classes="button-row"):
                yield Button("Import", id="import_chart", variant="primary", classes="control-button")
                yield Button("Backup", id="backup_data", variant="default", classes="control-button")


# Utility functions for control widgets
def create_button_with_tooltip(label: str, tooltip: str, button_id: str, variant: str = "default") -> Button:
    """Create a button with tooltip support."""
    button = Button(label, id=button_id, variant=variant)
    button.tooltip = tooltip
    return button


def create_control_section(title: str, buttons: List[Dict[str, str]]) -> Vertical:
    """Create a standardized control section."""
    section = Vertical()
    section.mount(Label(title, classes="control-section-title"))
    
    for button_config in buttons:
        button = Button(
            button_config["label"],
            id=button_config["id"],
            variant=button_config.get("variant", "default"),
            classes="control-button"
        )
        section.mount(button)
    
    return section
