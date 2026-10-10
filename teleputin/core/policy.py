"""Central operational limits for catalogs, artwork and candidate discovery."""
METADATA_TTL = 6 * 60 * 60
ARTWORK_MAX_BYTES = 8 * 1024 * 1024
ARTWORK_BUDGET_BYTES = 256 * 1024 * 1024
ARTWORK_CONCURRENCY = 6
ARTWORK_TIMEOUT = 8
ARTWORK_BATCH_TIMEOUT = 12
CANDIDATE_QUERY_LIMIT = 4
CANDIDATE_METADATA_LIMIT = 3
CANDIDATE_LIMIT = 40
FEATURE_MINUTES = 60
CATALOG_ROWS = {
    "Home": [("Trending Movies", "trending"), ("Popular Series", "series"), ("Science Fiction", 878), ("Horror", 27), ("Documentaries", 99)],
    "Movies": [("Trending Movies", "trending"), ("Popular Movies", "movies"), ("Science Fiction", 878), ("Horror", 27)],
    "Series": [("Popular Series", "series")],
    "Documentaries": [("Documentaries", 99)],
}

TITLE_MATCH_WEIGHT = 60
YEAR_MATCH_WEIGHT = 15
DIRECTOR_MATCH_WEIGHT = 10
RUNTIME_MATCH_WEIGHT = 20
FEATURE_LENGTH_WEIGHT = 10
CLIP_PENALTY = 35
STRONG_TITLE_MATCH = 0.8
RUNTIME_TOLERANCE_SECONDS = 600
RUNTIME_TOLERANCE_RATIO = 0.2

CATALOG_NAVIGATION_TTL = 300

# Bound background artwork work while navigating through many catalogs.
ARTWORK_QUEUE_LIMIT = 240

# End a discovery source even when several individually valid requests stall.
DISCOVERY_SOURCE_TIMEOUT = 20
