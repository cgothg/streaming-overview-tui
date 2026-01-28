import json
from enum import Enum
from pathlib import Path

from platformdirs import user_config_dir
from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

APP_NAME = "streaming-overview-tui"
CONFIG_DIR = Path(user_config_dir(APP_NAME))
CONFIG_FILE = CONFIG_DIR / "stream_config.json"


class StreamingService(str, Enum):
    """Available streaming services."""

    NETFLIX = "Netflix"
    HBO_MAX = "HBO-MAX"
    AMAZON_PRIME = "AmazonPrime"
    DISNEY_PLUS = "Disney+"


class UserConfig:
    """User configuration stored in JSON file."""

    def __init__(
        self,
        region: str = "DK",
        subscriptions: list[str] | None = None,
    ):
        self.region = region
        self.subscriptions = subscriptions or []

    def to_dict(self) -> dict:
        return {
            "region": self.region,
            "subscriptions": self.subscriptions,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserConfig":
        return cls(
            region=data.get("region", "DK"),
            subscriptions=data.get("subscriptions", []),
        )


class AppSettings(BaseSettings):
    """Application settings from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    tmdb_bearer_token: str | None = Field(default=None)
    tmdb_url: str = Field(default="https://api.themoviedb.org/3")


def config_exists() -> bool:
    """Check if user config file exists."""
    return CONFIG_FILE.exists()


def load_user_config() -> UserConfig:
    """Load user config from file. Returns default config if file doesn't exist."""
    if not config_exists():
        return UserConfig()

    with open(CONFIG_FILE) as f:
        data = json.load(f)
    return UserConfig.from_dict(data)


def save_user_config(user_config: UserConfig) -> None:
    """Save user config to file. Creates config directory if needed."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(user_config.to_dict(), f, indent=2)


def get_available_services() -> list[str]:
    """Get list of available streaming service names."""
    return [service.value for service in StreamingService]


# Global instance
app_settings = AppSettings()
