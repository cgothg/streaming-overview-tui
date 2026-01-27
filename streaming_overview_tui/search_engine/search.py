from streaming_overview_tui.config_layer.config import StreamingService
from streaming_overview_tui.search_engine.models import SearchResult

MIN_QUERY_LENGTH = 2


async def search(
    query: str,
    subscribed_services: list[StreamingService],
    region: str,
) -> SearchResult:
    """Search for movies and TV shows, partitioned by streaming availability."""
    if len(query) < MIN_QUERY_LENGTH:
        return SearchResult(available=[], other=[], error=None)

    # TODO: Implement full search
    return SearchResult(available=[], other=[], error=None)
