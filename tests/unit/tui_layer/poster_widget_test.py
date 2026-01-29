import io
from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest
from PIL import Image
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

        with patch("httpx.Client.get", return_value=mock_response):
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
