from dataclasses import dataclass
from dataclasses import field
from typing import Literal

from streaming_overview_tui.config_layer.config import StreamingService


@dataclass
class ContentItem:
    """A single search result item."""

    tmdb_id: int
    title: str
    year: int | None
    content_type: Literal["movie", "tv"]
    poster_url: str | None
    services: list[StreamingService]
    overview: str | None = None
    rating: float | None = None
    watch_urls: dict[StreamingService, str] = field(default_factory=dict)


@dataclass
class SearchResult:
    """Search results partitioned by availability."""

    available: list[ContentItem]
    other: list[ContentItem]
    error: str | None


# Mapping from TMDB provider names to StreamingService enum
PROVIDER_NAME_MAP: dict[str, StreamingService] = {
    "Netflix": StreamingService.NETFLIX,
    "Max": StreamingService.HBO_MAX,
    "HBO Max": StreamingService.HBO_MAX,
    "Amazon Prime Video": StreamingService.AMAZON_PRIME,
    "Disney Plus": StreamingService.DISNEY_PLUS,
}


def map_provider_to_service(provider_name: str) -> StreamingService | None:
    """Map TMDB provider name to StreamingService enum."""
    return PROVIDER_NAME_MAP.get(provider_name)
