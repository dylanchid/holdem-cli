"""
Profile manager screen for managing user profiles and statistics.

This screen provides an interface for users to create profiles, view
statistics, and manage their training data.
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import Header, Footer, Button, Label, Input, Static, DataTable, TabbedContent, TabPane
from textual.screen import Screen
from textual import events
from textual.binding import Binding

from ....services.holdem_service import get_holdem_service


class ProfileManagerScreen(Screen):
    """Profile management and statistics screen."""

    CSS = """
    ProfileManagerScreen {
        layout: vertical;
        padding: 1;
    }

    .title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 2;
        width: 100%;
    }

    .profile-section {
        width: 100%;
        margin: 1 0;
        border: solid $primary;
        padding: 1;
        background: $surface;
    }

    .profile-row {
        layout: horizontal;
        margin: 1 0;
        align: center middle;
    }

    .profile-label {
        width: 15;
        margin-right: 2;
    }

    .profile-input {
        width: 30;
        margin-right: 2;
    }

    .profile-button {
        width: 15;
        margin: 0 1;
    }

    .stats-section {
        width: 100%;
        margin: 1 0;
        border: solid $secondary;
        padding: 1;
        background: $background;
        height: 25;
    }

    .stats-title {
        text-style: bold;
        color: $secondary;
        margin-bottom: 1;
    }

    .stats-content {
        height: 20;
        overflow: auto;
        background: $surface;
        padding: 1;
        border: solid grey;
    }

    .profile-list {
        height: 15;
        overflow: auto;
        background: $surface;
        padding: 1;
        border: solid grey;
    }

    .profile-item {
        layout: horizontal;
        margin: 1 0;
        align: center middle;
        padding: 1;
        border: solid grey;
    }

    .profile-name {
        width: 20;
        color: $primary;
        text-style: bold;
    }

    .profile-created {
        width: 25;
        color: $secondary;
    }

    .profile-action {
        width: 15;
        margin-left: auto;
    }

    .footer-text {
        text-align: center;
        color: grey;
        margin-top: 1;
        width: 100%;
    }
    """

    BINDINGS = [
        Binding("escape", "back", "Back to Main Menu"),
        Binding("f5", "refresh", "Refresh Data"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_profile = "default"
        self.profiles_data = []
        self.current_stats = None

    def compose(self) -> ComposeResult:
        """Compose the profile manager screen."""
        yield Header()

        yield Label("👤 Profile Manager", classes="title")

        # Profile management section
        with Vertical(classes="profile-section"):
            yield Label("⚙️ Profile Management", classes="section-title")

            # Create new profile
            with Horizontal(classes="profile-row"):
                yield Label("New Profile:", classes="profile-label")
                yield Input(
                    placeholder="Enter new profile name",
                    id="new_profile_input",
                    classes="profile-input"
                )
                yield Button("Create", id="create_profile", variant="success", classes="profile-button")

            # Switch to profile
            with Horizontal(classes="profile-row"):
                yield Label("Switch to:", classes="profile-label")
                yield Input(
                    placeholder="Enter profile name",
                    value=self.current_profile,
                    id="switch_profile_input",
                    classes="profile-input"
                )
                yield Button("Switch", id="switch_profile", variant="primary", classes="profile-button")

        # Statistics section with tabs
        with TabbedContent(id="profile_tabs", initial="tab_list"):
            # Profile list tab
            with TabPane("📋 All Profiles", id="tab_list"):
                with Vertical(classes="stats-section"):
                    yield Label("👥 Available Profiles", classes="stats-title")
                    yield Static("Loading profiles...", id="profile_list", classes="profile-list")

            # Statistics tab
            with TabPane("📊 Statistics", id="tab_stats"):
                with Vertical(classes="stats-section"):
                    yield Label(f"📈 Statistics for '{self.current_profile}'", classes="stats-title")
                    yield Static("Loading statistics...", id="stats_content", classes="stats-content")

        yield Static("Press F5 to refresh • Press Escape to go back", classes="footer-text")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the screen."""
        self._refresh_profiles()
        self._refresh_stats()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id

        if button_id == "create_profile":
            self._create_new_profile()
        elif button_id == "switch_profile":
            self._switch_profile()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes."""
        if event.input.id == "switch_profile_input":
            self.current_profile = event.value or "default"

    def action_refresh(self) -> None:
        """Refresh all data."""
        self._refresh_profiles()
        self._refresh_stats()

    def _create_new_profile(self) -> None:
        """Create a new profile."""
        try:
            profile_input = self.query_one("#new_profile_input", Input)
            profile_name = profile_input.value.strip()

            if not profile_name:
                self.notify("❌ Please enter a profile name", severity="error")
                return

            with get_holdem_service() as service:
                success, message = service.create_profile(profile_name)

                if success:
                    self.notify(f"✅ {message}", severity="information")
                    profile_input.value = ""  # Clear input
                    self._refresh_profiles()
                else:
                    self.notify(f"❌ {message}", severity="error")

        except Exception as e:
            self.notify(f"❌ Error creating profile: {e}", severity="error")

    def _switch_profile(self) -> None:
        """Switch to a different profile."""
        try:
            with get_holdem_service() as service:
                # Check if profile exists
                user = service.db.get_user(self.current_profile)
                if user:
                    self.notify(f"✅ Switched to profile '{self.current_profile}'", severity="information")
                    self._refresh_stats()
                else:
                    self.notify(f"❌ Profile '{self.current_profile}' not found", severity="error")

        except Exception as e:
            self.notify(f"❌ Error switching profile: {e}", severity="error")

    def _refresh_profiles(self) -> None:
        """Refresh the list of profiles."""
        try:
            with get_holdem_service() as service:
                self.profiles_data = service.list_profiles()
                self._display_profiles()

        except Exception as e:
            self.notify(f"❌ Error loading profiles: {e}", severity="error")

    def _refresh_stats(self) -> None:
        """Refresh statistics for the current profile."""
        try:
            with get_holdem_service() as service:
                self.current_stats = service.get_profile_stats(self.current_profile)
                self._display_stats()

        except Exception as e:
            self.notify(f"❌ Error loading statistics: {e}", severity="error")

    def _display_profiles(self) -> None:
        """Display the list of profiles."""
        try:
            if not self.profiles_data:
                content = "No profiles found. Create your first profile above."
            else:
                lines = ["Available Profiles:"]
                lines.append("-" * 40)

                for profile in self.profiles_data:
                    name = profile.get('name', 'Unknown')
                    created = profile.get('created_at', 'Unknown date')
                    lines.append(f"👤 {name}")
                    lines.append(f"   Created: {created}")
                    lines.append("")

                content = "\\n".join(lines)

            profile_list = self.query_one("#profile_list", Static)
            profile_list.update(content)

        except Exception as e:
            self.notify(f"❌ Error displaying profiles: {e}", severity="error")

    def _display_stats(self) -> None:
        """Display statistics for the current profile."""
        try:
            if not self.current_stats:
                content = f"No statistics available for profile '{self.current_profile}'."
            else:
                lines = []
                lines.append(f"📊 Statistics for '{self.current_profile}'")
                lines.append("=" * 50)

                # Overall stats
                overall = self.current_stats.get('overall', {})
                if overall:
                    total_sessions = overall.get('total_sessions', 0)
                    avg_accuracy = overall.get('avg_accuracy')
                    total_questions = overall.get('total_questions', 0)

                    lines.append(f"\\n🎯 Overall Performance:")
                    lines.append(f"   Total Quiz Sessions: {total_sessions}")
                    if avg_accuracy:
                        lines.append(f"   Average Accuracy: {avg_accuracy:.1f}%")
                    lines.append(f"   Total Questions: {total_questions}")

                # By quiz type
                by_type = self.current_stats.get('by_type', {})
                if by_type:
                    lines.append(f"\\n📈 Performance by Quiz Type:")
                    for quiz_type, stats in by_type.items():
                        avg_accuracy = stats.get('avg_accuracy', 0)
                        sessions = stats.get('sessions', 0)
                        lines.append(f"   {quiz_type.title()}: {avg_accuracy:.1f}% avg ({sessions} sessions)")

                # Recent activity
                lines.append(f"\\n⏰ Recent Activity:")
                lines.append("   (Feature coming soon)")

                content = "\\n".join(lines)

            stats_content = self.query_one("#stats_content", Static)
            stats_content.update(content)

        except Exception as e:
            self.notify(f"❌ Error displaying statistics: {e}", severity="error")

    def action_back(self) -> None:
        """Go back to the main menu."""
        self.app.pop_screen()

    def on_key(self, event: events.Key) -> None:
        """Handle keyboard input."""
        if event.key == "escape":
            self.action_back()

