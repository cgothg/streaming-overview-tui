# streaming-overview-tui
Search movies and tv-shows across your streaming services. Get direct links to watch them based on your subscriptions.

## The architecture
````
┌─────────────────────────────────────────────────┐
│                    TUI Layer                    │
│         (Textual or rich + prompt_toolkit)      │
├─────────────────────────────────────────────────┤
│                  Search Engine                  │
│      (fuzzy search, filters by service)         │
├─────────────────────────────────────────────────┤
│                 Data Layer                      │
│   (TMDB API client, local cache/SQLite)         │
├─────────────────────────────────────────────────┤
│                 Config Layer                    │
│  (user's subscriptions, region, preferences)    │
└─────────────────────────────────────────────────┘
````

### TUI Layer
The TUI layer is built using the Textual framework, providing a rich and interactive text-based user interface.
It allows users to search for movies and TV shows, filter results based on their streaming subscriptions, 
and get direct links to watch content. The TUI is designed to be user-friendly and responsive, making it easy to 
navigate through search results. Links can be opened directly from the interface. At first launch a configuration
wizard will guide the user to set up their preferences. This includes selecting streaming services they are subscribed to,
setting their region for accurate content availability, and other personal preferences. This can always be changed later.

### Search Engine
The search engine component handles the logic for searching movies and TV shows. It uses fuzzy search algorithms
to provide relevant results even with partial or misspelled queries. Users can filter search results based on their
streaming service subscriptions, ensuring they only see content they can access. The search engine interacts with the 
data layer to fetch and filter content based on user preferences. Local caching is implemented to speed up repeated
searches.

### Data Layer
The data layer is responsible for fetching movie and TV show data from the TMDB (The Movie Database) API. 
It includes a client that handles API requests and responses, ensuring efficient data retrieval. To improve performance 
and reduce API calls, a local cache or SQLite database is used to store frequently accessed data. This layer abstracts the complexities
of data retrieval, providing a simple interface for the search engine to access content information. 

### Config Layer
The config layer manages user preferences and settings. It allows users to specify their streaming service subscriptions,
region, and other preferences that influence search results. The configuration is stored locally, enabling the TUI to 
customize the user experience based on individual settings. This layer provides methods to read and update user configurations,
ensuring that changes are reflected in the search results and overall application behavior.

## Folder structure
```
.
├── pyproject.toml
├── README.md
├── streaming_overview_tui
│   ├── config_layer
│   │   ├── config.py
│   │   └── __init__.py
│   ├── data_layer
│   │   └── __init__.py
│   ├── __init__.py
│   ├── run.py
│   ├── search_engine
│   │   └── __init__.py
│   └── tui_layer
│       ├── __init__.py
│       ├── main_screen.py
│       ├── setup_screen.py
│       └── stream_app.py
├── tests
│   ├── __init__.py
│   └── unit
│       ├── config_layer
│       │   └── __init__.py
│       ├── data_layer
│       │   └── __init__.py
│       ├── __init__.py
│       ├── search_engine
│       │   └── __init__.py
│       └── tui_layer
│           └── __init__.py
└── uv.lock
```

