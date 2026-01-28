import httpx

from streaming_overview_tui.config_layer.config import StreamingService
from streaming_overview_tui.data_layer.repository import ContentRepository
from streaming_overview_tui.search_engine.models import ContentItem
from streaming_overview_tui.search_engine.models import map_provider_to_service
from streaming_overview_tui.search_engine.models import SearchResult

MIN_QUERY_LENGTH = 2
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"


def _build_poster_url(poster_path: str | None) -> str | None:
    """Build full poster URL from TMDB poster path."""
    if not poster_path:
        return None
    return f"{TMDB_IMAGE_BASE_URL}{poster_path}"


async def search(
    query: str,
    subscribed_services: list[StreamingService],
) -> SearchResult:
    """Search for movies and TV shows, partitioned by streaming availability."""
    if len(query) < MIN_QUERY_LENGTH:
        return SearchResult(available=[], other=[], error=None)

    repository = ContentRepository()

    try:
        tmdb_results = await repository.search(query)
    except httpx.TimeoutException:
        return SearchResult(
            available=[],
            other=[],
            error="TMDB API request failed: connection timeout",
        )
    except httpx.HTTPStatusError as e:
        return SearchResult(
            available=[],
            other=[],
            error=f"TMDB API returned error: HTTP {e.response.status_code}",
        )
    except Exception:
        return SearchResult(
            available=[],
            other=[],
            error="TMDB API unavailable - please try again later",
        )

    available: list[ContentItem] = []
    other: list[ContentItem] = []

    for tmdb_item in tmdb_results:
        # Fetch full details with streaming providers
        try:
            if tmdb_item.content_type == "movie":
                details = await repository.get_movie(tmdb_item.id)
                content_type = "movie"
            else:
                details = await repository.get_show(tmdb_item.id)
                content_type = "tv"
        except Exception:
            continue  # Skip items that fail to fetch

        if details is None:
            continue

        # Map providers to subscribed services
        matched_services: list[StreamingService] = []
        for provider in details.providers:
            service = map_provider_to_service(provider.provider_name)
            if (
                service
                and service in subscribed_services
                and service not in matched_services
            ):
                matched_services.append(service)

        # Build ContentItem
        item = ContentItem(
            tmdb_id=tmdb_item.id,
            title=tmdb_item.title,
            year=tmdb_item.year,
            content_type=content_type,
            poster_url=_build_poster_url(tmdb_item.poster_path),
            services=matched_services,
        )

        # Partition by availability
        if matched_services:
            available.append(item)
        else:
            other.append(item)

    return SearchResult(available=available, other=other, error=None)
