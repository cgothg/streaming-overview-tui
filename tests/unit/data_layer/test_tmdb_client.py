import pytest

from streaming_overview_tui.data_layer.tmdb_client import TMDBClient


class TestTMDBClient:
    def test_init(self):
        client = TMDBClient()
        assert client.base_url == "https://api.themoviedb.org/3"

    def test_get_headers_without_token(self, monkeypatch):
        # Ensure no token is set
        monkeypatch.setattr(
            "streaming_overview_tui.data_layer.tmdb_client.app_settings",
            type("Settings", (), {"tmdb_bearer_token": None, "tmdb_url": "https://api.themoviedb.org/3"})(),
        )
        client = TMDBClient()
        with pytest.raises(ValueError, match="TMDB_BEARER_TOKEN"):
            client._get_headers()

    def test_get_headers_with_token(self, monkeypatch):
        monkeypatch.setattr(
            "streaming_overview_tui.data_layer.tmdb_client.app_settings",
            type("Settings", (), {"tmdb_bearer_token": "test_token", "tmdb_url": "https://api.themoviedb.org/3"})(),
        )
        client = TMDBClient()
        headers = client._get_headers()
        assert headers["Authorization"] == "Bearer test_token"
        assert headers["Accept"] == "application/json"
