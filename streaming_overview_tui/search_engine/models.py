from dataclasses import dataclass
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


@dataclass
class SearchResult:
    """Search results partitioned by availability."""

    available: list[ContentItem]
    other: list[ContentItem]
    error: str | None
