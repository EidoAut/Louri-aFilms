# ==========================================================================
"""config.py
Non-secret preferences and environment credential resolution.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]


def data_directory() -> Path:
    """Resolve the primary user directory and migrate legacy data on explicit startup."""
    load_dotenv(ROOT.parent / ".env")
    from lourihna_films.core.compatibility import legacy_location, migrate_data

    base = (
        Path(os.getenv("LOCALAPPDATA", str(Path.home())))
        if os.name == "nt"
        else Path(os.getenv("XDG_DATA_HOME", str(Path.home() / ".local/share")))
    )
    path = Path(os.getenv("LOURIHNA_FILMS_DATA_DIR") or base / "lourihna_films")
    path.mkdir(parents=True, exist_ok=True)
    if not os.getenv("LOURIHNA_FILMS_DATA_DIR"):
        migrate_data(path, legacy_location(base))
    return path


def credentials(settings: dict) -> dict:
    """Resolve environment overrides and saved provider preferences without logging secrets."""
    environment_tmdb = bool(os.getenv("TMDB_TOKEN") or os.getenv("TMDB_API_KEY"))
    return {
        "tmdb_token": os.getenv("TMDB_TOKEN", "")
        if environment_tmdb
        else settings.get("tmdb_token", ""),
        "tmdb_key": os.getenv("TMDB_API_KEY", "")
        if environment_tmdb
        else settings.get("tmdb_key", ""),
        "brave_key": os.getenv("BRAVE_SEARCH_API_KEY") or settings.get("brave_key", ""),
        "language": os.getenv("TMDB_LANGUAGE") or settings.get("language", "en-US"),
    }
