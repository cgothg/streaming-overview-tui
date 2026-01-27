from streaming_overview_tui.config_layer.config import StreamingService
from streaming_overview_tui.search_engine.models import ContentItem
from streaming_overview_tui.search_engine.models import map_provider_to_service
from streaming_overview_tui.search_engine.models import SearchResult


class TestContentItem:
    def test_create_content_item(self):
        item = ContentItem(
            tmdb_id=123,
            title="The Batman",
            year=2022,
            content_type="movie",
            poster_url="https://image.tmdb.org/t/p/w500/test.jpg",
            services=[StreamingService.HBO_MAX],
        )
        assert item.tmdb_id == 123
        assert item.title == "The Batman"
        assert item.year == 2022
        assert item.content_type == "movie"
        assert item.poster_url == "https://image.tmdb.org/t/p/w500/test.jpg"
        assert item.services == [StreamingService.HBO_MAX]

    def test_create_content_item_minimal(self):
        item = ContentItem(
            tmdb_id=456,
            title="Unknown Show",
            year=None,
            content_type="tv",
            poster_url=None,
            services=[],
        )
        assert item.tmdb_id == 456
        assert item.year is None
        assert item.poster_url is None
        assert item.services == []


class TestSearchResult:
    def test_create_search_result(self):
        available_item = ContentItem(
            tmdb_id=123,
            title="Available Movie",
            year=2022,
            content_type="movie",
            poster_url=None,
            services=[StreamingService.NETFLIX],
        )
        other_item = ContentItem(
            tmdb_id=456,
            title="Other Movie",
            year=2021,
            content_type="movie",
            poster_url=None,
            services=[],
        )
        result = SearchResult(
            available=[available_item],
            other=[other_item],
            error=None,
        )
        assert len(result.available) == 1
        assert len(result.other) == 1
        assert result.error is None

    def test_create_search_result_with_error(self):
        result = SearchResult(
            available=[],
            other=[],
            error="TMDB API unavailable - please try again later",
        )
        assert result.available == []
        assert result.other == []
        assert result.error == "TMDB API unavailable - please try again later"


class TestProviderMapping:
    def test_map_netflix(self):
        assert map_provider_to_service("Netflix") == StreamingService.NETFLIX

    def test_map_hbo_max(self):
        # TMDB uses "Max" for HBO Max
        assert map_provider_to_service("Max") == StreamingService.HBO_MAX
        assert map_provider_to_service("HBO Max") == StreamingService.HBO_MAX

    def test_map_amazon_prime(self):
        assert (
            map_provider_to_service("Amazon Prime Video")
            == StreamingService.AMAZON_PRIME
        )

    def test_map_disney_plus(self):
        assert map_provider_to_service("Disney Plus") == StreamingService.DISNEY_PLUS

    def test_map_unknown_returns_none(self):
        assert map_provider_to_service("Apple TV+") is None
        assert map_provider_to_service("Hulu") is None
