"""
Help dialog widget for contextual help throughout the application.

This widget provides contextual help and navigation assistance
for all screens in the application.
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import Static, Button, Label
from textual.widget import Widget
from textual.reactive import reactive
from textual import events
from textual.message import Message


class HelpDialog(Widget):
    """Contextual help dialog widget."""

    CSS = """
    HelpDialog {
        layer: overlay;
        background: $background;
        border: solid $primary;
        width: 60%;
        height: 70%;
        padding: 1;
        margin: auto;
        display: none;
    }

    HelpDialog.open {
        display: block;
    }

    .help-title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
        text-align: center;
    }

    .help-content {
        height: 15;
        overflow: auto;
        background: $surface;
        padding: 1;
        border: solid grey;
        margin-bottom: 1;
    }

    .help-section {
        margin: 1 0;
    }

    .help-section-title {
        text-style: bold;
        color: $secondary;
        margin-bottom: 1;
    }

    .help-item {
        margin: 0 0 1 2;
    }

    .help-key {
        color: $primary;
        text-style: bold;
        width: 8;
    }

    .help-description {
        color: $text;
    }

    .help-footer {
        layout: horizontal;
        align: center middle;
        margin-top: 1;
    }

    .help-button {
        width: 15;
        margin: 0 1;
    }
    """

    open = reactive(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.help_context = "main"

    def compose(self) -> ComposeResult:
        """Compose the help dialog."""
        yield Label("🆘 Help & Navigation", classes="help-title")

        with ScrollableContainer(classes="help-content"):
            yield Static(self._get_help_content(), id="help_content")

        with Horizontal(classes="help-footer"):
            yield Button("Close", id="close_help", variant="primary", classes="help-button")
            yield Button("Previous", id="prev_context", variant="secondary", classes="help-button")
            yield Button("Next", id="next_context", variant="secondary", classes="help-button")

    def _get_help_content(self) -> str:
        """Get help content based on current context."""
        help_content = {
            "main": self._get_main_help(),
            "quiz_menu": self._get_quiz_help(),
            "equity_calculator": self._get_equity_help(),
            "simulator": self._get_simulator_help(),
            "chart_management": self._get_chart_help(),
            "profile_manager": self._get_profile_help()
        }

        return help_content.get(self.help_context, self._get_main_help())

    def _get_main_help(self) -> str:
        """Get help for main menu."""
        return """
📋 **Main Menu Help**

This is the central hub of Holdem CLI. From here you can access all features:

🎯 **Navigation:**
• Use **Arrow Keys** to navigate between options
• Press **Enter** to select an option
• Press **Q** to quit the application
• Press **F1** for this help dialog

📊 **Available Modes:**
• **Chart Analysis**: View and analyze GTO poker charts
• **Quiz Mode**: Test your poker knowledge with interactive quizzes
• **Equity Calculator**: Calculate hand vs hand equity
• **Simulator**: Practice against AI opponents
• **Chart Quiz**: Test your chart knowledge (coming soon)
• **Profile**: Manage your training data and statistics

💡 **Tips:**
• All progress is automatically saved to your profile
• You can switch between modes at any time
• Use the help system (F1) in any screen for context-specific guidance
"""

    def _get_quiz_help(self) -> str:
        """Get help for quiz menu."""
        return """
🎯 **Quiz Mode Help**

Test your poker knowledge with adaptive quizzes:

📝 **Quiz Types:**
• **Hand Ranking Quiz**: Test your ability to rank poker hands
• **Pot Odds Quiz**: Practice calculating pot odds decisions

⚙️ **Configuration Options:**
• **Profile**: Select which profile to save results to
• **Questions**: Choose how many questions (5-50)
• **Difficulty**: Easy, Medium, Hard, or Adaptive

🎮 **Controls:**
• Use **Arrow Keys** to navigate options
• Press **Enter** to select and start quiz
• Press **Escape** to return to main menu
• Answer questions using number keys or arrow keys

📊 **Features:**
• Adaptive difficulty adjusts based on performance
• Detailed explanations for each question
• Progress tracking and statistics
• Results saved automatically to your profile
"""

    def _get_equity_help(self) -> str:
        """Get help for equity calculator."""
        return """
🧮 **Equity Calculator Help**

Calculate precise hand vs hand equity with advanced options:

📝 **Input Options:**
• **Hand 1 & Hand 2**: Enter hole cards (e.g., AsKs, 7h7d)
• **Board**: Optional community cards (e.g., 2c7s9h)
• **Iterations**: Monte Carlo simulation count (higher = more accurate)
• **Random Seed**: Optional seed for reproducible results

🎛️ **Advanced Features:**
• **JSON Output**: Toggle between human-readable and JSON formats
• **Deterministic Results**: Use seed for consistent calculations
• **Board Analysis**: Include flop, turn, and river cards

⌨️ **Controls:**
• Press **F5** or click **Calculate** to run simulation
• Use **Tab** to navigate between input fields
• Click **Format Toggle** to switch output modes
• Press **Escape** to return to main menu

📊 **Output:**
• **Human-readable**: Formatted text matching CLI output
• **JSON**: Machine-readable format for programmatic use
• **Win/Tie/Loss Probabilities**: Detailed breakdown
• **Simulation Statistics**: Iterations and confidence level
"""

    def _get_simulator_help(self) -> str:
        """Get help for simulator."""
        return """
🎲 **Poker Simulator Help**

Practice real poker scenarios against AI opponents:

🤖 **AI Difficulty Levels:**
• **Easy**: Basic strategy with some mistakes
• **Medium**: Solid strategy with occasional errors
• **Hard**: Expert-level play

📁 **Export Features:**
• **Filename**: Optional name for exported files
• **Format**: JSON (detailed) or Text (summary)
• **Auto-save**: All simulations saved to your profile

🎮 **Game Features:**
• Realistic poker scenarios
• Action history tracking
• Final hand analysis
• Winner determination with reasoning

⌨️ **Controls:**
• Press **F5** or click **Start Simulation** to begin
• Configure AI level and export options first
• Press **Escape** to return to main menu

📊 **Results Include:**
• Final hole cards and board
• Action history throughout the hand
• Winner and pot size
• AI reasoning (for learning)
• Optional file export
"""

    def _get_chart_help(self) -> str:
        """Get help for chart management."""
        return """
📊 **Chart Management Help**

Comprehensive chart viewing, creation, and analysis tools:

📋 **Chart List Tab:**
• Browse all saved charts
• View chart metadata (spot, stack depth, matchup)
• Click on charts to view details

👁️ **Chart Viewer Tab:**
• Visual matrix representation
• Hand-by-hand action breakdown
• Action frequencies and EV estimates

📈 **Analysis Tab:**
• Range composition statistics
• Action distribution charts
• Performance analysis

⚙️ **Management Features:**
• **View Chart**: Load and display any saved chart
• **Create Chart**: Build new charts from templates
• **Import/Export**: JSON, Text, and CSV formats
• **Sample Chart**: Quick access to demo content

⌨️ **Controls:**
• Press **F5** to refresh chart list
• Press **F6** to load sample chart
• Use **Tab** to switch between views
• Press **Escape** to return to main menu

💡 **Tips:**
• Charts include GTO-optimal strategies
• Use analysis tab to understand range composition
• Export charts for use in other applications
• Import charts from external sources
"""

    def _get_profile_help(self) -> str:
        """Get help for profile manager."""
        return """
👤 **Profile Manager Help**

Manage your training data, progress, and statistics:

👥 **Profile List Tab:**
• View all created profiles
• See creation dates and basic info
• Switch between profiles easily

📊 **Statistics Tab:**
• Overall quiz performance
• Quiz type breakdown
• Accuracy trends and progress
• Recent activity summary

⚙️ **Profile Operations:**
• **Create Profile**: Start fresh with a new name
• **Switch Profile**: Change active profile
• **View Stats**: Detailed performance analytics

📈 **Statistics Include:**
• Total quiz sessions completed
• Average accuracy across all quizzes
• Performance by quiz type (hand ranking, pot odds)
• Recent activity and trends

⌨️ **Controls:**
• Press **F5** to refresh all data
• Use **Tab** to switch between profile list and stats
• Press **Escape** to return to main menu

💡 **Tips:**
• Each profile maintains separate progress
• Statistics help identify improvement areas
• Regular practice with different quiz types recommended
• Progress automatically saved and tracked
"""

    def toggle(self) -> None:
        """Toggle the help dialog visibility."""
        self.open = not self.open
        self.refresh()

    def set_context(self, context: str) -> None:
        """Set the help context."""
        self.help_context = context
        help_content = self.query_one("#help_content", Static)
        help_content.update(self._get_help_content())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "close_help":
            self.toggle()
        elif event.button.id == "prev_context":
            self._previous_context()
        elif event.button.id == "next_context":
            self._next_context()

    def _previous_context(self) -> None:
        """Switch to previous help context."""
        contexts = ["main", "quiz_menu", "equity_calculator", "simulator", "chart_management", "profile_manager"]
        current_index = contexts.index(self.help_context)
        prev_index = (current_index - 1) % len(contexts)
        self.set_context(contexts[prev_index])

    def _next_context(self) -> None:
        """Switch to next help context."""
        contexts = ["main", "quiz_menu", "equity_calculator", "simulator", "chart_management", "profile_manager"]
        current_index = contexts.index(self.help_context)
        next_index = (current_index + 1) % len(contexts)
        self.set_context(contexts[next_index])

    def on_key(self, event: events.Key) -> None:
        """Handle keyboard input."""
        if event.key == "escape":
            self.toggle()
