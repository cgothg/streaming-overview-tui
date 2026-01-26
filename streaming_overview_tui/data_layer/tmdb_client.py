import httpx

from streaming_overview_tui.config_layer import app_settings


class TMDBClient:
    """HTTP client for TMDB API."""

    def __init__(self):
        self.base_url = app_settings.tmdb_url
        self.token = app_settings.tmdb_bearer_token

    def _get_headers(self) -> dict[str, str]:
        """Get authorization headers."""
        if not self.token:
            raise ValueError("TMDB_BEARER_TOKEN environment variable not set")
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
        }

    async def search_multi(self, query: str) -> dict:
        """Search for movies and TV shows.

        Args:
            query: Search query string

        Returns:
            TMDB API response with results
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/search/multi",
                headers=self._get_headers(),
                params={"query": query},
            )
            response.raise_for_status()
            return response.json()

    async def get_movie(self, movie_id: int) -> dict:
        """Get movie details with watch providers.

        Args:
            movie_id: TMDB movie ID

        Returns:
            TMDB API response with movie details and watch providers
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/movie/{movie_id}",
                headers=self._get_headers(),
                params={"append_to_response": "watch/providers"},
            )
            response.raise_for_status()
            return response.json()

    async def get_show(self, show_id: int) -> dict:
        """Get TV show details with watch providers.

        Args:
            show_id: TMDB show ID

        Returns:
            TMDB API response with show details and watch providers
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/tv/{show_id}",
                headers=self._get_headers(),
                params={"append_to_response": "watch/providers"},
            )
            response.raise_for_status()
            return response.json()
