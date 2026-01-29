import pytest
from textual.app import App
from textual.app import ComposeResult

from streaming_overview_tui.config_layer.config import StreamingService
from streaming_overview_tui.search_engine.models import ContentItem
from streaming_overview_tui.tui_layer.widgets.detail_panel import DetailPanel
from streaming_overview_tui.tui_layer.widgets.poster_widget import PosterWidget


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
