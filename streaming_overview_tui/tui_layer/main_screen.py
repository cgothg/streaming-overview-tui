from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer
from textual.widgets import Header
from textual.widgets import Static

from streaming_overview_tui.config_layer.config import load_user_config


class MainScreen(Screen):
    """Main screen for searching and browsing content."""

    def compose(self) -> ComposeResult:
        yield Header()
        user_config = load_user_config()
        yield Static(f"Region: {user_config.region}")
        yield Static(f"Subscriptions: {', '.join(user_config.subscriptions) or 'None'}")
        yield Static("Main search interface - TODO")
        yield Footer()
