import webbrowser

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.containers import Vertical
from textual.screen import Screen
from textual.timer import Timer
from textual.widgets import Button
from textual.widgets import Footer
from textual.widgets import Header
from textual.widgets import Input
from textual.widgets import Static

from streaming_overview_tui.config_layer.config import load_user_config
from streaming_overview_tui.config_layer.config import StreamingService
from streaming_overview_tui.search_engine import search
from streaming_overview_tui.search_engine import SearchResult
from streaming_overview_tui.tui_layer.widgets import DetailPanel
from streaming_overview_tui.tui_layer.widgets import ResultsList


class MainScreen(Screen):
    """Main screen for searching and browsing content."""

    BINDINGS = [
        Binding("escape", "focus_search", "Focus search"),
        Binding("q", "quit", "Quit"),
    ]

    DEFAULT_CSS = """
    MainScreen {
        layout: grid;
        grid-size: 1;
        grid-rows: auto 1fr auto;
    }

    #search-container {
        height: auto;
        padding: 1;
    }

    #search-input {
        width: 100%;
    }

    #main-content {
        height: 100%;
    }

    #results-container {
        width: 60%;
    }

    #detail-container {
        width: 40%;
        border-left: solid $primary;
    }

    #status-bar {
        height: auto;
        padding: 0 1;
        color: $text-muted;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._search_timer: Timer | None = None
        self._current_query: str = ""
        self._user_config = load_user_config()

    def compose(self) -> ComposeResult:
        yield Header()

        with Vertical(id="search-container"):
            yield Input(placeholder="Search movies and TV shows...", id="search-input")

        with Horizontal(id="main-content"):
            with Vertical(id="results-container"):
                yield ResultsList()
            with Vertical(id="detail-container"):
                yield DetailPanel()

        yield Static("", id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        """Focus search input on mount."""
        self.query_one("#search-input", Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes with debounce."""
        if event.input.id != "search-input":
            return

        self._current_query = event.value

        # Cancel pending search timer
        if self._search_timer is not None:
            self._search_timer.stop()

        # Set new debounce timer (300ms)
        if event.value:
            self._search_timer = self.set_timer(0.3, self._trigger_search)
        else:
            # Clear results immediately if input is empty
            self.query_one(ResultsList).results = None
            self.query_one(DetailPanel).item = None

    def _trigger_search(self) -> None:
        """Trigger the search after debounce."""
        self._search_timer = None
        if self._current_query:
            self._do_search(self._current_query)

    @work(exclusive=True)
    async def _do_search(self, query: str) -> None:
        """Perform search in background worker."""
        # Update status
        self._set_status("Searching...")

        # Get subscribed services
        subscriptions = [
            StreamingService(s)
            for s in self._user_config.subscriptions
            if s in [ss.value for ss in StreamingService]
        ]

        # Perform search
        result = await search(query, subscriptions)

        # Update UI
        self._update_results(result)

    def _set_status(self, message: str) -> None:
        """Update status bar."""
        self.query_one("#status-bar", Static).update(message)

    def _update_results(self, result: SearchResult) -> None:
        """Update results list with search results."""
        self.query_one(ResultsList).results = result

        # Update status
        total = len(result.available) + len(result.other)
        if result.error:
            self._set_status(result.error)
        elif total == 0:
            self._set_status(f"No results found for '{self._current_query}'")
        else:
            self._set_status(f"Found {total} results")

        # Clear detail panel
        self.query_one(DetailPanel).item = None

    def on_results_list_item_selected(self, event: ResultsList.ItemSelected) -> None:
        """Handle item selection from results list."""
        self.query_one(DetailPanel).item = event.item

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle watch button press."""
        if hasattr(event.button, "url"):
            webbrowser.open(event.button.url)

    def action_focus_search(self) -> None:
        """Focus the search input."""
        self.query_one("#search-input", Input).focus()

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
