from datetime import datetime
from datetime import timedelta
from datetime import timezone

from sqlmodel import select

from streaming_overview_tui.config_layer import load_user_config
from streaming_overview_tui.data_layer.database import get_session
from streaming_overview_tui.data_layer.database import init_db
from streaming_overview_tui.data_layer.models import CachedMovie
from streaming_overview_tui.data_layer.models import CachedShow
from streaming_overview_tui.data_layer.models import Movie
from streaming_overview_tui.data_layer.models import SearchResult
from streaming_overview_tui.data_layer.models import Show
from streaming_overview_tui.data_layer.models import StreamingAvailability
from streaming_overview_tui.data_layer.models import StreamingProvider
from streaming_overview_tui.data_layer.tmdb_client import TMDBClient

# Cache TTL in days
CACHE_TTL_DAYS = 30


class ContentRepository:
    """Repository for movies and TV shows with caching."""

    def __init__(self):
        self._client = TMDBClient()
        init_db()

    def _is_cache_fresh(self, cached_at: datetime) -> bool:
        """Check if cached data is still fresh."""
        expiry = cached_at + timedelta(days=CACHE_TTL_DAYS)
        return datetime.now(timezone.utc) < expiry

    def _extract_year(self, date_str: str | None) -> int | None:
        """Extract year from TMDB date string (YYYY-MM-DD)."""
        if not date_str:
            return None
        try:
            return int(date_str[:4])
        except (ValueError, IndexError):
            return None

    def _parse_providers(
        self, watch_providers: dict, region: str
    ) -> list[StreamingProvider]:
        """Parse watch providers response for a region.

        Only returns subscription (flatrate) providers.
        """
        providers = []
        results = watch_providers.get("results", {})
        region_data = results.get(region, {})
        flatrate = region_data.get("flatrate", [])

        for provider in flatrate:
            providers.append(
                StreamingProvider(
                    provider_id=provider["provider_id"],
                    provider_name=provider["provider_name"],
                    link=region_data.get("link", ""),
                )
            )

        return providers

    async def search(self, query: str) -> list[SearchResult]:
        """Search for movies and TV shows.

        Returns cached results if fresh, otherwise fetches from TMDB.
        """
        # Always fetch from API for search (search results change frequently)
        data = await self._client.search_multi(query)
        results = []

        for item in data.get("results", []):
            media_type = item.get("media_type")
            if media_type not in ("movie", "tv"):
                continue

            if media_type == "movie":
                results.append(
                    SearchResult(
                        id=item["id"],
                        title=item.get("title", "Unknown"),
                        year=self._extract_year(item.get("release_date")),
                        content_type="movie",
                        poster_path=item.get("poster_path"),
                        rating=item.get("vote_average"),
                    )
                )
            else:  # tv
                results.append(
                    SearchResult(
                        id=item["id"],
                        title=item.get("name", "Unknown"),
                        year=self._extract_year(item.get("first_air_date")),
                        content_type="show",
                        poster_path=item.get("poster_path"),
                        rating=item.get("vote_average"),
                    )
                )

        return results

    async def get_movie(self, movie_id: int) -> Movie | None:
        """Get movie details with streaming availability.

        Returns cached data if fresh, otherwise fetches from TMDB.
        """
        region = load_user_config().region

        # Check cache
        with get_session() as session:
            cached = session.get(CachedMovie, movie_id)
            if cached and self._is_cache_fresh(cached.cached_at):
                providers = self._get_cached_providers("movie", movie_id, region)
                return Movie(
                    id=cached.id,
                    title=cached.title,
                    release_year=cached.release_year,
                    overview=cached.overview,
                    rating=cached.rating,
                    poster_path=cached.poster_path,
                    providers=providers,
                )

        # Fetch from API
        try:
            data = await self._client.get_movie(movie_id)
        except Exception:
            # On API failure, return stale cache if available
            with get_session() as session:
                cached = session.get(CachedMovie, movie_id)
                if cached:
                    providers = self._get_cached_providers("movie", movie_id, region)
                    return Movie(
                        id=cached.id,
                        title=cached.title,
                        release_year=cached.release_year,
                        overview=cached.overview,
                        rating=cached.rating,
                        poster_path=cached.poster_path,
                        providers=providers,
                    )
            raise

        # Cache and return
        providers = self._parse_providers(data.get("watch/providers", {}), region)
        movie = self._cache_movie(data, providers, region)
        return movie

    async def get_show(self, show_id: int) -> Show | None:
        """Get TV show details with streaming availability.

        Returns cached data if fresh, otherwise fetches from TMDB.
        """
        region = load_user_config().region

        # Check cache
        with get_session() as session:
            cached = session.get(CachedShow, show_id)
            if cached and self._is_cache_fresh(cached.cached_at):
                providers = self._get_cached_providers("show", show_id, region)
                return Show(
                    id=cached.id,
                    title=cached.title,
                    first_air_year=cached.first_air_year,
                    overview=cached.overview,
                    rating=cached.rating,
                    poster_path=cached.poster_path,
                    providers=providers,
                )

        # Fetch from API
        try:
            data = await self._client.get_show(show_id)
        except Exception:
            # On API failure, return stale cache if available
            with get_session() as session:
                cached = session.get(CachedShow, show_id)
                if cached:
                    providers = self._get_cached_providers("show", show_id, region)
                    return Show(
                        id=cached.id,
                        title=cached.title,
                        first_air_year=cached.first_air_year,
                        overview=cached.overview,
                        rating=cached.rating,
                        poster_path=cached.poster_path,
                        providers=providers,
                    )
            raise

        # Cache and return
        providers = self._parse_providers(data.get("watch/providers", {}), region)
        show = self._cache_show(data, providers, region)
        return show

    async def refresh(self, content_type: str, content_id: int) -> None:
        """Force refresh from API, bypassing cache."""
        if content_type == "movie":
            await self._refresh_movie(content_id)
        elif content_type == "show":
            await self._refresh_show(content_id)

    async def _refresh_movie(self, movie_id: int) -> Movie:
        """Force refresh movie from API."""
        region = load_user_config().region
        data = await self._client.get_movie(movie_id)
        providers = self._parse_providers(data.get("watch/providers", {}), region)
        return self._cache_movie(data, providers, region)

    async def _refresh_show(self, show_id: int) -> Show:
        """Force refresh show from API."""
        region = load_user_config().region
        data = await self._client.get_show(show_id)
        providers = self._parse_providers(data.get("watch/providers", {}), region)
        return self._cache_show(data, providers, region)

    async def get_streaming_providers(
        self, content_type: str, content_id: int
    ) -> list[StreamingProvider]:
        """Get streaming availability for content in user's region."""
        region = load_user_config().region
        return self._get_cached_providers(content_type, content_id, region)

    def _get_cached_providers(
        self, content_type: str, content_id: int, region: str
    ) -> list[StreamingProvider]:
        """Get providers from cache."""
        with get_session() as session:
            statement = select(StreamingAvailability).where(
                StreamingAvailability.content_type == content_type,
                StreamingAvailability.content_id == content_id,
                StreamingAvailability.region == region,
            )
            results = session.exec(statement).all()
            return [
                StreamingProvider(
                    provider_id=r.provider_id,
                    provider_name=r.provider_name,
                    link=r.link,
                )
                for r in results
            ]

    def _cache_movie(
        self, data: dict, providers: list[StreamingProvider], region: str
    ) -> Movie:
        """Cache movie data and return Movie object."""
        now = datetime.now(timezone.utc)

        cached_movie = CachedMovie(
            id=data["id"],
            title=data.get("title", "Unknown"),
            release_year=self._extract_year(data.get("release_date")),
            overview=data.get("overview"),
            rating=data.get("vote_average"),
            poster_path=data.get("poster_path"),
            cached_at=now,
        )

        with get_session() as session:
            # Upsert movie
            existing = session.get(CachedMovie, cached_movie.id)
            if existing:
                existing.title = cached_movie.title
                existing.release_year = cached_movie.release_year
                existing.overview = cached_movie.overview
                existing.rating = cached_movie.rating
                existing.poster_path = cached_movie.poster_path
                existing.cached_at = now
            else:
                session.add(cached_movie)

            # Update streaming availability
            statement = select(StreamingAvailability).where(
                StreamingAvailability.content_type == "movie",
                StreamingAvailability.content_id == data["id"],
                StreamingAvailability.region == region,
            )
            old_providers = session.exec(statement).all()
            for p in old_providers:
                session.delete(p)

            for provider in providers:
                session.add(
                    StreamingAvailability(
                        content_type="movie",
                        content_id=data["id"],
                        provider_id=provider.provider_id,
                        provider_name=provider.provider_name,
                        region=region,
                        link=provider.link,
                        cached_at=now,
                    )
                )

            session.commit()

        return Movie(
            id=data["id"],
            title=data.get("title", "Unknown"),
            release_year=self._extract_year(data.get("release_date")),
            overview=data.get("overview"),
            rating=data.get("vote_average"),
            poster_path=data.get("poster_path"),
            providers=providers,
        )

    def _cache_show(
        self, data: dict, providers: list[StreamingProvider], region: str
    ) -> Show:
        """Cache show data and return Show object."""
        now = datetime.now(timezone.utc)

        cached_show = CachedShow(
            id=data["id"],
            title=data.get("name", "Unknown"),
            first_air_year=self._extract_year(data.get("first_air_date")),
            overview=data.get("overview"),
            rating=data.get("vote_average"),
            poster_path=data.get("poster_path"),
            cached_at=now,
        )

        with get_session() as session:
            # Upsert show
            existing = session.get(CachedShow, cached_show.id)
            if existing:
                existing.title = cached_show.title
                existing.first_air_year = cached_show.first_air_year
                existing.overview = cached_show.overview
                existing.rating = cached_show.rating
                existing.poster_path = cached_show.poster_path
                existing.cached_at = now
            else:
                session.add(cached_show)

            # Update streaming availability
            statement = select(StreamingAvailability).where(
                StreamingAvailability.content_type == "show",
                StreamingAvailability.content_id == data["id"],
                StreamingAvailability.region == region,
            )
            old_providers = session.exec(statement).all()
            for p in old_providers:
                session.delete(p)

            for provider in providers:
                session.add(
                    StreamingAvailability(
                        content_type="show",
                        content_id=data["id"],
                        provider_id=provider.provider_id,
                        provider_name=provider.provider_name,
                        region=region,
                        link=provider.link,
                        cached_at=now,
                    )
                )

            session.commit()

        return Show(
            id=data["id"],
            title=data.get("name", "Unknown"),
            first_air_year=self._extract_year(data.get("first_air_date")),
            overview=data.get("overview"),
            rating=data.get("vote_average"),
            poster_path=data.get("poster_path"),
            providers=providers,
        )
