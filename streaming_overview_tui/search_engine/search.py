from streaming_overview_tui.config_layer.config import StreamingService
from streaming_overview_tui.data_layer.repository import ContentRepository
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

    repository = ContentRepository()
    tmdb_results = await repository.search(query)

    # TODO: Process results
    return SearchResult(available=[], other=[], error=None)
