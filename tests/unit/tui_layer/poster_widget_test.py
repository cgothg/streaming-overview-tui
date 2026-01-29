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
