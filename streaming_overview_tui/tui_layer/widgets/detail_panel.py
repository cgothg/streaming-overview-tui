from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button
from textual.widgets import Label
from textual.widgets import Static

from streaming_overview_tui.search_engine.models import ContentItem
from streaming_overview_tui.tui_layer.widgets.poster_widget import PosterWidget


class DetailPanel(Widget):
    """Panel showing details of selected content item."""

    DEFAULT_CSS = """
    DetailPanel {
        width: 100%;
        height: 100%;
        padding: 1;
    }

    DetailPanel Horizontal {
        height: auto;
    }

    DetailPanel #poster-container {
        width: 12;
        height: 18;
        margin-right: 1;
    }

    DetailPanel #info-container {
        width: 1fr;
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
        with Horizontal():
            yield PosterWidget(id="poster-container")
            yield Vertical(id="info-container")

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
        info_container = self.query_one("#info-container", Vertical)
        info_container.remove_children()

        poster_widget = self.query_one(PosterWidget)

        if self.item is None:
            poster_widget.poster_url = None
            poster_widget.tmdb_id = None
            info_container.mount(Static("Select an item to see details", classes="empty"))
            return

        # Update poster widget
        poster_widget.poster_url = self.item.poster_url
        poster_widget.tmdb_id = self.item.tmdb_id
        poster_widget.fetch_poster()

        # Title and year
        year_str = f" ({self.item.year})" if self.item.year else ""
        info_container.mount(Label(f"{self.item.title}{year_str}", classes="title"))

        # Content type
        type_str = "Movie" if self.item.content_type == "movie" else "TV Show"
        info_container.mount(Label(type_str, classes="type"))

        # Rating
        if self.item.rating is not None:
            info_container.mount(Label(f"Rating: {self.item.rating}/10", classes="rating"))

        # Overview
        if self.item.overview:
            # Truncate long overviews
            overview = self.item.overview
            if len(overview) > 200:
                overview = overview[:197] + "..."
            info_container.mount(Static(overview, classes="overview"))
        else:
            info_container.mount(Static("No description available", classes="overview"))

        # Watch buttons
        for service in self.item.services:
            if service in self.item.watch_urls:
                url = self.item.watch_urls[service]
                btn = Button(f"Watch on {service.value}", classes="watch-button")
                btn.url = url  # Store URL on button for handler
                info_container.mount(btn)
