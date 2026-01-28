# TUI Layer Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the main search screen with results list, detail panel, and watch buttons.

**Architecture:** Three custom widgets (DetailPanel, ResultsList, SearchInput) composed in MainScreen. Search is debounced and runs async. Detail panel updates on selection. Watch buttons open browser.

**Tech Stack:** Textual (TUI framework), webbrowser (stdlib), existing search_engine module.

---

## Task 1: Extend ContentItem with Detail Fields

The current `ContentItem` lacks overview, rating, and watch URLs needed for the detail panel. We'll extend it and update the search function.

**Files:**
- Modify: `streaming_overview_tui/search_engine/models.py`
- Modify: `streaming_overview_tui/search_engine/search.py`
- Modify: `tests/unit/search_engine/test_models.py`
- Modify: `tests/unit/search_engine/test_search.py`

**Step 1: Write failing test for extended ContentItem**

Add to `tests/unit/search_engine/test_models.py`:

```python
class TestContentItemExtended:
    def test_content_item_with_details(self):
        from streaming_overview_tui.config_layer.config import StreamingService
        from streaming_overview_tui.search_engine.models import ContentItem

        item = ContentItem(
            tmdb_id=123,
            title="The Batman",
            year=2022,
            content_type="movie",
            poster_url="https://image.tmdb.org/t/p/w500/test.jpg",
            services=[StreamingService.NETFLIX],
            overview="A dark detective story.",
            rating=7.8,
            watch_urls={StreamingService.NETFLIX: "https://netflix.com/watch/123"},
        )
        assert item.overview == "A dark detective story."
        assert item.rating == 7.8
        assert item.watch_urls[StreamingService.NETFLIX] == "https://netflix.com/watch/123"

    def test_content_item_optional_details(self):
        from streaming_overview_tui.search_engine.models import ContentItem

        item = ContentItem(
            tmdb_id=456,
            title="Unknown Movie",
            year=None,
            content_type="movie",
            poster_url=None,
            services=[],
            overview=None,
            rating=None,
            watch_urls={},
        )
        assert item.overview is None
        assert item.rating is None
        assert item.watch_urls == {}
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/search_engine/test_models.py::TestContentItemExtended -v`
Expected: FAIL with "unexpected keyword argument 'overview'"

**Step 3: Update ContentItem dataclass**

Modify `streaming_overview_tui/search_engine/models.py`:

```python
from dataclasses import dataclass
from dataclasses import field
from typing import Literal

from streaming_overview_tui.config_layer.config import StreamingService


@dataclass
class ContentItem:
    """A single search result item."""

    tmdb_id: int
    title: str
    year: int | None
    content_type: Literal["movie", "tv"]
    poster_url: str | None
    services: list[StreamingService]
    overview: str | None = None
    rating: float | None = None
    watch_urls: dict[StreamingService, str] = field(default_factory=dict)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/search_engine/test_models.py::TestContentItemExtended -v`
Expected: PASS

**Step 5: Update existing ContentItem test**

Update `tests/unit/search_engine/test_models.py` - the existing `TestContentItem` tests need the new fields:

```python
class TestContentItem:
    def test_create_content_item(self):
        from streaming_overview_tui.config_layer.config import StreamingService
        from streaming_overview_tui.search_engine.models import ContentItem

        item = ContentItem(
            tmdb_id=123,
            title="Test Movie",
            year=2023,
            content_type="movie",
            poster_url="https://example.com/poster.jpg",
            services=[StreamingService.NETFLIX, StreamingService.HBO_MAX],
            overview="A test movie.",
            rating=8.0,
            watch_urls={StreamingService.NETFLIX: "https://netflix.com/123"},
        )
        assert item.tmdb_id == 123
        assert item.title == "Test Movie"
        assert item.year == 2023
        assert item.content_type == "movie"
        assert item.poster_url == "https://example.com/poster.jpg"
        assert StreamingService.NETFLIX in item.services
        assert StreamingService.HBO_MAX in item.services
        assert item.overview == "A test movie."
        assert item.rating == 8.0

    def test_create_content_item_minimal(self):
        from streaming_overview_tui.search_engine.models import ContentItem

        item = ContentItem(
            tmdb_id=456,
            title="Minimal Movie",
            year=None,
            content_type="tv",
            poster_url=None,
            services=[],
        )
        assert item.tmdb_id == 456
        assert item.year is None
        assert item.poster_url is None
        assert item.services == []
        assert item.overview is None
        assert item.rating is None
        assert item.watch_urls == {}
```

**Step 6: Run all model tests**

Run: `uv run pytest tests/unit/search_engine/test_models.py -v`
Expected: All PASS

**Step 7: Update search function to populate new fields**

Modify `streaming_overview_tui/search_engine/search.py` - update the ContentItem creation (lines 81-88):

```python
        # Map providers to subscribed services with URLs
        matched_services: list[StreamingService] = []
        watch_urls: dict[StreamingService, str] = {}
        for provider in details.providers:
            service = map_provider_to_service(provider.provider_name)
            if (
                service
                and service in subscribed_services
                and service not in matched_services
            ):
                matched_services.append(service)
                watch_urls[service] = provider.link

        # Build ContentItem
        item = ContentItem(
            tmdb_id=tmdb_item.id,
            title=tmdb_item.title,
            year=tmdb_item.year,
            content_type=content_type,
            poster_url=_build_poster_url(tmdb_item.poster_path),
            services=matched_services,
            overview=details.overview,
            rating=details.rating,
            watch_urls=watch_urls,
        )
```

**Step 8: Update search tests for new fields**

Modify `tests/unit/search_engine/test_search.py` - update `test_partitions_by_subscription` to verify new fields:

Add these assertions after the existing ones (around line 151):

```python
        # Verify detail fields are populated
        assert result.available[0].overview == "..."
        assert result.available[0].rating == 8.0
        assert result.available[0].watch_urls == {StreamingService.NETFLIX: "..."}
```

**Step 9: Run all tests**

Run: `uv run pytest -v`
Expected: All 45+ tests PASS

**Step 10: Commit**

```bash
git add streaming_overview_tui/search_engine/models.py streaming_overview_tui/search_engine/search.py tests/unit/search_engine/test_models.py tests/unit/search_engine/test_search.py
git commit -m "feat(search-engine): extend ContentItem with overview, rating, watch_urls"
```

---

## Task 2: Create DetailPanel Widget

A widget that displays selected item details and watch buttons.

**Files:**
- Create: `streaming_overview_tui/tui_layer/widgets/__init__.py`
- Create: `streaming_overview_tui/tui_layer/widgets/detail_panel.py`
- Create: `tests/unit/tui_layer/__init__.py`
- Create: `tests/unit/tui_layer/test_detail_panel.py`

**Step 1: Create widgets package**

Create `streaming_overview_tui/tui_layer/widgets/__init__.py`:

```python
from streaming_overview_tui.tui_layer.widgets.detail_panel import DetailPanel

__all__ = ["DetailPanel"]
```

**Step 2: Create test directory**

Create `tests/unit/tui_layer/__init__.py`:

```python
```

**Step 3: Write failing test for DetailPanel**

Create `tests/unit/tui_layer/test_detail_panel.py`:

```python
import pytest
from textual.app import App
from textual.app import ComposeResult

from streaming_overview_tui.config_layer.config import StreamingService
from streaming_overview_tui.search_engine.models import ContentItem
from streaming_overview_tui.tui_layer.widgets.detail_panel import DetailPanel


class DetailPanelApp(App):
    """Test app for DetailPanel."""

    def __init__(self, item: ContentItem | None = None):
        super().__init__()
        self.item = item

    def compose(self) -> ComposeResult:
        yield DetailPanel(item=self.item)


class TestDetailPanel:
    @pytest.mark.asyncio
    async def test_displays_title_and_year(self):
        item = ContentItem(
            tmdb_id=123,
            title="The Batman",
            year=2022,
            content_type="movie",
            poster_url=None,
            services=[StreamingService.NETFLIX],
            overview="A dark story.",
            rating=7.8,
            watch_urls={StreamingService.NETFLIX: "https://netflix.com/123"},
        )
        async with DetailPanelApp(item).run_test() as pilot:
            panel = pilot.app.query_one(DetailPanel)
            # Check title is rendered
            assert "The Batman" in panel.render_str()
            assert "2022" in panel.render_str()

    @pytest.mark.asyncio
    async def test_displays_content_type(self):
        item = ContentItem(
            tmdb_id=123,
            title="Breaking Bad",
            year=2008,
            content_type="tv",
            poster_url=None,
            services=[],
            overview="A chemistry teacher turns to crime.",
            rating=9.5,
            watch_urls={},
        )
        async with DetailPanelApp(item).run_test() as pilot:
            panel = pilot.app.query_one(DetailPanel)
            assert "TV Show" in panel.render_str() or "tv" in panel.render_str().lower()

    @pytest.mark.asyncio
    async def test_displays_rating(self):
        item = ContentItem(
            tmdb_id=123,
            title="Test",
            year=2020,
            content_type="movie",
            poster_url=None,
            services=[],
            overview=None,
            rating=8.5,
            watch_urls={},
        )
        async with DetailPanelApp(item).run_test() as pilot:
            panel = pilot.app.query_one(DetailPanel)
            assert "8.5" in panel.render_str()

    @pytest.mark.asyncio
    async def test_hides_rating_when_none(self):
        item = ContentItem(
            tmdb_id=123,
            title="Test",
            year=2020,
            content_type="movie",
            poster_url=None,
            services=[],
            overview=None,
            rating=None,
            watch_urls={},
        )
        async with DetailPanelApp(item).run_test() as pilot:
            panel = pilot.app.query_one(DetailPanel)
            assert "Rating" not in panel.render_str()

    @pytest.mark.asyncio
    async def test_shows_no_description_when_overview_none(self):
        item = ContentItem(
            tmdb_id=123,
            title="Test",
            year=2020,
            content_type="movie",
            poster_url=None,
            services=[],
            overview=None,
            rating=None,
            watch_urls={},
        )
        async with DetailPanelApp(item).run_test() as pilot:
            panel = pilot.app.query_one(DetailPanel)
            assert "No description available" in panel.render_str()

    @pytest.mark.asyncio
    async def test_empty_when_no_item(self):
        async with DetailPanelApp(None).run_test() as pilot:
            panel = pilot.app.query_one(DetailPanel)
            rendered = panel.render_str()
            # Should be mostly empty or show placeholder
            assert "The Batman" not in rendered
```

**Step 4: Run test to verify it fails**

Run: `uv run pytest tests/unit/tui_layer/test_detail_panel.py -v`
Expected: FAIL with "No module named 'streaming_overview_tui.tui_layer.widgets.detail_panel'"

**Step 5: Implement DetailPanel widget**

Create `streaming_overview_tui/tui_layer/widgets/detail_panel.py`:

```python
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
```

**Step 6: Run tests**

Run: `uv run pytest tests/unit/tui_layer/test_detail_panel.py -v`
Expected: All PASS

**Step 7: Commit**

```bash
git add streaming_overview_tui/tui_layer/widgets/ tests/unit/tui_layer/
git commit -m "feat(tui): add DetailPanel widget with watch buttons"
```

---

## Task 3: Create ResultsList Widget

A widget showing search results in two sections: available and other.

**Files:**
- Modify: `streaming_overview_tui/tui_layer/widgets/__init__.py`
- Create: `streaming_overview_tui/tui_layer/widgets/results_list.py`
- Create: `tests/unit/tui_layer/test_results_list.py`

**Step 1: Write failing test**

Create `tests/unit/tui_layer/test_results_list.py`:

```python
import pytest
from textual.app import App
from textual.app import ComposeResult

from streaming_overview_tui.config_layer.config import StreamingService
from streaming_overview_tui.search_engine.models import ContentItem
from streaming_overview_tui.search_engine.models import SearchResult
from streaming_overview_tui.tui_layer.widgets.results_list import ResultsList


class ResultsListApp(App):
    """Test app for ResultsList."""

    def __init__(self, results: SearchResult | None = None):
        super().__init__()
        self.results = results

    def compose(self) -> ComposeResult:
        yield ResultsList(results=self.results)


def make_item(title: str, services: list[StreamingService] | None = None) -> ContentItem:
    """Helper to create test items."""
    return ContentItem(
        tmdb_id=hash(title) % 10000,
        title=title,
        year=2022,
        content_type="movie",
        poster_url=None,
        services=services or [],
        overview="Test overview",
        rating=7.5,
        watch_urls={s: f"https://example.com/{s.value}" for s in (services or [])},
    )


class TestResultsList:
    @pytest.mark.asyncio
    async def test_shows_available_section_header(self):
        results = SearchResult(
            available=[make_item("Available Movie", [StreamingService.NETFLIX])],
            other=[],
            error=None,
        )
        async with ResultsListApp(results).run_test() as pilot:
            widget = pilot.app.query_one(ResultsList)
            rendered = widget.render_str()
            assert "AVAILABLE" in rendered.upper()

    @pytest.mark.asyncio
    async def test_shows_other_section_header(self):
        results = SearchResult(
            available=[],
            other=[make_item("Other Movie")],
            error=None,
        )
        async with ResultsListApp(results).run_test() as pilot:
            widget = pilot.app.query_one(ResultsList)
            rendered = widget.render_str()
            assert "OTHER" in rendered.upper()

    @pytest.mark.asyncio
    async def test_shows_movie_title(self):
        results = SearchResult(
            available=[make_item("The Batman", [StreamingService.NETFLIX])],
            other=[],
            error=None,
        )
        async with ResultsListApp(results).run_test() as pilot:
            widget = pilot.app.query_one(ResultsList)
            rendered = widget.render_str()
            assert "The Batman" in rendered

    @pytest.mark.asyncio
    async def test_shows_service_names_for_available(self):
        results = SearchResult(
            available=[make_item("Movie", [StreamingService.NETFLIX, StreamingService.HBO_MAX])],
            other=[],
            error=None,
        )
        async with ResultsListApp(results).run_test() as pilot:
            widget = pilot.app.query_one(ResultsList)
            rendered = widget.render_str()
            assert "Netflix" in rendered

    @pytest.mark.asyncio
    async def test_empty_results_shows_message(self):
        results = SearchResult(available=[], other=[], error=None)
        async with ResultsListApp(results).run_test() as pilot:
            widget = pilot.app.query_one(ResultsList)
            rendered = widget.render_str()
            # Should show some empty state
            assert "No results" in rendered or rendered.strip() == ""

    @pytest.mark.asyncio
    async def test_no_results_shows_placeholder(self):
        async with ResultsListApp(None).run_test() as pilot:
            widget = pilot.app.query_one(ResultsList)
            rendered = widget.render_str()
            assert "Start typing" in rendered or "search" in rendered.lower()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/tui_layer/test_results_list.py -v`
Expected: FAIL with import error

**Step 3: Implement ResultsList widget**

Create `streaming_overview_tui/tui_layer/widgets/results_list.py`:

```python
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

    def watch_results(self, results: SearchResult | None) -> None:
        """React to results changes."""
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

        # Build flat list of items for navigation
        list_view = ListView()

        if self.results.available:
            container.mount(Label("AVAILABLE ON YOUR SERVICES", classes="section-header"))
            for item in self.results.available:
                self._items.append(item)
                services_str = ", ".join(s.value for s in item.services)
                year_str = f" ({item.year})" if item.year else ""
                list_view.append(
                    ListItem(
                        Label(f"{item.title}{year_str} - {services_str}"),
                        id=f"item-{item.tmdb_id}",
                    )
                )

        if self.results.other:
            container.mount(Label("OTHER RESULTS", classes="section-header"))
            for item in self.results.other:
                self._items.append(item)
                year_str = f" ({item.year})" if item.year else ""
                list_view.append(
                    ListItem(
                        Label(f"{item.title}{year_str}"),
                        id=f"item-{item.tmdb_id}",
                    )
                )

        container.mount(list_view)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle item selection."""
        # Find the item by index
        if event.list_view.index is not None and event.list_view.index < len(self._items):
            item = self._items[event.list_view.index]
            self.post_message(self.ItemSelected(item))

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Handle item highlight (for keyboard navigation)."""
        if event.list_view.index is not None and event.list_view.index < len(self._items):
            item = self._items[event.list_view.index]
            self.post_message(self.ItemSelected(item))
```

**Step 4: Update widgets __init__.py**

Modify `streaming_overview_tui/tui_layer/widgets/__init__.py`:

```python
from streaming_overview_tui.tui_layer.widgets.detail_panel import DetailPanel
from streaming_overview_tui.tui_layer.widgets.results_list import ResultsList

__all__ = ["DetailPanel", "ResultsList"]
```

**Step 5: Run tests**

Run: `uv run pytest tests/unit/tui_layer/test_results_list.py -v`
Expected: All PASS

**Step 6: Commit**

```bash
git add streaming_overview_tui/tui_layer/widgets/ tests/unit/tui_layer/test_results_list.py
git commit -m "feat(tui): add ResultsList widget with two-section display"
```

---

## Task 4: Create MainScreen with Search Integration

Rewrite MainScreen to compose the widgets and handle search.

**Files:**
- Modify: `streaming_overview_tui/tui_layer/main_screen.py`
- Create: `tests/unit/tui_layer/test_main_screen.py`

**Step 1: Write failing test**

Create `tests/unit/tui_layer/test_main_screen.py`:

```python
import pytest
from textual.app import App
from textual.app import ComposeResult
from textual.widgets import Input

from streaming_overview_tui.tui_layer.main_screen import MainScreen
from streaming_overview_tui.tui_layer.widgets import DetailPanel
from streaming_overview_tui.tui_layer.widgets import ResultsList


class MainScreenApp(App):
    """Test app for MainScreen."""

    def compose(self) -> ComposeResult:
        yield MainScreen()


class TestMainScreen:
    @pytest.mark.asyncio
    async def test_has_search_input(self):
        async with MainScreenApp().run_test() as pilot:
            inputs = pilot.app.query(Input)
            assert len(inputs) >= 1

    @pytest.mark.asyncio
    async def test_has_results_list(self):
        async with MainScreenApp().run_test() as pilot:
            results_list = pilot.app.query(ResultsList)
            assert len(results_list) == 1

    @pytest.mark.asyncio
    async def test_has_detail_panel(self):
        async with MainScreenApp().run_test() as pilot:
            detail_panel = pilot.app.query(DetailPanel)
            assert len(detail_panel) == 1

    @pytest.mark.asyncio
    async def test_shows_placeholder_initially(self):
        async with MainScreenApp().run_test() as pilot:
            results_list = pilot.app.query_one(ResultsList)
            rendered = results_list.render_str()
            assert "Start typing" in rendered or "search" in rendered.lower()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/tui_layer/test_main_screen.py -v`
Expected: FAIL (current MainScreen doesn't have these widgets)

**Step 3: Implement MainScreen**

Rewrite `streaming_overview_tui/tui_layer/main_screen.py`:

```python
import webbrowser

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button
from textual.widgets import Footer
from textual.widgets import Header
from textual.widgets import Input
from textual.widgets import Static
from textual.worker import Worker
from textual.worker import get_current_worker

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
        self._search_timer: float | None = None
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
            self.set_timer(0, lambda: None)  # Cancel by setting new timer

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
        worker = get_current_worker()
        if not worker.is_cancelled:
            self.call_from_thread(self._set_status, "Searching...")

        # Get subscribed services
        subscriptions = [
            StreamingService(s) for s in self._user_config.subscriptions
            if s in [ss.value for ss in StreamingService]
        ]

        # Perform search
        result = await search(query, subscriptions)

        # Update UI if not cancelled
        if not worker.is_cancelled:
            self.call_from_thread(self._update_results, result)

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
```

**Step 4: Run tests**

Run: `uv run pytest tests/unit/tui_layer/test_main_screen.py -v`
Expected: All PASS

**Step 5: Run all tests**

Run: `uv run pytest -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add streaming_overview_tui/tui_layer/main_screen.py tests/unit/tui_layer/test_main_screen.py
git commit -m "feat(tui): rewrite MainScreen with search, results, and detail panel"
```

---

## Task 5: Manual Testing and Polish

Test the full application flow manually.

**Step 1: Run the application**

Run: `uv run streaming-tui`

**Step 2: Test the flow**

1. Type a search query (e.g., "batman")
2. Wait for results to appear
3. Navigate with arrow keys
4. Verify detail panel updates
5. Press Enter on a watch button
6. Verify browser opens

**Step 3: Fix any issues found**

Address any bugs or UX issues discovered during manual testing.

**Step 4: Run pre-commit**

Run: `pre-commit run --all-files`
Fix any formatting issues.

**Step 5: Final commit**

```bash
git add -A
git commit -m "chore(tui): polish and fixes from manual testing"
```

---

## Task 6: Update TUI Layer Exports

Ensure public interface is exported.

**Files:**
- Modify: `streaming_overview_tui/tui_layer/__init__.py`

**Step 1: Update exports**

Modify `streaming_overview_tui/tui_layer/__init__.py`:

```python
from streaming_overview_tui.tui_layer.main_screen import MainScreen
from streaming_overview_tui.tui_layer.setup_screen import SetupComplete
from streaming_overview_tui.tui_layer.setup_screen import SetupScreen
from streaming_overview_tui.tui_layer.stream_app import StreamApp
from streaming_overview_tui.tui_layer.widgets import DetailPanel
from streaming_overview_tui.tui_layer.widgets import ResultsList

__all__ = [
    "DetailPanel",
    "MainScreen",
    "ResultsList",
    "SetupComplete",
    "SetupScreen",
    "StreamApp",
]
```

**Step 2: Run all tests**

Run: `uv run pytest -v`
Expected: All PASS

**Step 3: Commit**

```bash
git add streaming_overview_tui/tui_layer/__init__.py
git commit -m "feat(tui): export widgets from tui_layer package"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Extend ContentItem with details | models.py, search.py, tests |
| 2 | Create DetailPanel widget | widgets/detail_panel.py, tests |
| 3 | Create ResultsList widget | widgets/results_list.py, tests |
| 4 | Rewrite MainScreen | main_screen.py, tests |
| 5 | Manual testing | - |
| 6 | Update exports | tui_layer/__init__.py |
