from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button
from textual.widgets import Label
from textual.widgets import Static

from streaming_overview_tui.search_engine.models import ContentItem


class DetailPanel(Widget):
    """Panel showing details of selected content item."""

    DEFAULT_CSS = """
    DetailPanel {
        width: 100%;
        height: 100%;
        padding: 1;
    }

    DetailPanel .title {
        text-style: bold;
    }

    DetailPanel .type {
        color: $text-muted;
    }

    DetailPanel .rating {
        color: $success;
    }

    DetailPanel .overview {
        margin-top: 1;
    }

    DetailPanel .watch-button {
        margin-top: 1;
        width: 100%;
    }

    DetailPanel .empty {
        color: $text-muted;
        text-style: italic;
    }
    """

    item: reactive[ContentItem | None] = reactive(None)

    def __init__(self, item: ContentItem | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.item = item

    def compose(self) -> ComposeResult:
        yield Vertical(id="detail-content")

    def on_mount(self) -> None:
        """Build initial content when mounted."""
        self._rebuild_content()

    def render_str(self) -> str:
        """Return string representation for testing."""
        if self.item is None:
            return ""

        parts = [f"{self.item.title} ({self.item.year})"]
        parts.append("Movie" if self.item.content_type == "movie" else "TV Show")

        if self.item.rating is not None:
            parts.append(f"Rating: {self.item.rating}/10")

        if self.item.overview:
            parts.append(self.item.overview)
        else:
            parts.append("No description available")

        for service in self.item.services:
            parts.append(f"Watch on {service.value}")

        return " ".join(parts)

    def watch_item(self, item: ContentItem | None) -> None:
        """React to item changes."""
        if self.is_mounted:
            self._rebuild_content()

    def _rebuild_content(self) -> None:
        """Rebuild the panel content."""
        container = self.query_one("#detail-content", Vertical)
        container.remove_children()

        if self.item is None:
            container.mount(Static("Select an item to see details", classes="empty"))
            return

        # Title and year
        year_str = f" ({self.item.year})" if self.item.year else ""
        container.mount(Label(f"{self.item.title}{year_str}", classes="title"))

        # Content type
        type_str = "Movie" if self.item.content_type == "movie" else "TV Show"
        container.mount(Label(type_str, classes="type"))

        # Rating
        if self.item.rating is not None:
            container.mount(Label(f"Rating: {self.item.rating}/10", classes="rating"))

        # Overview
        if self.item.overview:
            # Truncate long overviews
            overview = self.item.overview
            if len(overview) > 200:
                overview = overview[:197] + "..."
            container.mount(Static(overview, classes="overview"))
        else:
            container.mount(Static("No description available", classes="overview"))

        # Watch buttons
        for service in self.item.services:
            if service in self.item.watch_urls:
                url = self.item.watch_urls[service]
                btn = Button(f"Watch on {service.value}", classes="watch-button")
                btn.url = url  # Store URL on button for handler
                container.mount(btn)
