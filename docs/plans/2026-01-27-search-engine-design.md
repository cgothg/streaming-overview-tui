# Search Engine Design

Design document for the streaming-overview-tui search engine layer.

## Overview

The search engine provides fuzzy search for movies and TV shows, with results filtered and prioritized by the user's streaming service subscriptions.

## Interface

```python
async def search(
    query: str,
    subscribed_services: list[StreamingService],
) -> SearchResult
```

Region is determined internally from user config via `load_user_config()`.

### SearchResult

```python
@dataclass
class SearchResult:
    available: list[ContentItem]  # On user's subscribed services
    other: list[ContentItem]      # On other services or unavailable
    error: str | None             # TMDB-specific error message
```

### ContentItem

```python
@dataclass
class ContentItem:
    tmdb_id: int
    title: str
    year: int | None
    content_type: Literal["movie", "tv"]
    poster_url: str | None
    services: list[StreamingService]  # User's subscribed services only
```

## Behavior

### Search Flow

1. **Validate query** - If less than 2 characters, return empty results (no API call)
2. **Search TMDB** - Call multi-search endpoint for movies and TV shows
3. **Fetch availability** - Use `ContentRepository` for streaming availability (handles caching)
4. **Partition results** - Split into `available` and `other` lists
5. **Enrich with services** - Populate `services` field with user's subscribed services only
6. **Return** - Both lists maintain TMDB relevance ordering

### Result Partitioning

- `available`: Content on at least one of user's subscribed services
- `other`: Content not on user's services, or no streaming availability

### Error Handling

Return empty lists with descriptive `error` message:
- "TMDB API request failed: connection timeout"
- "TMDB API returned error: rate limit exceeded"
- "TMDB API unavailable - please try again later"

## Debouncing Boundary

The search engine is a simple async function. Debouncing is handled by the TUI layer.

```
┌─────────────────────────────────────────────────────┐
│  TUI Layer                                          │
│  ┌─────────────┐    ┌─────────────┐                │
│  │ Text Input  │───▶│  Debouncer  │────┐           │
│  └─────────────┘    └─────────────┘    │           │
│                         300ms          ▼           │
│                              ┌──────────────────┐  │
│                              │ search() call    │  │
│                              └────────┬─────────┘  │
└───────────────────────────────────────┼────────────┘
                                        ▼
┌───────────────────────────────────────────────────┐
│  Search Engine                                     │
│  search(query, services, region) → SearchResult   │
└───────────────────────────────────────────────────┘
```

TUI layer responsibilities:
- Start 300ms timer on each keystroke
- Reset timer if user keeps typing
- Cancel in-flight requests when new search starts
- Call `search()` only when timer fires

This separation keeps the search engine testable without simulating timing.

## File Structure

```
search_engine/
├── __init__.py          # Exports search() function
├── models.py            # ContentItem, SearchResult dataclasses
└── search.py            # Main search() implementation
```

## Design Decisions

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| Data source | TMDB API directly | Fresh results, comprehensive catalog |
| Content types | Combined movies + TV | Simpler UX, one search covers both |
| Result display | Available first, others below | Users see actionable content first |
| Service display | All subscribed services | User can choose preferred service |
| Ranking | TMDB relevance | Simple, already good quality |
| Min query length | 2 characters | Avoid overly broad searches |
| Debounce delay | 300ms | Balance responsiveness and API load |

## Testing Strategy

Tests in `tests/unit/search_engine/`:

**Input validation:**
- Query under 2 characters returns empty results, no API call

**Partitioning logic:**
- Results on subscribed services go to `available`
- Results not on subscribed services go to `other`
- Results with no streaming availability go to `other`

**Service filtering:**
- `services` field only includes user's subscribed services

**Error handling:**
- TMDB timeout returns empty results with descriptive error
- TMDB rate limit returns empty results with descriptive error

**Integration points:**
- Mock `ContentRepository` to test search logic in isolation
- Mock TMDB client responses

## Future Considerations

- API health indicator in TUI (connection status)
- Popularity/recency ranking options
- Local cache fallback for offline search
