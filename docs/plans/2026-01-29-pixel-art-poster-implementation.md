# Pixel-Art Poster Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Display movie/TV posters as pixel-art in the detail panel using Unicode half-block characters.

**Architecture:** Add `pixel_art.py` module for image-to-text conversion, `poster_widget.py` for async fetching and display, then integrate into existing `detail_panel.py` with horizontal layout.

**Tech Stack:** Pillow (image processing), httpx (fetching), Textual (TUI), Rich (text styling)

---

## Task 1: Add Pillow Dependency

**Files:**
- Modify: `pyproject.toml:6-18`

**Step 1: Add pillow to dependencies**

Edit `pyproject.toml` and add pillow to the dependencies list:

```toml
dependencies = [
    "httpx>=0.28.1",
    "pillow>=11.0.0",
    "platformdirs>=4.5.1",
    ...
]
```

**Step 2: Install dependencies**

Run: `uv sync`
Expected: Pillow installs successfully

**Step 3: Verify import works**

Run: `uv run python -c "from PIL import Image; print('OK')"`
Expected: `OK`

**Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "build: add pillow dependency for poster rendering"
```

---

## Task 2: Create pixel_art Module - Basic Conversion

**Files:**
- Create: `streaming_overview_tui/tui_layer/widgets/pixel_art.py`
- Create: `tests/unit/tui_layer/test_pixel_art.py`

**Step 1: Write the failing test for solid color image**

Create `tests/unit/tui_layer/test_pixel_art.py`:

```python
import pytest
from PIL import Image
from rich.text import Text

from streaming_overview_tui.tui_layer.widgets.pixel_art import image_to_half_blocks


class TestImageToHalfBlocks:
    def test_solid_red_image_produces_uniform_output(self):
        """A solid red image should produce all red half-blocks."""
        # 4x4 pixel red image -> 4 wide x 2 tall in characters
        img = Image.new("RGB", (4, 4), color=(255, 0, 0))
        result = image_to_half_blocks(img, width=4, height=2)

        assert isinstance(result, Text)
        # Should have 2 lines (2 char rows)
        lines = str(result).split("\n")
        assert len(lines) == 2
        # Each line should have 4 half-block characters
        assert all(len(line) == 4 for line in lines)
        # All characters should be the lower half-block
        assert all(c == "▄" for line in lines for c in line)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/tui_layer/test_pixel_art.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'streaming_overview_tui.tui_layer.widgets.pixel_art'`

**Step 3: Write minimal implementation**

Create `streaming_overview_tui/tui_layer/widgets/pixel_art.py`:

```python
"""Convert images to Unicode half-block pixel art."""

from PIL import Image
from rich.style import Style
from rich.text import Text


def image_to_half_blocks(image: Image.Image, width: int, height: int) -> Text:
    """Convert a PIL Image to Rich Text using half-block characters.

    Each character cell represents 2 vertical pixels using the ▄ character.
    The top pixel is the background color, bottom pixel is foreground color.

    Args:
        image: PIL Image to convert (will be resized)
        width: Target width in characters
        height: Target height in characters (each char = 2 pixels)

    Returns:
        Rich Text object with styled half-block characters
    """
    # Resize image to target pixel dimensions
    pixel_height = height * 2  # 2 vertical pixels per character
    resized = image.resize((width, pixel_height), Image.Resampling.NEAREST)

    # Ensure RGB mode
    if resized.mode != "RGB":
        resized = resized.convert("RGB")

    pixels = resized.load()
    text = Text()

    for char_row in range(height):
        if char_row > 0:
            text.append("\n")

        for col in range(width):
            # Top pixel (background) and bottom pixel (foreground)
            top_y = char_row * 2
            bottom_y = top_y + 1

            top_color = pixels[col, top_y]
            bottom_color = pixels[col, bottom_y]

            # Convert RGB tuples to hex colors
            bg_hex = "#{:02x}{:02x}{:02x}".format(*top_color)
            fg_hex = "#{:02x}{:02x}{:02x}".format(*bottom_color)

            style = Style(color=fg_hex, bgcolor=bg_hex)
            text.append("▄", style=style)

    return text
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/tui_layer/test_pixel_art.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add streaming_overview_tui/tui_layer/widgets/pixel_art.py tests/unit/tui_layer/test_pixel_art.py
git commit -m "feat: add pixel_art module with basic image conversion"
```

---

## Task 3: Add pixel_art Tests for Edge Cases

**Files:**
- Modify: `tests/unit/tui_layer/test_pixel_art.py`

**Step 1: Write test for different colors in top/bottom pixels**

Add to `tests/unit/tui_layer/test_pixel_art.py`:

```python
    def test_two_color_vertical_stripe(self):
        """Top half red, bottom half blue should have different fg/bg colors."""
        img = Image.new("RGB", (2, 4), color=(255, 0, 0))
        pixels = img.load()
        # Bottom 2 rows are blue
        for x in range(2):
            for y in range(2, 4):
                pixels[x, y] = (0, 0, 255)

        result = image_to_half_blocks(img, width=2, height=2)
        plain = str(result)

        # First row: red top, red bottom (same color)
        # Second row: red top, blue bottom (different colors)
        lines = plain.split("\n")
        assert len(lines) == 2
        assert all(c == "▄" for line in lines for c in line)

    def test_respects_target_dimensions(self):
        """Output should match requested width and height."""
        img = Image.new("RGB", (100, 100), color=(0, 255, 0))
        result = image_to_half_blocks(img, width=12, height=18)
        lines = str(result).split("\n")

        assert len(lines) == 18
        assert all(len(line) == 12 for line in lines)
```

**Step 2: Run tests**

Run: `uv run pytest tests/unit/tui_layer/test_pixel_art.py -v`
Expected: PASS (implementation already handles these cases)

**Step 3: Commit**

```bash
git add tests/unit/tui_layer/test_pixel_art.py
git commit -m "test: add edge case tests for pixel_art module"
```

---

## Task 4: Create PosterWidget - Placeholder State

**Files:**
- Create: `streaming_overview_tui/tui_layer/widgets/poster_widget.py`
- Create: `tests/unit/tui_layer/test_poster_widget.py`

**Step 1: Write failing test for placeholder when no item**

Create `tests/unit/tui_layer/test_poster_widget.py`:

```python
import pytest
from textual.app import App
from textual.app import ComposeResult

from streaming_overview_tui.tui_layer.widgets.poster_widget import PosterWidget


class PosterWidgetApp(App):
    """Test app for PosterWidget."""

    def __init__(self, poster_url: str | None = None, tmdb_id: int | None = None):
        super().__init__()
        self.poster_url = poster_url
        self.tmdb_id = tmdb_id

    def compose(self) -> ComposeResult:
        yield PosterWidget(poster_url=self.poster_url, tmdb_id=self.tmdb_id)


class TestPosterWidget:
    @pytest.mark.asyncio
    async def test_shows_placeholder_when_no_poster_url(self):
        """When poster_url is None, show placeholder."""
        async with PosterWidgetApp(poster_url=None, tmdb_id=None).run_test() as pilot:
            widget = pilot.app.query_one(PosterWidget)
            rendered = widget.render_str()
            assert "No" in rendered
            assert "Poster" in rendered
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/tui_layer/test_poster_widget.py::TestPosterWidget::test_shows_placeholder_when_no_poster_url -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Create `streaming_overview_tui/tui_layer/widgets/poster_widget.py`:

```python
"""Widget for displaying movie/TV posters as pixel art."""

from textual.reactive import reactive
from textual.widget import Widget
from rich.text import Text

# Poster dimensions in characters
POSTER_WIDTH = 12
POSTER_HEIGHT = 18


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

    def render(self) -> Text:
        """Render the poster or placeholder."""
        if self._rendered_art is not None:
            return self._rendered_art
        return Text(PLACEHOLDER, style="dim")

    def render_str(self) -> str:
        """Return string representation for testing."""
        return str(self.render())
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/tui_layer/test_poster_widget.py::TestPosterWidget::test_shows_placeholder_when_no_poster_url -v`
Expected: PASS

**Step 5: Commit**

```bash
git add streaming_overview_tui/tui_layer/widgets/poster_widget.py tests/unit/tui_layer/test_poster_widget.py
git commit -m "feat: add PosterWidget with placeholder state"
```

---

## Task 5: Add Poster Cache to StreamApp

**Files:**
- Modify: `streaming_overview_tui/tui_layer/stream_app.py`

**Step 1: Add poster_cache dict to StreamApp**

Edit `streaming_overview_tui/tui_layer/stream_app.py`:

```python
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
```

**Step 2: Run all tests to verify no regressions**

Run: `uv run pytest -v`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add streaming_overview_tui/tui_layer/stream_app.py
git commit -m "feat: add poster_cache to StreamApp"
```

---

## Task 6: PosterWidget - Async Fetch and Render

**Files:**
- Modify: `streaming_overview_tui/tui_layer/widgets/poster_widget.py`
- Modify: `tests/unit/tui_layer/test_poster_widget.py`

**Step 1: Write failing test for successful fetch**

Add to `tests/unit/tui_layer/test_poster_widget.py`:

```python
from unittest.mock import AsyncMock
from unittest.mock import patch
from PIL import Image
import io


class TestPosterWidgetFetch:
    @pytest.mark.asyncio
    async def test_fetches_and_renders_poster(self):
        """When poster_url is set, fetch and render the image."""
        # Create a small test image
        test_image = Image.new("RGB", (92, 138), color=(255, 0, 0))
        img_bytes = io.BytesIO()
        test_image.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        mock_response = AsyncMock()
        mock_response.content = img_bytes.getvalue()
        mock_response.raise_for_status = lambda: None

        with patch("httpx.AsyncClient.get", return_value=mock_response):
            app = PosterWidgetApp(
                poster_url="https://image.tmdb.org/t/p/w92/test.jpg",
                tmdb_id=123,
            )
            async with app.run_test() as pilot:
                widget = pilot.app.query_one(PosterWidget)
                # Trigger fetch
                widget.fetch_poster()
                # Wait for worker to complete
                await pilot.pause()
                await pilot.pause()

                rendered = widget.render_str()
                # Should contain half-block characters, not placeholder
                assert "▄" in rendered
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/tui_layer/test_poster_widget.py::TestPosterWidgetFetch::test_fetches_and_renders_poster -v`
Expected: FAIL (fetch_poster method doesn't exist)

**Step 3: Implement async fetch**

Update `streaming_overview_tui/tui_layer/widgets/poster_widget.py`:

```python
"""Widget for displaying movie/TV posters as pixel art."""

from io import BytesIO

import httpx
from PIL import Image
from rich.text import Text
from textual.reactive import reactive
from textual.widget import Widget
from textual.worker import Worker
from textual.worker import get_current_worker

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
    async def _do_fetch(self) -> None:
        """Fetch poster image in background thread."""
        worker = get_current_worker()
        if worker.is_cancelled:
            return

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.poster_url)
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


# Import work decorator
from textual.worker import work
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/tui_layer/test_poster_widget.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add streaming_overview_tui/tui_layer/widgets/poster_widget.py tests/unit/tui_layer/test_poster_widget.py
git commit -m "feat: add async poster fetching to PosterWidget"
```

---

## Task 7: Update DetailPanel - Horizontal Layout

**Files:**
- Modify: `streaming_overview_tui/tui_layer/widgets/detail_panel.py`
- Modify: `tests/unit/tui_layer/test_detail_panel.py`

**Step 1: Write failing test for horizontal layout**

Add to `tests/unit/tui_layer/test_detail_panel.py`:

```python
from streaming_overview_tui.tui_layer.widgets.poster_widget import PosterWidget


class TestDetailPanelLayout:
    @pytest.mark.asyncio
    async def test_has_poster_widget(self):
        """DetailPanel should contain a PosterWidget."""
        item = ContentItem(
            tmdb_id=123,
            title="Test Movie",
            year=2022,
            content_type="movie",
            poster_url="/test.jpg",
            services=[],
            overview="Test overview",
            rating=7.5,
            watch_urls={},
        )
        async with DetailPanelApp(item).run_test() as pilot:
            posters = pilot.app.query(PosterWidget)
            assert len(posters) == 1

    @pytest.mark.asyncio
    async def test_poster_receives_url_from_item(self):
        """PosterWidget should receive poster_url from ContentItem."""
        item = ContentItem(
            tmdb_id=456,
            title="Test Movie",
            year=2022,
            content_type="movie",
            poster_url="/poster123.jpg",
            services=[],
            overview=None,
            rating=None,
            watch_urls={},
        )
        async with DetailPanelApp(item).run_test() as pilot:
            poster = pilot.app.query_one(PosterWidget)
            assert poster.tmdb_id == 456
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/tui_layer/test_detail_panel.py::TestDetailPanelLayout -v`
Expected: FAIL

**Step 3: Update DetailPanel implementation**

Update `streaming_overview_tui/tui_layer/widgets/detail_panel.py`:

```python
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
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/tui_layer/test_detail_panel.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add streaming_overview_tui/tui_layer/widgets/detail_panel.py tests/unit/tui_layer/test_detail_panel.py
git commit -m "feat: add horizontal layout with PosterWidget to DetailPanel"
```

---

## Task 8: Export PosterWidget from widgets package

**Files:**
- Modify: `streaming_overview_tui/tui_layer/widgets/__init__.py`

**Step 1: Add PosterWidget to exports**

Update `streaming_overview_tui/tui_layer/widgets/__init__.py`:

```python
from streaming_overview_tui.tui_layer.widgets.detail_panel import DetailPanel
from streaming_overview_tui.tui_layer.widgets.poster_widget import PosterWidget
from streaming_overview_tui.tui_layer.widgets.results_list import ResultsList

__all__ = ["DetailPanel", "PosterWidget", "ResultsList"]
```

**Step 2: Run all tests**

Run: `uv run pytest -v`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add streaming_overview_tui/tui_layer/widgets/__init__.py
git commit -m "feat: export PosterWidget from widgets package"
```

---

## Task 9: Run Pre-commit and Final Verification

**Step 1: Run pre-commit hooks**

Run: `pre-commit run --all-files`
Expected: All checks pass (or fix any issues)

**Step 2: Run full test suite**

Run: `uv run pytest -v`
Expected: All tests PASS

**Step 3: Manual smoke test**

Run: `uv run streaming-tui`
- Search for a movie
- Select a result
- Verify poster appears (or placeholder if no poster)

**Step 4: Final commit if any fixes needed**

```bash
git add -A
git commit -m "fix: address pre-commit issues"
```
