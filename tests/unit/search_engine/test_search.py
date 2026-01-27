import pytest

from streaming_overview_tui.config_layer.config import StreamingService
from streaming_overview_tui.search_engine.search import search


class TestSearchValidation:
    @pytest.mark.asyncio
    async def test_short_query_returns_empty_results(self):
        result = await search(
            query="a",
            subscribed_services=[StreamingService.NETFLIX],
            region="DK",
        )
        assert result.available == []
        assert result.other == []
        assert result.error is None

    @pytest.mark.asyncio
    async def test_empty_query_returns_empty_results(self):
        result = await search(
            query="",
            subscribed_services=[StreamingService.NETFLIX],
            region="DK",
        )
        assert result.available == []
        assert result.other == []
        assert result.error is None
