from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

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


class TestSearchTMDBIntegration:
    @pytest.fixture
    def mock_repository(self):
        with patch(
            "streaming_overview_tui.search_engine.search.ContentRepository"
        ) as mock:
            repo_instance = MagicMock()
            mock.return_value = repo_instance
            yield repo_instance

    @pytest.mark.asyncio
    async def test_search_calls_repository(self, mock_repository):
        mock_repository.search = AsyncMock(return_value=[])

        await search(
            query="batman",
            subscribed_services=[StreamingService.NETFLIX],
            region="DK",
        )

        mock_repository.search.assert_called_once_with("batman")

    @pytest.mark.asyncio
    async def test_short_query_does_not_call_repository(self, mock_repository):
        mock_repository.search = AsyncMock(return_value=[])

        await search(
            query="b",
            subscribed_services=[StreamingService.NETFLIX],
            region="DK",
        )

        mock_repository.search.assert_not_called()
