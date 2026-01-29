from io import BytesIO

import httpx
from PIL import Image
from rich.text import Text
from textual import work
from textual.reactive import reactive
from textual.widget import Widget
from textual.worker import get_current_worker
from textual.worker import Worker

from streaming_overview_tui.tui_layer.widgets.pixel_art import image_to_half_blocks

# Poster dimensions in characters
POSTER_WIDTH = 12
POSTER_HEIGHT = 18

# TMDB image base URL
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w92"


PLACEHOLDER = """\
┌──────────┐
│   ___    │
│  |   |   │
│  | > |   │
│  |___|   │
│          │
│    No    │
│  Poster  │
│          │
│          │
│          │
│          │
│          │
│          │
│          │
│          │
│          │
└──────────┘\
"""

LOADING_PLACEHOLDER = """\
┌──────────┐
│          │
│          │
│          │
│          │
│          │
│ Loading  │
│   ...    │
│          │
│          │
│          │
│          │
│          │
│          │
│          │
│          │
│          │
└──────────┘\
"""


class PosterWidget(Widget):
    """Displays a movie/TV poster as pixel art or placeholder."""

    DEFAULT_CSS = """
    PosterWidget {
        width: 12;
        height: 18;
    }
    """

    poster_url: reactive[str | None] = reactive(None)
    tmdb_id: reactive[int | None] = reactive(None)

    def __init__(
        self,
        poster_url: str | None = None,
        tmdb_id: int | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.poster_url = poster_url
        self.tmdb_id = tmdb_id
        self._rendered_art: Text | None = None
        self._loading = False
        self._fetch_worker: Worker | None = None

    def render(self) -> Text:
        """Render the poster or placeholder."""
        if self._rendered_art is not None:
            return self._rendered_art
        if self._loading:
            return Text(LOADING_PLACEHOLDER, style="dim")
        return Text(PLACEHOLDER, style="dim")

    def render_str(self) -> str:
        """Return string representation for testing."""
        return str(self.render())

    def fetch_poster(self) -> None:
        """Start async fetch of poster image."""
        if self.poster_url is None or self.tmdb_id is None:
            return

        # Check cache first
        cache = getattr(self.app, "poster_cache", {})
        if self.tmdb_id in cache:
            self._render_image(cache[self.tmdb_id])
            return

        # Cancel any existing fetch
        if self._fetch_worker is not None:
            self._fetch_worker.cancel()

        self._loading = True
        self.refresh()
        self._fetch_worker = self._do_fetch()

    @work(exclusive=True, thread=True)
    def _do_fetch(self) -> None:
        """Fetch poster image in background thread."""
        worker = get_current_worker()
        if worker.is_cancelled:
            return

        try:
            with httpx.Client() as client:
                response = client.get(self.poster_url)
                response.raise_for_status()

                if worker.is_cancelled:
                    return

                image = Image.open(BytesIO(response.content))

                # Cache the image
                cache = getattr(self.app, "poster_cache", None)
                if cache is not None and self.tmdb_id is not None:
                    cache[self.tmdb_id] = image

                self.app.call_from_thread(self._render_image, image)

        except Exception:
            self.app.call_from_thread(self._show_placeholder)

    def _render_image(self, image: Image.Image) -> None:
        """Convert image to pixel art and display."""
        self._rendered_art = image_to_half_blocks(image, POSTER_WIDTH, POSTER_HEIGHT)
        self._loading = False
        self.refresh()

    def _show_placeholder(self) -> None:
        """Show placeholder on fetch failure."""
        self._rendered_art = None
        self._loading = False
        self.refresh()
