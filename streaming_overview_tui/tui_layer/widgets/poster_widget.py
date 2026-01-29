from rich.text import Text
from textual.reactive import reactive
from textual.widget import Widget

# Poster dimensions in characters
POSTER_WIDTH = 12
POSTER_HEIGHT = 18


PLACEHOLDER = """\
┌──────────┐
│   ___    │
│  |   |   │
│  | > |   │
│  |___|   │
│          │
│    No    │
│  Poster  │
│          │
│          │
│          │
│          │
│          │
│          │
│          │
│          │
│          │
└──────────┘\
"""


class PosterWidget(Widget):
    """Displays a movie/TV poster as pixel art or placeholder."""

    DEFAULT_CSS = """
    PosterWidget {
        width: 12;
        height: 18;
    }
    """

    poster_url: reactive[str | None] = reactive(None)
    tmdb_id: reactive[int | None] = reactive(None)

    def __init__(
        self,
        poster_url: str | None = None,
        tmdb_id: int | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.poster_url = poster_url
        self.tmdb_id = tmdb_id
        self._rendered_art: Text | None = None

    def render(self) -> Text:
        """Render the poster or placeholder."""
        if self._rendered_art is not None:
            return self._rendered_art
        return Text(PLACEHOLDER, style="dim")

    def render_str(self) -> str:
        """Return string representation for testing."""
        return str(self.render())
