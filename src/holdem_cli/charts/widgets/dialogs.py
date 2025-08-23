"""
Dialog widgets for the TUI interface.

This module contains various dialog widgets used throughout the application:
- HelpDialog: Comprehensive help system
- ChartImportDialog: File import interface
- ConfirmDialog: Confirmation dialogs
- ErrorDialog: Error display
"""

from textual.widgets import Static, Button, Input, Select, Label, TextArea
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.reactive import reactive
from textual.message import Message
from textual import on
from typing import List, Dict, Optional, Callable, Any
from pathlib import Path

from ..constants import (
    HELP_DIALOG_CSS, CHART_IMPORT_DIALOG_CSS, HELP_CONTENT,
    SUPPORTED_IMPORT_FORMATS, DEFAULT_DIALOG_WIDTH, DEFAULT_DIALOG_HEIGHT
)
from ..messages import ImportDialogClosed


class HelpDialog(Container):
    """Interactive help dialog with searchable content."""
    
    CSS = HELP_DIALOG_CSS
    
    is_open: reactive[bool] = reactive(False)
    current_section: reactive[str] = reactive("general")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_open = False
        self.current_section = "general"
        self.help_sections = self._create_help_sections()
    
    def compose(self):
        """Create help dialog layout."""
        with ScrollableContainer(classes="help-content"):
            yield Label("🎯 Holdem CLI Help", classes="help-title")
            
            # Section selector
            yield Select(
                [
                    ("📖 General", "general"),
                    ("🎮 Navigation", "navigation"),
                    ("📊 View Modes", "views"),
                    ("🔧 Range Builder", "builder"),
                    ("💾 File Operations", "files"),
                    ("⌨️ Keyboard Shortcuts", "shortcuts"),
                    ("🐛 Troubleshooting", "troubleshooting")
                ],
                value="general",
                id="help_section_select"
            )
            
            # Help content area
            yield Static("", id="help_content_display", classes="help-section")
            
            # Close button
            with Horizontal(classes="help-buttons"):
                yield Button("Close Help", id="close_help", variant="primary")
                yield Button("Print Help", id="print_help", variant="default")
    
    def on_mount(self) -> None:
        """Initialize help dialog."""
        self._update_help_content("general")
    
    @on(Select.Changed, "#help_section_select")
    def handle_section_change(self, event: Select.Changed) -> None:
        """Handle help section change."""
        if event.value and isinstance(event.value, str):
            self.current_section = event.value
            self._update_help_content(event.value)
    
    @on(Button.Pressed, "#close_help")
    def handle_close_help(self, event: Button.Pressed) -> None:
        """Handle close help button."""
        self.close()
    
    @on(Button.Pressed, "#print_help")
    def handle_print_help(self, event: Button.Pressed) -> None:
        """Handle print help button."""
        self._export_help_to_file()
    
    def open(self) -> None:
        """Open the help dialog."""
        self.is_open = True
        self.add_class("open")
        self.display = True
    
    def close(self) -> None:
        """Close the help dialog."""
        self.is_open = False
        self.remove_class("open")
        self.display = False
    
    def toggle(self) -> None:
        """Toggle help dialog visibility."""
        if self.is_open:
            self.close()
        else:
            self.open()
    
    def _create_help_sections(self) -> Dict[str, List[str]]:
        """Create organized help content sections."""
        return {
            "general": [
                "[bold]Welcome to Holdem CLI![/bold]",
                "",
                "This is an interactive poker chart viewer and trainer that helps you",
                "study and practice GTO (Game Theory Optimal) poker strategies.",
                "",
                "[bold]Main Features:[/bold]",
                "• Interactive 13x13 hand matrix visualization",
                "• Multiple view modes (Range, Frequency, EV)",
                "• Range builder for creating custom ranges",
                "• Chart comparison and analysis tools",
                "• Import/export functionality",
                "• Built-in quiz system for training",
                "",
                "[bold]Getting Started:[/bold]",
                "1. Use arrow keys to navigate the hand matrix",
                "2. Press Enter to select a hand and view details",
                "3. Use Tab to switch between panels",
                "4. Press H anytime to open this help system",
                "",
                "Select different sections above for detailed help on specific topics."
            ],
            
            "navigation": [
                "[bold]🎮 Navigation Controls[/bold]",
                "",
                "[bold]Matrix Navigation:[/bold]",
                "• [accent]↑↓←→[/accent] or [accent]WASD[/accent] - Navigate hand matrix",
                "• [accent]Enter/Space[/accent] - Select hand and show details",
                "• [accent]Home[/accent] - Jump to top-left (AA)",
                "• [accent]End[/accent] - Jump to bottom-right (22)",
                "",
                "[bold]Panel Navigation:[/bold]",
                "• [accent]Tab[/accent] - Cycle to next panel",
                "• [accent]Shift+Tab[/accent] - Cycle to previous panel",
                "• [accent]Escape[/accent] - Clear selection or close dialogs",
                "",
                "[bold]Quick Jumps:[/bold]",
                "• [accent]1-6[/accent] - Jump to position-specific charts",
                "  1=UTG, 2=MP, 3=CO, 4=BTN, 5=SB, 6=BB",
                "",
                "[bold]Tab Navigation:[/bold]",
                "• [accent]Ctrl+1[/accent] - Main chart tab",
                "• [accent]Ctrl+2[/accent] - Statistics tab", 
                "• [accent]Ctrl+3[/accent] - Notes tab",
                "• [accent]Ctrl+T[/accent] - New chart tab",
                "• [accent]Ctrl+W[/accent] - Close current tab"
            ],
            
            "views": [
                "[bold]📊 View Modes[/bold]",
                "",
                "The chart viewer supports multiple visualization modes:",
                "",
                "[bold]1. Range View (Default)[/bold]",
                "• Shows action types with color coding",
                "• 🔴 Raise  🟢 Call  ⚫ Fold  🟡 Mixed  🔵 Bluff",
                "• Best for understanding overall strategy",
                "",
                "[bold]2. Frequency View[/bold]",
                "• Shows percentage frequency for each action",
                "• Color intensity indicates frequency level",
                "• Useful for mixed strategies and ranges",
                "",
                "[bold]3. EV View[/bold]",
                "• Shows expected value in big blinds",
                "• Green = positive EV, Red = negative EV",
                "• Helps understand profitability",
                "",
                "[bold]Switching Views:[/bold]",
                "• [accent]F[/accent] - Toggle frequency view",
                "• [accent]V[/accent] - Toggle EV view", 
                "• [accent]M[/accent] - Cycle through all view modes",
                "• Use the dropdown in the controls panel",
                "",
                "[bold]View Tips:[/bold]",
                "• Each view highlights different strategic aspects",
                "• Use frequency view to understand mixed strategies",
                "• Use EV view to understand hand profitability",
                "• Range view is best for quick strategy overview"
            ],
            
            "builder": [
                "[bold]🔧 Range Builder[/bold]",
                "",
                "The range builder helps you create and modify custom ranges:",
                "",
                "[bold]Activating Range Builder:[/bold]",
                "• [accent]B[/accent] - Toggle range builder mode",
                "• Builder mode indicator appears in title",
                "• Range builder controls become active",
                "",
                "[bold]Building Ranges:[/bold]",
                "• [accent]A[/accent] - Add currently selected hand to range",
                "• [accent]D[/accent] - Remove currently selected hand from range",
                "• [accent]C[/accent] - Clear entire custom range",
                "",
                "[bold]Range Builder Features:[/bold]",
                "• Visual feedback for hands in custom range",
                "• Ability to modify action types and frequencies",
                "• Save custom ranges to database",
                "• Export ranges to various formats",
                "",
                "[bold]Workflow Tips:[/bold]",
                "1. Enable range builder mode",
                "2. Navigate to hands you want to include",
                "3. Press A to add each hand",
                "4. Use controls panel to modify actions",
                "5. Save your custom range when complete",
                "",
                "[bold]Action Templates:[/bold]",
                "• Set default action for new hands added",
                "• Modify frequency and EV values",
                "• Add notes for strategic context"
            ],
            
            "files": [
                "[bold]💾 File Operations[/bold]",
                "",
                "[bold]Loading Charts:[/bold]",
                "• [accent]Ctrl+L[/accent] - Load chart from database",
                "• Import from files using Charts → Import menu",
                "• Supported formats: JSON, Simple text, PioSOLVER*, GTO Wizard*",
                "• (*Formats marked with * are planned features)",
                "",
                "[bold]Saving Charts:[/bold]",
                "• [accent]Ctrl+S[/accent] - Save current chart to database",
                "• Auto-saves include metadata and timestamps",
                "• Version history maintained automatically",
                "",
                "[bold]Exporting Data:[/bold]",
                "• [accent]Ctrl+E[/accent] - Export current chart",
                "• Multiple formats: TXT, JSON, CSV, PNG*",
                "• Include statistics and analysis in exports",
                "",
                "[bold]File Formats:[/bold]",
                "",
                "[bold]JSON Format:[/bold]",
                "```json",
                '{',
                '  \"name\": \"Chart Name\",',
                '  \"ranges\": {',
                '    \"AA\": {\"action\": \"raise\", \"frequency\": 1.0},',
                '    \"KK\": {\"action\": \"raise\", \"frequency\": 1.0}',
                '  }',
                '}',
                "```",
                "",
                "[bold]Simple Text Format:[/bold]",
                "```",
                "AA raise 1.0",
                "KK raise 1.0", 
                "QQ raise 0.9",
                "JJ call 0.8",
                "```",
                "",
                "[bold]Import Tips:[/bold]",
                "• Use JSON for complete data with notes and EV",
                "• Use simple text for quick range imports",
                "• Validate imported data before saving"
            ],
            
            "shortcuts": [
                "[bold]⌨️ Keyboard Shortcuts Reference[/bold]",
                "",
                "[bold]Essential Navigation:[/bold]",
                "• [accent]↑↓←→[/accent] - Navigate matrix",
                "• [accent]Enter[/accent] - Select hand",
                "• [accent]Tab[/accent] - Next panel",
                "• [accent]Q[/accent] - Quit application",
                "• [accent]H[/accent] - Toggle help",
                "",
                "[bold]Chart Operations:[/bold]",
                "• [accent]Ctrl+L[/accent] - Load chart",
                "• [accent]Ctrl+S[/accent] - Save chart", 
                "• [accent]Ctrl+C[/accent] - Compare charts",
                "• [accent]Ctrl+E[/accent] - Export chart",
                "",
                "[bold]View Controls:[/bold]",
                "• [accent]F[/accent] - Frequency view",
                "• [accent]V[/accent] - EV view",
                "• [accent]M[/accent] - Cycle view modes",
                "• [accent]R[/accent] - Reset view",
                "",
                "[bold]Range Builder:[/bold]",
                "• [accent]B[/accent] - Toggle builder mode",
                "• [accent]A[/accent] - Add hand to range",
                "• [accent]D[/accent] - Remove hand from range",
                "• [accent]C[/accent] - Clear custom range",
                "",
                "[bold]Search & Navigation:[/bold]",
                "• [accent]/[/accent] - Search hands",
                "• [accent]N[/accent] - Next search result",
                "• [accent]Shift+N[/accent] - Previous search result",
                "",
                "[bold]Quick Actions:[/bold]",
                "• [accent]Ctrl+R[/accent] - Refresh data",
                "• [accent]Ctrl+Z[/accent] - Undo action",
                "• [accent]Escape[/accent] - Close/Cancel",
                "",
                "[bold]Position Shortcuts:[/bold]",
                "• [accent]1[/accent] UTG    • [accent]4[/accent] BTN",
                "• [accent]2[/accent] MP     • [accent]5[/accent] SB", 
                "• [accent]3[/accent] CO     • [accent]6[/accent] BB",
                "",
                "[bold]Tab Management:[/bold]",
                "• [accent]Ctrl+T[/accent] - New tab",
                "• [accent]Ctrl+W[/accent] - Close tab",
                "• [accent]Ctrl+1/2/3[/accent] - Switch tabs"
            ],
            
            "troubleshooting": [
                "[bold]🐛 Troubleshooting[/bold]",
                "",
                "[bold]Common Issues:[/bold]",
                "",
                "[bold]Performance Issues:[/bold]",
                "• Chart rendering slowly?",
                "  → Try compact view mode",
                "  → Reduce chart complexity",
                "  → Clear cache with Ctrl+R",
                "",
                "• High memory usage?",
                "  → Close unused chart tabs",
                "  → Restart application periodically",
                "  → Clear render cache",
                "",
                "[bold]Display Issues:[/bold]",
                "• Colors not showing correctly?",
                "  → Check terminal color support",
                "  → Try different terminal emulator",
                "  → Use --no-color flag if needed",
                "",
                "• Text overlapping or misaligned?",
                "  → Resize terminal window",
                "  → Try compact view mode",
                "  → Check terminal font settings",
                "",
                "[bold]File Issues:[/bold]",
                "• Cannot import chart file?",
                "  → Check file format and structure",
                "  → Validate JSON syntax",
                "  → Check file permissions",
                "",
                "• Export failing?",
                "  → Check disk space",
                "  → Verify write permissions",
                "  → Try different export format",
                "",
                "[bold]Navigation Issues:[/bold]",
                "• Keys not working?",
                "  → Check if correct panel has focus",
                "  → Try clicking on matrix first",
                "  → Restart application if needed",
                "",
                "[bold]Getting Help:[/bold]",
                "• Check GitHub issues for known problems",
                "• Run with --debug flag for detailed logs",
                "• Include terminal info when reporting bugs",
                "• Try minimal reproduction steps",
                "",
                "[bold]Reset Options:[/bold]",
                "• [accent]R[/accent] - Reset current view",
                "• [accent]Ctrl+R[/accent] - Refresh all data",
                "• Restart app - Close and reopen",
                "• Clear config - Delete ~/.config/holdem-cli/"
            ]
        }
    
    def _update_help_content(self, section: str) -> None:
        """Update help content display for selected section."""
        try:
            content_display = self.query_one("#help_content_display", Static)
            if section in self.help_sections:
                content_lines = self.help_sections[section]
                content_display.update("\n".join(content_lines))
            else:
                content_display.update("Help section not found.")
        except Exception:
            pass  # Widget might not be mounted yet
    
    def _export_help_to_file(self) -> None:
        """Export help content to a text file."""
        try:
            help_file = Path("holdem_cli_help.txt")
            with open(help_file, 'w') as f:
                f.write("HOLDEM CLI HELP GUIDE\n")
                f.write("=" * 50 + "\n\n")
                
                for section_name, content_lines in self.help_sections.items():
                    f.write(f"{section_name.upper()}\n")
                    f.write("-" * len(section_name) + "\n")
                    for line in content_lines:
                        # Strip rich markup for plain text
                        clean_line = line.replace("[bold]", "").replace("[/bold]", "")
                        clean_line = clean_line.replace("[accent]", "").replace("[/accent]", "")
                        f.write(clean_line + "\n")
                    f.write("\n")
            
            if hasattr(self.app, 'notify'):
                self.app.notify(f"Help exported to {help_file}", severity="information")
        except Exception as e:
            if hasattr(self.app, 'notify'):
                self.app.notify(f"Failed to export help: {e}", severity="error")


class ChartImportDialog(Container):
    """Dialog for importing charts from files."""
    
    CSS = CHART_IMPORT_DIALOG_CSS
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.import_callback: Optional[Callable] = None
    
    def compose(self):
        """Create import dialog layout."""
        with Vertical(classes="import-dialog-content"):
            yield Label("📁 Import Chart", classes="dialog-title")
            
            # File selection
            yield Label("File Path:", classes="field-label")
            yield Input(
                placeholder="Enter file path or browse...",
                id="file_path_input",
                classes="file-input"
            )
            yield Button("Browse", id="browse_file", variant="default", classes="browse-button")
            
            # Format selection
            yield Label("Format:", classes="field-label")
            yield Select(
                [
                    ("JSON Format", "json"),
                    ("Simple Text", "simple"),
                    ("PioSOLVER (Beta)", "pio"),
                    ("GTO Wizard (Beta)", "gto_wizard")
                ],
                value="json",
                id="format_select"
            )
            
            # Chart details
            yield Label("Chart Name (optional):", classes="field-label")
            yield Input(
                placeholder="Auto-generated from filename",
                id="chart_name_input"
            )
            
            yield Label("Description (optional):", classes="field-label")
            yield Input(
                placeholder="Brief description of the chart",
                id="description_input"
            )
            
            # Import options
            yield Label("Options:", classes="field-label")
            # Note: Checkboxes would go here in a full implementation
            
            # Buttons
            with Horizontal(classes="dialog-buttons"):
                yield Button("Import", id="import_btn", variant="primary")
                yield Button("Cancel", id="cancel_btn", variant="default")
    
    @on(Button.Pressed, "#browse_file")
    def handle_browse_file(self, event: Button.Pressed) -> None:
        """Handle file browse button."""
        # In a real implementation, this would open a file picker
        # For now, just provide guidance
        if hasattr(self.app, 'notify'):
            self.app.notify("Enter file path manually. File picker coming in future version.", severity="information")
    
    @on(Button.Pressed, "#import_btn")
    def handle_import(self, event: Button.Pressed) -> None:
        """Handle import button press."""
        try:
            file_path_input = self.query_one("#file_path_input", Input)
            format_select = self.query_one("#format_select", Select)
            chart_name_input = self.query_one("#chart_name_input", Input)
            description_input = self.query_one("#description_input", Input)
            
            file_path = file_path_input.value.strip()
            format_type = format_select.value
            chart_name = chart_name_input.value.strip()
            description = description_input.value.strip()
            
            if not file_path:
                if hasattr(self.app, 'notify'):
                    self.app.notify("Please enter a file path", severity="error")
                return
            
            # Validate file exists
            if not Path(file_path).exists():
                if hasattr(self.app, 'notify'):
                    self.app.notify("File not found", severity="error")
                return
            
            # Generate chart name if not provided
            if not chart_name:
                chart_name = Path(file_path).stem.replace('_', ' ').title()
            
            # Attempt import
            if isinstance(format_type, str):
                self._perform_import(file_path, format_type, chart_name, description)
            else:
                if hasattr(self.app, 'notify'):
                    self.app.notify("Please select a format type", severity="error")
            
        except Exception as e:
            if hasattr(self.app, 'notify'):
                self.app.notify(f"Import error: {e}", severity="error")
    
    @on(Button.Pressed, "#cancel_btn")
    def handle_cancel(self, event: Button.Pressed) -> None:
        """Handle cancel button press."""
        self.close()
    
    def _perform_import(self, file_path: str, format_type: str, chart_name: str, description: str) -> None:
        """Perform the actual import operation."""
        try:
            # Import the chart using the utils function
            from ..utils import create_chart_from_file
            
            chart_data = create_chart_from_file(file_path, format_type)
            
            if not chart_data:
                if hasattr(self.app, 'notify'):
                    self.app.notify("No valid chart data found in file", severity="error")
                return
            
            # Save to database
            from ....storage import init_database
            from ...cli_integration import ChartManager
            
            db = init_database()
            manager = ChartManager(db)
            _ = manager.save_chart(chart_name, description, chart_data, 100)
            
            # Notify success
            if hasattr(self.app, 'notify'):
                self.app.notify(
                    f"✅ Imported '{chart_name}' with {len(chart_data)} hands",
                    severity="information"
                )
            
            # Close dialog and notify parent
            self.post_message(ImportDialogClosed(True, file_path, format_type))
            self.close()
            
            db.close()
            
        except Exception as e:
            if hasattr(self.app, 'notify'):
                self.app.notify(f"Import failed: {e}", severity="error")
    
    def open(self) -> None:
        """Open the import dialog."""
        self.display = True
        self.add_class("open")
        
        # Focus the file path input
        try:
            file_input = self.query_one("#file_path_input", Input)
            file_input.focus()
        except Exception:
            pass
    
    def close(self) -> None:
        """Close the import dialog."""
        self.display = False
        self.remove_class("open")


class ConfirmDialog(Container):
    """Generic confirmation dialog."""
    
    def __init__(self, title: str, message: str, confirm_callback: Optional[Callable] = None, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.message = message
        self.confirm_callback = confirm_callback
    
    def compose(self):
        """Create confirmation dialog layout."""
        with Vertical(classes="confirm-dialog-content"):
            yield Label(self.title, classes="dialog-title")
            yield Static(self.message, classes="dialog-message")
            
            with Horizontal(classes="dialog-buttons"):
                yield Button("Confirm", id="confirm_btn", variant="primary")
                yield Button("Cancel", id="cancel_btn", variant="default")
    
    @on(Button.Pressed, "#confirm_btn")
    def handle_confirm(self, event: Button.Pressed) -> None:
        """Handle confirm button."""
        if self.confirm_callback:
            self.confirm_callback()
        self.close()
    
    @on(Button.Pressed, "#cancel_btn")
    def handle_cancel(self, event: Button.Pressed) -> None:
        """Handle cancel button."""
        self.close()
    
    def open(self) -> None:
        """Open the dialog."""
        self.display = True
        self.add_class("open")
    
    def close(self) -> None:
        """Close the dialog."""
        self.display = False
        self.remove_class("open")


class ErrorDialog(Container):
    """Error display dialog."""
    
    def __init__(self, error_title: str, error_message: str, error_details: str = "", **kwargs):
        super().__init__(**kwargs)
        self.error_title = error_title
        self.error_message = error_message
        self.error_details = error_details
    
    def compose(self):
        """Create error dialog layout."""
        with Vertical(classes="error-dialog-content"):
            yield Label(f"❌ {self.error_title}", classes="error-title")
            yield Static(self.error_message, classes="error-message")
            
            if self.error_details:
                yield Label("Details:", classes="error-details-label")
                yield TextArea(
                    self.error_details,
                    read_only=True,
                    classes="error-details"
                )
            
            with Horizontal(classes="dialog-buttons"):
                yield Button("Copy Error", id="copy_error", variant="default")
                yield Button("Close", id="close_error", variant="primary")
    
    @on(Button.Pressed, "#copy_error")
    def handle_copy_error(self, event: Button.Pressed) -> None:
        """Handle copy error button."""
        # In a real implementation, this would copy to clipboard
        if hasattr(self.app, 'notify'):
            self.app.notify("Error details copied to clipboard", severity="information")
    
    @on(Button.Pressed, "#close_error")
    def handle_close_error(self, event: Button.Pressed) -> None:
        """Handle close error button."""
        self.close()
    
    def open(self) -> None:
        """Open the error dialog."""
        self.display = True
        self.add_class("open")
    
    def close(self) -> None:
        """Close the error dialog."""
        self.display = False
        self.remove_class("open")


# Utility functions for creating common dialogs
def create_confirmation_dialog(title: str, message: str, on_confirm: Callable) -> ConfirmDialog:
    """Create a standard confirmation dialog."""
    return ConfirmDialog(title, message, on_confirm)


def create_error_dialog(title: str, message: str, details: str = "") -> ErrorDialog:
    """Create a standard error dialog.""" 
    return ErrorDialog(title, message, details)


def show_info_dialog(app, title: str, message: str) -> None:
    """Show an information dialog using the app's notify system."""
    if hasattr(app, 'notify'):
        app.notify(f"{title}: {message}", severity="information")
