from datetime import datetime

from streaming_overview_tui.data_layer.models import CachedMovie
from streaming_overview_tui.data_layer.models import CachedShow
from streaming_overview_tui.data_layer.models import Movie
from streaming_overview_tui.data_layer.models import SearchResult
from streaming_overview_tui.data_layer.models import Show
from streaming_overview_tui.data_layer.models import StreamingAvailability
from streaming_overview_tui.data_layer.models import StreamingProvider


class TestCachedMovie:
    def test_create_cached_movie(self):
        movie = CachedMovie(
            id=123,
            title="Test Movie",
            release_year=2023,
            overview="A test movie",
            rating=8.5,
            poster_path="/test.jpg",
        )
        assert movie.id == 123
        assert movie.title == "Test Movie"
        assert movie.release_year == 2023
        assert movie.overview == "A test movie"
        assert movie.rating == 8.5
        assert movie.poster_path == "/test.jpg"
        assert isinstance(movie.cached_at, datetime)

    def test_create_cached_movie_minimal(self):
        movie = CachedMovie(id=123, title="Test Movie")
        assert movie.id == 123
        assert movie.title == "Test Movie"
        assert movie.release_year is None
        assert movie.overview is None
        assert movie.rating is None
        assert movie.poster_path is None


class TestCachedShow:
    def test_create_cached_show(self):
        show = CachedShow(
            id=456,
            title="Test Show",
            first_air_year=2022,
            overview="A test show",
            rating=9.0,
            poster_path="/show.jpg",
        )
        assert show.id == 456
        assert show.title == "Test Show"
        assert show.first_air_year == 2022
        assert show.overview == "A test show"
        assert show.rating == 9.0
        assert show.poster_path == "/show.jpg"
        assert isinstance(show.cached_at, datetime)


class TestStreamingAvailability:
    def test_create_streaming_availability(self):
        availability = StreamingAvailability(
            content_type="movie",
            content_id=123,
            provider_id=8,
            provider_name="Netflix",
            region="DK",
            link="https://www.netflix.com/title/123",
        )
        assert availability.content_type == "movie"
        assert availability.content_id == 123
        assert availability.provider_id == 8
        assert availability.provider_name == "Netflix"
        assert availability.region == "DK"
        assert availability.link == "https://www.netflix.com/title/123"


class TestSearchResult:
    def test_create_search_result(self):
        result = SearchResult(
            id=123,
            title="Test Movie",
            year=2023,
            content_type="movie",
            poster_path="/test.jpg",
            rating=8.5,
        )
        assert result.id == 123
        assert result.title == "Test Movie"
        assert result.year == 2023
        assert result.content_type == "movie"
        assert result.poster_path == "/test.jpg"
        assert result.rating == 8.5


class TestStreamingProvider:
    def test_create_streaming_provider(self):
        provider = StreamingProvider(
            provider_id=8,
            provider_name="Netflix",
            link="https://www.netflix.com/title/123",
        )
        assert provider.provider_id == 8
        assert provider.provider_name == "Netflix"
        assert provider.link == "https://www.netflix.com/title/123"


class TestMovie:
    def test_create_movie(self):
        providers = [
            StreamingProvider(
                provider_id=8,
                provider_name="Netflix",
                link="https://www.netflix.com/title/123",
            )
        ]
        movie = Movie(
            id=123,
            title="Test Movie",
            release_year=2023,
            overview="A test movie",
            rating=8.5,
            poster_path="/test.jpg",
            providers=providers,
        )
        assert movie.id == 123
        assert movie.title == "Test Movie"
        assert movie.release_year == 2023
        assert movie.overview == "A test movie"
        assert movie.rating == 8.5
        assert movie.poster_path == "/test.jpg"
        assert len(movie.providers) == 1
        assert movie.providers[0].provider_name == "Netflix"


class TestShow:
    def test_create_show(self):
        providers = [
            StreamingProvider(
                provider_id=337,
                provider_name="Disney Plus",
                link="https://www.disneyplus.com/shows/123",
            )
        ]
        show = Show(
            id=456,
            title="Test Show",
            first_air_year=2022,
            overview="A test show",
            rating=9.0,
            poster_path="/show.jpg",
            providers=providers,
        )
        assert show.id == 456
        assert show.title == "Test Show"
        assert show.first_air_year == 2022
        assert show.overview == "A test show"
        assert show.rating == 9.0
        assert show.poster_path == "/show.jpg"
        assert len(show.providers) == 1
        assert show.providers[0].provider_name == "Disney Plus"
