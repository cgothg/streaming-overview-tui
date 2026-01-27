# Search Engine Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the search engine layer that searches TMDB, fetches streaming availability, and partitions results by user subscriptions.

**Architecture:** The search engine exposes an async `search()` function that queries TMDB, enriches results with streaming availability via `ContentRepository`, and partitions into "available" (on user's services) and "other" lists.

**Tech Stack:** Python async/await, existing `ContentRepository` and `TMDBClient`, dataclasses for models.

---

## Task 1: Create Search Engine Models

**Files:**
- Create: `streaming_overview_tui/search_engine/models.py`
- Create: `tests/unit/search_engine/__init__.py`
- Create: `tests/unit/search_engine/test_models.py`

**Step 1: Create test directory**

```bash
mkdir -p tests/unit/search_engine
touch tests/unit/search_engine/__init__.py
```

**Step 2: Write the failing test for ContentItem**

Create `tests/unit/search_engine/test_models.py`:

```python
from streaming_overview_tui.config_layer.config import StreamingService
from streaming_overview_tui.search_engine.models import ContentItem


class TestContentItem:
    def test_create_content_item(self):
        item = ContentItem(
            tmdb_id=123,
            title="The Batman",
            year=2022,
            content_type="movie",
            poster_url="https://image.tmdb.org/t/p/w500/test.jpg",
            services=[StreamingService.HBO_MAX],
        )
        assert item.tmdb_id == 123
        assert item.title == "The Batman"
        assert item.year == 2022
        assert item.content_type == "movie"
        assert item.poster_url == "https://image.tmdb.org/t/p/w500/test.jpg"
        assert item.services == [StreamingService.HBO_MAX]

    def test_create_content_item_minimal(self):
        item = ContentItem(
            tmdb_id=456,
            title="Unknown Show",
            year=None,
            content_type="tv",
            poster_url=None,
            services=[],
        )
        assert item.tmdb_id == 456
        assert item.year is None
        assert item.poster_url is None
        assert item.services == []
```

**Step 3: Run test to verify it fails**

Run: `uv run pytest tests/unit/search_engine/test_models.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'streaming_overview_tui.search_engine'"

**Step 4: Create the search_engine package**

Create `streaming_overview_tui/search_engine/__init__.py`:

```python
```

(Empty file to make it a package)

**Step 5: Write ContentItem model**

Create `streaming_overview_tui/search_engine/models.py`:

```python
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
```

**Step 6: Run test to verify ContentItem passes**

Run: `uv run pytest tests/unit/search_engine/test_models.py::TestContentItem -v`
Expected: PASS

**Step 7: Write failing test for SearchResult**

Add to `tests/unit/search_engine/test_models.py`:

```python
from streaming_overview_tui.search_engine.models import SearchResult


class TestSearchResult:
    def test_create_search_result(self):
        available_item = ContentItem(
            tmdb_id=123,
            title="Available Movie",
            year=2022,
            content_type="movie",
            poster_url=None,
            services=[StreamingService.NETFLIX],
        )
        other_item = ContentItem(
            tmdb_id=456,
            title="Other Movie",
            year=2021,
            content_type="movie",
            poster_url=None,
            services=[],
        )
        result = SearchResult(
            available=[available_item],
            other=[other_item],
            error=None,
        )
        assert len(result.available) == 1
        assert len(result.other) == 1
        assert result.error is None

    def test_create_search_result_with_error(self):
        result = SearchResult(
            available=[],
            other=[],
            error="TMDB API unavailable - please try again later",
        )
        assert result.available == []
        assert result.other == []
        assert result.error == "TMDB API unavailable - please try again later"
```

**Step 8: Run test to verify it fails**

Run: `uv run pytest tests/unit/search_engine/test_models.py::TestSearchResult -v`
Expected: FAIL with "cannot import name 'SearchResult'"

**Step 9: Write SearchResult model**

Add to `streaming_overview_tui/search_engine/models.py`:

```python
@dataclass
class SearchResult:
    """Search results partitioned by availability."""

    available: list[ContentItem]
    other: list[ContentItem]
    error: str | None
```

**Step 10: Run all model tests**

Run: `uv run pytest tests/unit/search_engine/test_models.py -v`
Expected: PASS (all 4 tests)

**Step 11: Commit**

```bash
git add streaming_overview_tui/search_engine/ tests/unit/search_engine/
git commit -m "feat(search-engine): add ContentItem and SearchResult models"
```

---

## Task 2: Implement Provider Name Mapping

**Files:**
- Modify: `streaming_overview_tui/search_engine/models.py`
- Modify: `tests/unit/search_engine/test_models.py`

The TMDB API returns provider names like "Netflix", "Max", "Amazon Prime Video", "Disney Plus". We need to map these to our `StreamingService` enum.

**Step 1: Write failing test for provider mapping**

Add to `tests/unit/search_engine/test_models.py`:

```python
from streaming_overview_tui.search_engine.models import map_provider_to_service


class TestProviderMapping:
    def test_map_netflix(self):
        assert map_provider_to_service("Netflix") == StreamingService.NETFLIX

    def test_map_hbo_max(self):
        # TMDB uses "Max" for HBO Max
        assert map_provider_to_service("Max") == StreamingService.HBO_MAX
        assert map_provider_to_service("HBO Max") == StreamingService.HBO_MAX

    def test_map_amazon_prime(self):
        assert map_provider_to_service("Amazon Prime Video") == StreamingService.AMAZON_PRIME

    def test_map_disney_plus(self):
        assert map_provider_to_service("Disney Plus") == StreamingService.DISNEY_PLUS

    def test_map_unknown_returns_none(self):
        assert map_provider_to_service("Apple TV+") is None
        assert map_provider_to_service("Hulu") is None
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/search_engine/test_models.py::TestProviderMapping -v`
Expected: FAIL with "cannot import name 'map_provider_to_service'"

**Step 3: Implement provider mapping**

Add to `streaming_overview_tui/search_engine/models.py`:

```python
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
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/search_engine/test_models.py::TestProviderMapping -v`
Expected: PASS (all 5 tests)

**Step 5: Commit**

```bash
git add streaming_overview_tui/search_engine/models.py tests/unit/search_engine/test_models.py
git commit -m "feat(search-engine): add TMDB provider name mapping"
```

---

## Task 3: Implement Search Function - Query Validation

**Files:**
- Create: `streaming_overview_tui/search_engine/search.py`
- Create: `tests/unit/search_engine/test_search.py`

**Step 1: Write failing test for short query validation**

Create `tests/unit/search_engine/test_search.py`:

```python
import pytest

from streaming_overview_tui.config_layer.config import StreamingService
from streaming_overview_tui.search_engine.search import search


class TestSearchValidation:
    @pytest.mark.asyncio
    async def test_short_query_returns_empty_results(self):
        result = await search(
            query="a",
            subscribed_services=[StreamingService.NETFLIX],
            region="DK",
        )
        assert result.available == []
        assert result.other == []
        assert result.error is None

    @pytest.mark.asyncio
    async def test_empty_query_returns_empty_results(self):
        result = await search(
            query="",
            subscribed_services=[StreamingService.NETFLIX],
            region="DK",
        )
        assert result.available == []
        assert result.other == []
        assert result.error is None
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/search_engine/test_search.py::TestSearchValidation -v`
Expected: FAIL with "cannot import name 'search'"

**Step 3: Implement search function stub**

Create `streaming_overview_tui/search_engine/search.py`:

```python
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
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/search_engine/test_search.py::TestSearchValidation -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add streaming_overview_tui/search_engine/search.py tests/unit/search_engine/test_search.py
git commit -m "feat(search-engine): add search function with query validation"
```

---

## Task 4: Implement Search Function - TMDB Integration

**Files:**
- Modify: `streaming_overview_tui/search_engine/search.py`
- Modify: `tests/unit/search_engine/test_search.py`

**Step 1: Write failing test for TMDB search integration**

Add to `tests/unit/search_engine/test_search.py`:

```python
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch


class TestSearchTMDBIntegration:
    @pytest.fixture
    def mock_repository(self):
        with patch(
            "streaming_overview_tui.search_engine.search.ContentRepository"
        ) as mock:
            repo_instance = MagicMock()
            mock.return_value = repo_instance
            yield repo_instance

    @pytest.mark.asyncio
    async def test_search_calls_repository(self, mock_repository):
        mock_repository.search = AsyncMock(return_value=[])

        await search(
            query="batman",
            subscribed_services=[StreamingService.NETFLIX],
            region="DK",
        )

        mock_repository.search.assert_called_once_with("batman")

    @pytest.mark.asyncio
    async def test_short_query_does_not_call_repository(self, mock_repository):
        mock_repository.search = AsyncMock(return_value=[])

        await search(
            query="b",
            subscribed_services=[StreamingService.NETFLIX],
            region="DK",
        )

        mock_repository.search.assert_not_called()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/search_engine/test_search.py::TestSearchTMDBIntegration -v`
Expected: FAIL with assertion error (search not called)

**Step 3: Update search function to call repository**

Update `streaming_overview_tui/search_engine/search.py`:

```python
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
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/search_engine/test_search.py::TestSearchTMDBIntegration -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add streaming_overview_tui/search_engine/search.py tests/unit/search_engine/test_search.py
git commit -m "feat(search-engine): integrate TMDB search via repository"
```

---

## Task 5: Implement Result Partitioning

**Files:**
- Modify: `streaming_overview_tui/search_engine/search.py`
- Modify: `tests/unit/search_engine/test_search.py`

**Step 1: Write failing test for result partitioning**

Add to `tests/unit/search_engine/test_search.py`:

```python
from streaming_overview_tui.data_layer.models import SearchResult as TMDBSearchResult
from streaming_overview_tui.data_layer.models import Movie
from streaming_overview_tui.data_layer.models import StreamingProvider


class TestSearchPartitioning:
    @pytest.fixture
    def mock_repository(self):
        with patch(
            "streaming_overview_tui.search_engine.search.ContentRepository"
        ) as mock:
            repo_instance = MagicMock()
            mock.return_value = repo_instance
            yield repo_instance

    @pytest.mark.asyncio
    async def test_partitions_by_subscription(self, mock_repository):
        # TMDB search returns two movies
        mock_repository.search = AsyncMock(
            return_value=[
                TMDBSearchResult(
                    id=123,
                    title="Movie on Netflix",
                    year=2022,
                    content_type="movie",
                    poster_path="/netflix.jpg",
                    rating=8.0,
                ),
                TMDBSearchResult(
                    id=456,
                    title="Movie on Disney",
                    year=2021,
                    content_type="movie",
                    poster_path="/disney.jpg",
                    rating=7.5,
                ),
            ]
        )

        # Movie details with providers
        mock_repository.get_movie = AsyncMock(
            side_effect=[
                Movie(
                    id=123,
                    title="Movie on Netflix",
                    release_year=2022,
                    overview="...",
                    rating=8.0,
                    poster_path="/netflix.jpg",
                    providers=[
                        StreamingProvider(
                            provider_id=8, provider_name="Netflix", link="..."
                        )
                    ],
                ),
                Movie(
                    id=456,
                    title="Movie on Disney",
                    release_year=2021,
                    overview="...",
                    rating=7.5,
                    poster_path="/disney.jpg",
                    providers=[
                        StreamingProvider(
                            provider_id=337, provider_name="Disney Plus", link="..."
                        )
                    ],
                ),
            ]
        )

        result = await search(
            query="movie",
            subscribed_services=[StreamingService.NETFLIX],  # Only subscribed to Netflix
            region="DK",
        )

        # Movie on Netflix should be in "available"
        assert len(result.available) == 1
        assert result.available[0].title == "Movie on Netflix"
        assert result.available[0].services == [StreamingService.NETFLIX]

        # Movie on Disney should be in "other"
        assert len(result.other) == 1
        assert result.other[0].title == "Movie on Disney"
        assert result.other[0].services == []  # No subscribed services

    @pytest.mark.asyncio
    async def test_no_providers_goes_to_other(self, mock_repository):
        mock_repository.search = AsyncMock(
            return_value=[
                TMDBSearchResult(
                    id=789,
                    title="Movie No Streaming",
                    year=2020,
                    content_type="movie",
                    poster_path=None,
                    rating=6.0,
                ),
            ]
        )

        mock_repository.get_movie = AsyncMock(
            return_value=Movie(
                id=789,
                title="Movie No Streaming",
                release_year=2020,
                overview="...",
                rating=6.0,
                poster_path=None,
                providers=[],  # No streaming providers
            )
        )

        result = await search(
            query="movie",
            subscribed_services=[StreamingService.NETFLIX],
            region="DK",
        )

        assert len(result.available) == 0
        assert len(result.other) == 1
        assert result.other[0].title == "Movie No Streaming"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/search_engine/test_search.py::TestSearchPartitioning -v`
Expected: FAIL with assertion error (empty results)

**Step 3: Implement result partitioning**

Update `streaming_overview_tui/search_engine/search.py`:

```python
from streaming_overview_tui.config_layer.config import StreamingService
from streaming_overview_tui.data_layer.repository import ContentRepository
from streaming_overview_tui.search_engine.models import ContentItem
from streaming_overview_tui.search_engine.models import SearchResult
from streaming_overview_tui.search_engine.models import map_provider_to_service

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
    region: str,
) -> SearchResult:
    """Search for movies and TV shows, partitioned by streaming availability."""
    if len(query) < MIN_QUERY_LENGTH:
        return SearchResult(available=[], other=[], error=None)

    repository = ContentRepository()
    tmdb_results = await repository.search(query)

    available: list[ContentItem] = []
    other: list[ContentItem] = []

    for tmdb_item in tmdb_results:
        # Fetch full details with streaming providers
        if tmdb_item.content_type == "movie":
            details = await repository.get_movie(tmdb_item.id)
            content_type = "movie"
        else:
            details = await repository.get_show(tmdb_item.id)
            content_type = "tv"

        if details is None:
            continue

        # Map providers to subscribed services
        matched_services: list[StreamingService] = []
        for provider in details.providers:
            service = map_provider_to_service(provider.provider_name)
            if service and service in subscribed_services:
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
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/search_engine/test_search.py::TestSearchPartitioning -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add streaming_overview_tui/search_engine/search.py tests/unit/search_engine/test_search.py
git commit -m "feat(search-engine): implement result partitioning by subscriptions"
```

---

## Task 6: Implement Error Handling

**Files:**
- Modify: `streaming_overview_tui/search_engine/search.py`
- Modify: `tests/unit/search_engine/test_search.py`

**Step 1: Write failing test for error handling**

Add to `tests/unit/search_engine/test_search.py`:

```python
import httpx


class TestSearchErrorHandling:
    @pytest.fixture
    def mock_repository(self):
        with patch(
            "streaming_overview_tui.search_engine.search.ContentRepository"
        ) as mock:
            repo_instance = MagicMock()
            mock.return_value = repo_instance
            yield repo_instance

    @pytest.mark.asyncio
    async def test_timeout_error_returns_descriptive_message(self, mock_repository):
        mock_repository.search = AsyncMock(
            side_effect=httpx.TimeoutException("Connection timeout")
        )

        result = await search(
            query="batman",
            subscribed_services=[StreamingService.NETFLIX],
            region="DK",
        )

        assert result.available == []
        assert result.other == []
        assert "TMDB API" in result.error
        assert "timeout" in result.error.lower()

    @pytest.mark.asyncio
    async def test_http_error_returns_descriptive_message(self, mock_repository):
        mock_repository.search = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Rate limited",
                request=MagicMock(),
                response=MagicMock(status_code=429),
            )
        )

        result = await search(
            query="batman",
            subscribed_services=[StreamingService.NETFLIX],
            region="DK",
        )

        assert result.available == []
        assert result.other == []
        assert "TMDB API" in result.error

    @pytest.mark.asyncio
    async def test_generic_error_returns_descriptive_message(self, mock_repository):
        mock_repository.search = AsyncMock(
            side_effect=Exception("Unknown error")
        )

        result = await search(
            query="batman",
            subscribed_services=[StreamingService.NETFLIX],
            region="DK",
        )

        assert result.available == []
        assert result.other == []
        assert "TMDB API" in result.error
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/search_engine/test_search.py::TestSearchErrorHandling -v`
Expected: FAIL (exception not caught, or error message not set)

**Step 3: Implement error handling**

Update `streaming_overview_tui/search_engine/search.py`:

```python
import httpx

from streaming_overview_tui.config_layer.config import StreamingService
from streaming_overview_tui.data_layer.repository import ContentRepository
from streaming_overview_tui.search_engine.models import ContentItem
from streaming_overview_tui.search_engine.models import SearchResult
from streaming_overview_tui.search_engine.models import map_provider_to_service

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
    region: str,
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
            # Skip items that fail to fetch details
            continue

        if details is None:
            continue

        # Map providers to subscribed services
        matched_services: list[StreamingService] = []
        for provider in details.providers:
            service = map_provider_to_service(provider.provider_name)
            if service and service in subscribed_services:
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
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/search_engine/test_search.py::TestSearchErrorHandling -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add streaming_overview_tui/search_engine/search.py tests/unit/search_engine/test_search.py
git commit -m "feat(search-engine): add TMDB error handling with descriptive messages"
```

---

## Task 7: Export Public Interface

**Files:**
- Modify: `streaming_overview_tui/search_engine/__init__.py`

**Step 1: Write failing test for public imports**

Add to `tests/unit/search_engine/test_models.py`:

```python
class TestPublicInterface:
    def test_can_import_from_package(self):
        from streaming_overview_tui.search_engine import ContentItem
        from streaming_overview_tui.search_engine import SearchResult
        from streaming_overview_tui.search_engine import search

        assert ContentItem is not None
        assert SearchResult is not None
        assert search is not None
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/search_engine/test_models.py::TestPublicInterface -v`
Expected: FAIL with "cannot import name 'ContentItem' from 'streaming_overview_tui.search_engine'"

**Step 3: Export public interface**

Update `streaming_overview_tui/search_engine/__init__.py`:

```python
from streaming_overview_tui.search_engine.models import ContentItem
from streaming_overview_tui.search_engine.models import SearchResult
from streaming_overview_tui.search_engine.search import search

__all__ = ["ContentItem", "SearchResult", "search"]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/search_engine/test_models.py::TestPublicInterface -v`
Expected: PASS

**Step 5: Run all tests**

Run: `uv run pytest -v`
Expected: All tests pass

**Step 6: Commit**

```bash
git add streaming_overview_tui/search_engine/__init__.py tests/unit/search_engine/test_models.py
git commit -m "feat(search-engine): export public interface"
```

---

## Task 8: Final Verification and Cleanup

**Step 1: Run all tests**

Run: `uv run pytest -v`
Expected: All tests pass (26 existing + ~15 new = ~41 total)

**Step 2: Run linter**

Run: `pre-commit run --all-files`
Expected: All checks pass

**Step 3: Fix any linting issues if needed**

If ruff or other linters report issues, fix them and re-run.

**Step 4: Final commit if any fixes were needed**

```bash
git add -A
git commit -m "chore: fix linting issues"
```

**Step 5: Verify branch is ready**

Run: `git log --oneline main..HEAD`
Expected: See all commits for this feature

---

## Summary

After completing all tasks, the search engine will:
- Accept a query, subscribed services, and region
- Return empty results for queries under 2 characters (no API call)
- Search TMDB via the existing ContentRepository
- Fetch streaming availability for each result
- Partition results into "available" (on user's services) and "other"
- Handle TMDB errors gracefully with descriptive messages
- Export a clean public interface: `search()`, `ContentItem`, `SearchResult`
