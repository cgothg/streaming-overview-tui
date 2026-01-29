# Pixel-Art Poster Display Design

Design document for adding pixel-art movie/TV posters to the detail panel.

## Overview

Display movie and TV show posters as pixel-art in the detail panel using Unicode half-block characters. Posters appear on the left with info text on the right.

## Layout

Horizontal layout with fixed-width poster area:

```
┌─────────────────────────────────────┐
│ ┌──────────┐  The Batman (2022)     │
│ │          │  Movie                 │
│ │  POSTER  │  ───────────────────   │
│ │  12×18   │  Rating: 7.8/10        │
│ │  chars   │                        │
│ │          │  A reclusive young     │
│ │          │  billionaire Bruce...  │
│ │          │                        │
│ └──────────┘  [Watch on Netflix]    │
│               [Watch on HBO Max]    │
└─────────────────────────────────────┘
```

| Component | Size | Notes |
|-----------|------|-------|
| Poster | 12×18 chars | Fixed width, ~2:3 aspect ratio |
| Gap | 1 char | Between poster and info |
| Info | Remaining | Flexible width |

## Pixel-Art Rendering

Uses Unicode half-block characters for 2 vertical pixels per character cell:

- `▄` (U+2584) - foreground color draws bottom half
- Background color draws top half
- Each cell = 2 vertical pixels with independent colors

**Rendering pipeline:**
1. Fetch poster from TMDB (w92 size, 92px wide)
2. Resize to 12×36 pixels using Pillow
3. Quantize to 256-color terminal palette
4. Convert pixel pairs to half-block characters with ANSI colors

**Color mapping:**
- Top pixel → background color
- Bottom pixel → foreground color
- Use `▄` character for all cells

## Image Fetching

**TMDB URL format:**
```
https://image.tmdb.org/t/p/w92/{poster_path}
```

**Fetch flow:**
1. Item selected → check for `poster_path`
2. No path → show placeholder
3. Path exists → check memory cache by TMDB ID
4. Cache hit → render immediately
5. Cache miss → show loading state, fetch async, cache, render

**Memory cache:**
- Dict on App instance: `{tmdb_id: PIL.Image}`
- Persists across screen changes within session
- No size limit (images are small)

**Async handling:**
- Textual worker for non-blocking fetch
- httpx for HTTP requests
- Cancel in-flight request if item changes

## Placeholder

ASCII placeholder for missing/loading/failed states:

```
┌──────────┐
│   ___    │
│  |   |   │
│  | > |   │
│  |___|   │
│    No    │
│  Poster  │
│          │
│          │
└──────────┘
```

| State | Display |
|-------|---------|
| Loading | Placeholder + "Loading..." |
| No poster_path | Placeholder + "No Poster" |
| Fetch failed | Placeholder + "No Poster" |
| Success | Rendered pixel-art |

Placeholder uses muted colors, same 12×18 dimensions as poster.

## File Structure

**New files:**
```
tui_layer/widgets/
├── poster_widget.py   # Widget with loading/render states
└── pixel_art.py       # Image → half-block conversion
```

**Modified files:**
```
tui_layer/widgets/detail_panel.py  # Horizontal layout with poster
tui_layer/stream_app.py            # Poster cache on App
```

**New dependency:**
- Pillow (image processing)

## Module Responsibilities

| Module | Purpose |
|--------|---------|
| `pixel_art.py` | Pure function: `image_to_half_blocks(image, width, height) -> Text` |
| `poster_widget.py` | Async fetch, cache lookup, state management, rendering |

## Testing Strategy

**pixel_art.py (unit):**
- Solid color image → uniform half-blocks
- Handles odd-height images
- Respects target dimensions
- Returns Rich Text with ANSI codes

**poster_widget.py (unit):**
- Placeholder when no item
- Placeholder when no poster_path
- Loading state while fetching
- Renders after successful fetch
- Placeholder on fetch error
- Cancels request on item change

**detail_panel.py (unit):**
- Horizontal layout structure
- Poster on left, info on right
- Fixed poster width

Visual accuracy verified through manual testing.
