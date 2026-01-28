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


def make_item(
    title: str, services: list[StreamingService] | None = None
) -> ContentItem:
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
            available=[
                make_item("Movie", [StreamingService.NETFLIX, StreamingService.HBO_MAX])
            ],
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
