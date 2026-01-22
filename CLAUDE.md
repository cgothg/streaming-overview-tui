# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A TUI application for searching movies and TV shows across streaming services, providing direct links to watch content based on user subscriptions. Uses TMDB API for content data.

## Commands

```bash
# Run the application
uv run streaming-tui

# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/unit/config_layer/test_config.py

# Run tests with verbose output
uv run pytest -v

# Lint and format (via pre-commit)
pre-commit run --all-files

# Install pre-commit hooks
pre-commit install
```

## Architecture

Four-layer architecture with clear separation of concerns:

1. **TUI Layer** (`tui_layer/`) - Textual-based interface with screens for main search and setup wizard
2. **Search Engine** (`search_engine/`) - Fuzzy search with filtering by streaming service subscriptions
3. **Data Layer** (`data_layer/`) - TMDB API client with local SQLite caching
4. **Config Layer** (`config_layer/`) - User preferences stored in OS config directory via platformdirs, environment variables for API credentials

## Configuration

- `TMDB_BEARER_TOKEN` - Required environment variable for TMDB API access (can be set in `.env` file)
- User config (region, subscriptions) stored in `~/.config/streaming-overview-tui/stream_config.json` (Linux) or equivalent OS config directory
- Available streaming services defined in `StreamingService` enum: Netflix, HBO-MAX, AmazonPrime, Disney+

## Key Dependencies

- **textual** - TUI framework
- **httpx** - Async HTTP client for API calls
- **sqlmodel** - SQLite ORM for caching
- **thefuzz/python-levenshtein** - Fuzzy string matching
- **pydantic-settings** - Settings management
- **platformdirs** - OS-specific config directory paths
