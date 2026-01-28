from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label
from textual.widgets import ListItem
from textual.widgets import ListView
from textual.widgets import Static

from streaming_overview_tui.search_engine.models import ContentItem
from streaming_overview_tui.search_engine.models import SearchResult


class ResultsList(Widget):
    """List of search results in two sections."""

    DEFAULT_CSS = """
    ResultsList {
        width: 100%;
        height: 100%;
    }

    ResultsList .section-header {
        text-style: bold;
        color: $primary;
        padding: 0 1;
        margin-top: 1;
    }

    ResultsList .result-item {
        padding: 0 1;
    }

    ResultsList .services {
        color: $success;
    }

    ResultsList .placeholder {
        color: $text-muted;
        text-style: italic;
        padding: 1;
    }

    ResultsList ListView {
        height: auto;
        max-height: 100%;
    }
    """

    results: reactive[SearchResult | None] = reactive(None)

    class ItemSelected(Message):
        """Message sent when an item is selected."""

        def __init__(self, item: ContentItem) -> None:
            self.item = item
            super().__init__()

    def __init__(self, results: SearchResult | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.results = results
        self._items: list[ContentItem] = []

    def compose(self) -> ComposeResult:
        yield VerticalScroll(id="results-container")

    def render_str(self) -> str:
        """Return string representation for testing."""
        if self.results is None:
            return "Start typing to search..."

        if not self.results.available and not self.results.other:
            if self.results.error:
                return self.results.error
            return "No results found"

        parts = []
        if self.results.available:
            parts.append("AVAILABLE ON YOUR SERVICES")
            for item in self.results.available:
                services_str = ", ".join(s.value for s in item.services)
                parts.append(f"{item.title} ({item.year}) - {services_str}")

        if self.results.other:
            parts.append("OTHER RESULTS")
            for item in self.results.other:
                parts.append(f"{item.title} ({item.year})")

        return "\n".join(parts)

    def on_mount(self) -> None:
        """Build initial content when mounted."""
        self._rebuild_list()

    def watch_results(self, results: SearchResult | None) -> None:
        """React to results changes."""
        if self.is_mounted:
            self._rebuild_list()

    def _rebuild_list(self) -> None:
        """Rebuild the results list."""
        container = self.query_one("#results-container", VerticalScroll)
        container.remove_children()
        self._items = []

        if self.results is None:
            container.mount(Static("Start typing to search...", classes="placeholder"))
            return

        if not self.results.available and not self.results.other:
            if self.results.error:
                container.mount(Static(self.results.error, classes="placeholder"))
            else:
                container.mount(Static("No results found", classes="placeholder"))
            return

        # Build available section
        if self.results.available:
            container.mount(
                Label("AVAILABLE ON YOUR SERVICES", classes="section-header")
            )
            available_items: list[ListItem] = []
            for item in self.results.available:
                self._items.append(item)
                services_str = ", ".join(s.value for s in item.services)
                year_str = f" ({item.year})" if item.year else ""
                available_items.append(
                    ListItem(
                        Label(f"{item.title}{year_str} - {services_str}"),
                        id=f"item-{item.tmdb_id}",
                    )
                )
            container.mount(ListView(*available_items, id="available-list"))

        # Build other section
        if self.results.other:
            container.mount(Label("OTHER RESULTS", classes="section-header"))
            other_items: list[ListItem] = []
            for item in self.results.other:
                self._items.append(item)
                year_str = f" ({item.year})" if item.year else ""
                other_items.append(
                    ListItem(
                        Label(f"{item.title}{year_str}"),
                        id=f"item-{item.tmdb_id}",
                    )
                )
            container.mount(ListView(*other_items, id="other-list"))

    def _get_item_from_list_event(self, list_view: ListView) -> ContentItem | None:
        """Get ContentItem from a ListView event by matching item ID."""
        if list_view.index is None:
            return None
        # Get the highlighted ListItem
        highlighted = list_view.highlighted_child
        if highlighted is None:
            return None
        # Extract tmdb_id from item ID (format: "item-{tmdb_id}")
        item_id = highlighted.id
        if item_id and item_id.startswith("item-"):
            try:
                tmdb_id = int(item_id[5:])
                for item in self._items:
                    if item.tmdb_id == tmdb_id:
                        return item
            except ValueError:
                pass
        return None

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle item selection."""
        item = self._get_item_from_list_event(event.list_view)
        if item:
            self.post_message(self.ItemSelected(item))

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Handle item highlight (for keyboard navigation)."""
        item = self._get_item_from_list_event(event.list_view)
        if item:
            self.post_message(self.ItemSelected(item))
