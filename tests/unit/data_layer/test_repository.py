from datetime import datetime
from datetime import timedelta
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from streaming_overview_tui.data_layer.models import CachedMovie
from streaming_overview_tui.data_layer.repository import CACHE_TTL_DAYS
from streaming_overview_tui.data_layer.repository import ContentRepository


class TestContentRepository:
    @pytest.fixture
    def mock_tmdb_client(self):
        with patch(
            "streaming_overview_tui.data_layer.repository.TMDBClient"
        ) as mock:
            yield mock

    @pytest.fixture
    def mock_init_db(self):
        with patch(
            "streaming_overview_tui.data_layer.repository.init_db"
        ) as mock:
            yield mock

    @pytest.fixture
    def mock_session(self):
        with patch(
            "streaming_overview_tui.data_layer.repository.get_session"
        ) as mock:
            session = MagicMock()
            mock.return_value.__enter__ = MagicMock(return_value=session)
            mock.return_value.__exit__ = MagicMock(return_value=False)
            yield session

    @pytest.fixture
    def mock_user_config(self):
        with patch(
            "streaming_overview_tui.data_layer.repository.load_user_config"
        ) as mock:
            config = MagicMock()
            config.region = "DK"
            mock.return_value = config
            yield config

    def test_is_cache_fresh_when_fresh(self, mock_tmdb_client, mock_init_db):
        repo = ContentRepository()
        cached_at = datetime.utcnow() - timedelta(days=1)
        assert repo._is_cache_fresh(cached_at) is True

    def test_is_cache_fresh_when_expired(self, mock_tmdb_client, mock_init_db):
        repo = ContentRepository()
        cached_at = datetime.utcnow() - timedelta(days=CACHE_TTL_DAYS + 1)
        assert repo._is_cache_fresh(cached_at) is False

    def test_is_cache_fresh_at_boundary(self, mock_tmdb_client, mock_init_db):
        repo = ContentRepository()
        # Exactly at TTL should still be fresh
        cached_at = datetime.utcnow() - timedelta(days=CACHE_TTL_DAYS - 1)
        assert repo._is_cache_fresh(cached_at) is True

    def test_extract_year_valid(self, mock_tmdb_client, mock_init_db):
        repo = ContentRepository()
        assert repo._extract_year("2023-05-15") == 2023

    def test_extract_year_none(self, mock_tmdb_client, mock_init_db):
        repo = ContentRepository()
        assert repo._extract_year(None) is None

    def test_extract_year_empty(self, mock_tmdb_client, mock_init_db):
        repo = ContentRepository()
        assert repo._extract_year("") is None

    def test_extract_year_invalid(self, mock_tmdb_client, mock_init_db):
        repo = ContentRepository()
        assert repo._extract_year("invalid") is None

    def test_parse_providers_with_flatrate(self, mock_tmdb_client, mock_init_db):
        repo = ContentRepository()
        watch_providers = {
            "results": {
                "DK": {
                    "link": "https://www.themoviedb.org/movie/123/watch",
                    "flatrate": [
                        {"provider_id": 8, "provider_name": "Netflix"},
                        {"provider_id": 337, "provider_name": "Disney Plus"},
                    ],
                }
            }
        }
        providers = repo._parse_providers(watch_providers, "DK")
        assert len(providers) == 2
        assert providers[0].provider_id == 8
        assert providers[0].provider_name == "Netflix"
        assert providers[1].provider_id == 337
        assert providers[1].provider_name == "Disney Plus"

    def test_parse_providers_no_region(self, mock_tmdb_client, mock_init_db):
        repo = ContentRepository()
        watch_providers = {
            "results": {
                "US": {
                    "flatrate": [{"provider_id": 8, "provider_name": "Netflix"}]
                }
            }
        }
        providers = repo._parse_providers(watch_providers, "DK")
        assert len(providers) == 0

    def test_parse_providers_no_flatrate(self, mock_tmdb_client, mock_init_db):
        repo = ContentRepository()
        watch_providers = {
            "results": {
                "DK": {
                    "rent": [{"provider_id": 2, "provider_name": "Apple TV"}]
                }
            }
        }
        providers = repo._parse_providers(watch_providers, "DK")
        assert len(providers) == 0

    @pytest.mark.asyncio
    async def test_search_returns_results(
        self, mock_tmdb_client, mock_init_db, mock_user_config
    ):
        mock_client_instance = mock_tmdb_client.return_value
        mock_client_instance.search_multi = AsyncMock(
            return_value={
                "results": [
                    {
                        "id": 123,
                        "media_type": "movie",
                        "title": "Test Movie",
                        "release_date": "2023-05-15",
                        "poster_path": "/test.jpg",
                        "vote_average": 8.5,
                    },
                    {
                        "id": 456,
                        "media_type": "tv",
                        "name": "Test Show",
                        "first_air_date": "2022-01-01",
                        "poster_path": "/show.jpg",
                        "vote_average": 9.0,
                    },
                    {
                        "id": 789,
                        "media_type": "person",
                        "name": "Actor Name",
                    },
                ]
            }
        )

        repo = ContentRepository()
        results = await repo.search("test")

        assert len(results) == 2
        assert results[0].id == 123
        assert results[0].title == "Test Movie"
        assert results[0].content_type == "movie"
        assert results[0].year == 2023
        assert results[1].id == 456
        assert results[1].title == "Test Show"
        assert results[1].content_type == "show"
        assert results[1].year == 2022

    @pytest.mark.asyncio
    async def test_get_movie_cache_hit(
        self,
        mock_tmdb_client,
        mock_init_db,
        mock_session,
        mock_user_config,
    ):
        cached_movie = CachedMovie(
            id=123,
            title="Cached Movie",
            release_year=2023,
            overview="Cached overview",
            rating=8.5,
            poster_path="/cached.jpg",
            cached_at=datetime.utcnow(),  # Fresh cache
        )
        mock_session.get.return_value = cached_movie
        mock_session.exec.return_value.all.return_value = []

        repo = ContentRepository()
        movie = await repo.get_movie(123)

        assert movie is not None
        assert movie.id == 123
        assert movie.title == "Cached Movie"
        # API should not be called when cache is fresh
        mock_tmdb_client.return_value.get_movie.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_movie_cache_miss(
        self,
        mock_tmdb_client,
        mock_init_db,
        mock_session,
        mock_user_config,
    ):
        mock_session.get.return_value = None
        mock_session.exec.return_value.all.return_value = []

        mock_client_instance = mock_tmdb_client.return_value
        mock_client_instance.get_movie = AsyncMock(
            return_value={
                "id": 123,
                "title": "API Movie",
                "release_date": "2023-05-15",
                "overview": "API overview",
                "vote_average": 9.0,
                "poster_path": "/api.jpg",
                "watch/providers": {"results": {}},
            }
        )

        repo = ContentRepository()
        movie = await repo.get_movie(123)

        assert movie is not None
        assert movie.id == 123
        assert movie.title == "API Movie"
        mock_client_instance.get_movie.assert_called_once_with(123)

    @pytest.mark.asyncio
    async def test_get_movie_api_failure_returns_stale_cache(
        self,
        mock_tmdb_client,
        mock_init_db,
        mock_session,
        mock_user_config,
    ):
        # First call returns expired cache
        expired_movie = CachedMovie(
            id=123,
            title="Stale Movie",
            release_year=2020,
            overview="Stale overview",
            rating=7.0,
            poster_path="/stale.jpg",
            cached_at=datetime.utcnow() - timedelta(days=CACHE_TTL_DAYS + 10),
        )
        mock_session.get.return_value = expired_movie
        mock_session.exec.return_value.all.return_value = []

        mock_client_instance = mock_tmdb_client.return_value
        mock_client_instance.get_movie = AsyncMock(side_effect=Exception("API Error"))

        repo = ContentRepository()
        movie = await repo.get_movie(123)

        assert movie is not None
        assert movie.id == 123
        assert movie.title == "Stale Movie"

    @pytest.mark.asyncio
    async def test_get_movie_api_failure_no_cache_raises(
        self,
        mock_tmdb_client,
        mock_init_db,
        mock_session,
        mock_user_config,
    ):
        mock_session.get.return_value = None

        mock_client_instance = mock_tmdb_client.return_value
        mock_client_instance.get_movie = AsyncMock(side_effect=Exception("API Error"))

        repo = ContentRepository()

        with pytest.raises(Exception, match="API Error"):
            await repo.get_movie(123)
