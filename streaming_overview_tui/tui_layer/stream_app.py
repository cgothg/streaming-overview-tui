from PIL import Image
from textual.app import App

from streaming_overview_tui.config_layer.config import config_exists
from streaming_overview_tui.tui_layer.main_screen import MainScreen
from streaming_overview_tui.tui_layer.setup_screen import SetupComplete
from streaming_overview_tui.tui_layer.setup_screen import SetupScreen


class StreamApp(App):
    """Main application for streaming overview TUI."""

    TITLE = "Streaming Overview"

    def __init__(self) -> None:
        super().__init__()
        self.poster_cache: dict[int, Image.Image] = {}

    def on_mount(self) -> None:
        """Route to appropriate screen based on config existence."""
        if config_exists():
            self.push_screen(MainScreen())
        else:
            self.push_screen(SetupScreen())

    def on_setup_complete(self, message: SetupComplete) -> None:
        """Called when setup is complete. Switch to main screen."""
        self.pop_screen()
        self.push_screen(MainScreen())
