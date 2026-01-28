# TUI Layer Design

Design document for the streaming-overview-tui main screen implementation.

## Overview

A quick-lookup interface for searching movies and TV shows across streaming services. Users type a query, see results partitioned by availability on their subscribed services, and can open streaming links directly.

## Layout

Two-column layout with search input at top:

```
┌─────────────────────────────────────────────────────────────────┐
│  Streaming Overview                                             │
├─────────────────────────────────────────────────────────────────┤
│  Search: [_____________________]                                │
├────────────────────────────────────┬────────────────────────────┤
│  AVAILABLE ON YOUR SERVICES        │  The Batman (2022)         │
│  ─────────────────────────────     │  ────────────────────────  │
│  > The Batman (2022) - Netflix     │  Rating: 7.8/10            │
│    The Dark Knight (2008) - HBO    │                            │
│                                    │  A young Batman uncovers   │
│  OTHER RESULTS                     │  corruption in Gotham...   │
│  ─────────────────────────────     │                            │
│    Batman Begins (2005)            │  ────────────────────────  │
│    Batman v Superman (2016)        │  [Watch on Netflix]        │
│                                    │                            │
├────────────────────────────────────┴────────────────────────────┤
│  ↑↓ Navigate  Enter: Open  q: Quit                              │
└─────────────────────────────────────────────────────────────────┘
```

**Components:**

| Component | Width | Purpose |
|-----------|-------|---------|
| Search input | 100% | Text field with 300ms debounce |
| Results list | ~60% | Two sections: available + other |
| Detail panel | ~40% | Selected item info + watch buttons |

The detail panel appears when a result is selected. Hidden when search is empty or no results.

## Search Behavior

### Debouncing

- 300ms timer starts/resets on each keystroke
- Search fires when timer completes
- In-flight requests cancelled when new search starts

### State Transitions

| State | Display |
|-------|---------|
| Empty input | "Start typing to search..." |
| Typing (debounce pending) | Previous results or empty |
| Searching | "Searching..." indicator |
| Results found | Partitioned list, first item selected |
| No results | "No results found for '[query]'" |
| Error | Error message from SearchResult.error |

### Keyboard Navigation

| Key | Action |
|-----|--------|
| `↑` / `↓` | Move selection through results |
| `Enter` | Activate focused watch button |
| `Tab` | Move focus: search ↔ results ↔ detail panel |
| `Escape` | Clear search / focus search input |
| `q` | Quit application |

Section headers are visual separators, not selectable. Arrow keys move through all results seamlessly.

## Detail Panel

```
┌────────────────────────────┐
│  The Batman (2022)         │  ← Title + year
│  Movie                     │  ← Content type
│  ──────────────────────    │
│  Rating: 7.8/10            │  ← TMDB rating
│                            │
│  A reclusive young         │  ← Overview (truncated)
│  billionaire Bruce Wayne   │
│  investigates corruption   │
│  in Gotham City...         │
│                            │
│  ──────────────────────    │
│  [Watch on Netflix    ]    │  ← Watch buttons
│  [Watch on HBO Max    ]    │
└────────────────────────────┘
```

### Watch Buttons

- One button per subscribed service that has the content
- Items in "Other results" show no buttons
- `Enter` on button opens link via `webbrowser.open()`

### Edge Cases

| Condition | Behavior |
|-----------|----------|
| No rating | Hide rating line |
| No overview | Show "No description available" |
| Overview too long | Truncate with "..." |

## File Structure

```
tui_layer/
├── __init__.py
├── stream_app.py        # Main app routing (existing)
├── main_screen.py       # Search interface (rewrite)
├── setup_screen.py      # First-time setup (existing)
└── widgets/
    ├── __init__.py
    ├── search_input.py  # Debounced text input
    ├── results_list.py  # Two-section listview
    └── detail_panel.py  # Info + watch buttons
```

## Implementation Details

### Debouncing

Use Textual's `set_timer()` to delay search:

```python
def on_input_changed(self, event: Input.Changed) -> None:
    self._cancel_pending_search()
    self._search_timer = self.set_timer(0.3, self._do_search)
```

### Async Search

Run search in Textual worker to avoid blocking:

```python
@work(exclusive=True)
async def _do_search(self) -> None:
    result = await search(query, subscribed_services)
    self.call_from_thread(self._update_results, result)
```

### Browser Opening

```python
import webbrowser

def on_watch_button_pressed(self, url: str) -> None:
    webbrowser.open(url)
```

## Testing Strategy

Unit tests in `tests/unit/tui_layer/`:

**SearchInput:**
- Debounce timer resets on new input
- Emits search message after delay
- Cancels pending search on new input

**ResultsList:**
- Renders available section first
- Renders other section second
- Keyboard navigation crosses sections
- Selection emits message with item

**DetailPanel:**
- Displays title, year, type, rating, overview
- Truncates long overview
- Shows watch buttons for available services
- Hides buttons for unavailable content

Integration testing via manual testing - TUI automation is brittle.

## Future Enhancements

- Pixel-art poster display
- Browsing/discovery mode with more details
- Keyboard shortcut to refresh results
