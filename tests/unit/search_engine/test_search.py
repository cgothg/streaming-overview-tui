from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import httpx
import pytest

from streaming_overview_tui.config_layer.config import StreamingService
from streaming_overview_tui.data_layer.models import Movie
from streaming_overview_tui.data_layer.models import StreamingProvider
from streaming_overview_tui.data_layer.models import TMDBSearchResult
from streaming_overview_tui.search_engine.search import search


class TestSearchValidation:
    @pytest.mark.asyncio
    async def test_short_query_returns_empty_results(self):
        result = await search(
            query="a",
            subscribed_services=[StreamingService.NETFLIX],
        )
        assert result.available == []
        assert result.other == []
        assert result.error is None

    @pytest.mark.asyncio
    async def test_empty_query_returns_empty_results(self):
        result = await search(
            query="",
            subscribed_services=[StreamingService.NETFLIX],
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
        )

        mock_repository.search.assert_called_once_with("batman")

    @pytest.mark.asyncio
    async def test_short_query_does_not_call_repository(self, mock_repository):
        mock_repository.search = AsyncMock(return_value=[])

        await search(
            query="b",
            subscribed_services=[StreamingService.NETFLIX],
        )

        mock_repository.search.assert_not_called()


class TestSearchPartitioning:
    @pytest.fixture
    def mock_repository(self):
        with patch(
            "streaming_overview_tui.search_engine.search.ContentRepository"
        ) as mock:
            repo_instance = MagicMock()
            mock.return_value = repo_instance
            yield repo_instance

    @pytest.mark.asyncio
    async def test_partitions_by_subscription(self, mock_repository):
        # TMDB search returns two movies
        mock_repository.search = AsyncMock(
            return_value=[
                TMDBSearchResult(
                    id=123,
                    title="Movie on Netflix",
                    year=2022,
                    content_type="movie",
                    poster_path="/netflix.jpg",
                    rating=8.0,
                ),
                TMDBSearchResult(
                    id=456,
                    title="Movie on Disney",
                    year=2021,
                    content_type="movie",
                    poster_path="/disney.jpg",
                    rating=7.5,
                ),
            ]
        )

        # Movie details with providers
        mock_repository.get_movie = AsyncMock(
            side_effect=[
                Movie(
                    id=123,
                    title="Movie on Netflix",
                    release_year=2022,
                    overview="...",
                    rating=8.0,
                    poster_path="/netflix.jpg",
                    providers=[
                        StreamingProvider(
                            provider_id=8, provider_name="Netflix", link="..."
                        )
                    ],
                ),
                Movie(
                    id=456,
                    title="Movie on Disney",
                    release_year=2021,
                    overview="...",
                    rating=7.5,
                    poster_path="/disney.jpg",
                    providers=[
                        StreamingProvider(
                            provider_id=337, provider_name="Disney Plus", link="..."
                        )
                    ],
                ),
            ]
        )

        result = await search(
            query="movie",
            subscribed_services=[
                StreamingService.NETFLIX
            ],  # Only subscribed to Netflix
        )

        # Movie on Netflix should be in "available"
        assert len(result.available) == 1
        assert result.available[0].title == "Movie on Netflix"
        assert result.available[0].services == [StreamingService.NETFLIX]

        # Verify detail fields are populated
        assert result.available[0].overview == "..."
        assert result.available[0].rating == 8.0
        assert result.available[0].watch_urls == {StreamingService.NETFLIX: "..."}

        # Movie on Disney should be in "other"
        assert len(result.other) == 1
        assert result.other[0].title == "Movie on Disney"
        assert result.other[0].services == []  # No subscribed services

    @pytest.mark.asyncio
    async def test_no_providers_goes_to_other(self, mock_repository):
        mock_repository.search = AsyncMock(
            return_value=[
                TMDBSearchResult(
                    id=789,
                    title="Movie No Streaming",
                    year=2020,
                    content_type="movie",
                    poster_path=None,
                    rating=6.0,
                ),
            ]
        )

        mock_repository.get_movie = AsyncMock(
            return_value=Movie(
                id=789,
                title="Movie No Streaming",
                release_year=2020,
                overview="...",
                rating=6.0,
                poster_path=None,
                providers=[],  # No streaming providers
            )
        )

        result = await search(
            query="movie",
            subscribed_services=[StreamingService.NETFLIX],
        )

        assert len(result.available) == 0
        assert len(result.other) == 1
        assert result.other[0].title == "Movie No Streaming"


class TestSearchErrorHandling:
    @pytest.fixture
    def mock_repository(self):
        with patch(
            "streaming_overview_tui.search_engine.search.ContentRepository"
        ) as mock:
            repo_instance = MagicMock()
            mock.return_value = repo_instance
            yield repo_instance

    @pytest.mark.asyncio
    async def test_timeout_error_returns_descriptive_message(self, mock_repository):
        mock_repository.search = AsyncMock(
            side_effect=httpx.TimeoutException("Connection timeout")
        )

        result = await search(
            query="batman",
            subscribed_services=[StreamingService.NETFLIX],
        )

        assert result.available == []
        assert result.other == []
        assert "TMDB API" in result.error
        assert "timeout" in result.error.lower()

    @pytest.mark.asyncio
    async def test_http_error_returns_descriptive_message(self, mock_repository):
        mock_repository.search = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Rate limited",
                request=MagicMock(),
                response=MagicMock(status_code=429),
            )
        )

        result = await search(
            query="batman",
            subscribed_services=[StreamingService.NETFLIX],
        )

        assert result.available == []
        assert result.other == []
        assert "TMDB API" in result.error

    @pytest.mark.asyncio
    async def test_generic_error_returns_descriptive_message(self, mock_repository):
        mock_repository.search = AsyncMock(side_effect=Exception("Unknown error"))

        result = await search(
            query="batman",
            subscribed_services=[StreamingService.NETFLIX],
        )

        assert result.available == []
        assert result.other == []
        assert "TMDB API" in result.error
