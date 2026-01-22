from textual.app import ComposeResult
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Button
from textual.widgets import Footer
from textual.widgets import Header
from textual.widgets import Input
from textual.widgets import Label
from textual.widgets import SelectionList
from textual.widgets import Static

from streaming_overview_tui.config_layer.config import get_available_services
from streaming_overview_tui.config_layer.config import save_user_config
from streaming_overview_tui.config_layer.config import UserConfig


class SetupComplete(Message):
    """Message sent when setup is complete."""


class SetupScreen(Screen):
    """Setup screen for first-time configuration."""

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Welcome! Let's set up your streaming preferences.", id="welcome")
        yield Label("Region (e.g., DK, US, UK):")
        yield Input(placeholder="DK", id="region-input")
        yield Label("Select your streaming subscriptions:")
        yield SelectionList[str](
            *[(service, service) for service in get_available_services()],
            id="subscriptions-list",
        )
        yield Button("Save & Continue", id="save-btn", variant="primary")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            self._save_config()

    def _save_config(self) -> None:
        """Save the user configuration and notify app."""
        region_input = self.query_one("#region-input", Input)
        selection_list = self.query_one("#subscriptions-list", SelectionList)

        region = region_input.value.strip() or "DK"
        subscriptions = list(selection_list.selected)

        user_config = UserConfig(region=region, subscriptions=subscriptions)
        save_user_config(user_config)

        self.post_message(SetupComplete())
