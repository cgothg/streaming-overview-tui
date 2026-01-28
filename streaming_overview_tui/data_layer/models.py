from datetime import datetime
from datetime import timezone

from sqlmodel import Field
from sqlmodel import SQLModel


class CachedMovie(SQLModel, table=True):
    """Cached movie data from TMDB."""

    __tablename__ = "cached_movies"

    id: int = Field(primary_key=True)  # TMDB movie ID
    title: str
    release_year: int | None = None
    overview: str | None = None
    rating: float | None = None  # TMDB vote average
    poster_path: str | None = None  # Relative path for TMDB image CDN
    cached_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CachedShow(SQLModel, table=True):
    """Cached TV show data from TMDB."""

    __tablename__ = "cached_shows"

    id: int = Field(primary_key=True)  # TMDB show ID
    title: str
    first_air_year: int | None = None
    overview: str | None = None
    rating: float | None = None
    poster_path: str | None = None
    cached_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StreamingAvailability(SQLModel, table=True):
    """Streaming availability for content in a specific region."""

    __tablename__ = "streaming_availability"

    id: int | None = Field(default=None, primary_key=True)
    content_type: str  # "movie" or "show"
    content_id: int  # References CachedMovie.id or CachedShow.id
    provider_id: int  # TMDB provider ID
    provider_name: str  # e.g., "Netflix"
    region: str  # e.g., "DK"
    link: str  # Direct watch link from TMDB
    cached_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Lightweight types for search results and API responses


class TMDBSearchResult:
    """Lightweight search result from TMDB API."""

    def __init__(
        self,
        id: int,
        title: str,
        year: int | None,
        content_type: str,
        poster_path: str | None,
        rating: float | None,
    ):
        self.id = id
        self.title = title
        self.year = year
        self.content_type = content_type
        self.poster_path = poster_path
        self.rating = rating


class StreamingProvider:
    """Streaming provider info."""

    def __init__(
        self,
        provider_id: int,
        provider_name: str,
        link: str,
    ):
        self.provider_id = provider_id
        self.provider_name = provider_name
        self.link = link


class Movie:
    """Full movie details with streaming availability."""

    def __init__(
        self,
        id: int,
        title: str,
        release_year: int | None,
        overview: str | None,
        rating: float | None,
        poster_path: str | None,
        providers: list[StreamingProvider],
    ):
        self.id = id
        self.title = title
        self.release_year = release_year
        self.overview = overview
        self.rating = rating
        self.poster_path = poster_path
        self.providers = providers


class Show:
    """Full TV show details with streaming availability."""

    def __init__(
        self,
        id: int,
        title: str,
        first_air_year: int | None,
        overview: str | None,
        rating: float | None,
        poster_path: str | None,
        providers: list[StreamingProvider],
    ):
        self.id = id
        self.title = title
        self.first_air_year = first_air_year
        self.overview = overview
        self.rating = rating
        self.poster_path = poster_path
        self.providers = providers
