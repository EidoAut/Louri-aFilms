"""Non-secret preferences and environment credential resolution."""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]


def data_directory() -> Path:
    load_dotenv(ROOT.parent / ".env")
    default = Path(os.getenv("LOCALAPPDATA", str(Path.home()))) / "TelePutin" if os.name == "nt" else Path(os.getenv("XDG_DATA_HOME", str(Path.home() / ".local/share"))) / "TelePutin"
    path = Path(os.getenv("TELEPUTIN_DATA_DIR") or default)
    path.mkdir(parents=True, exist_ok=True)
    return path


def credentials(settings: dict) -> dict:
    environment_tmdb = bool(os.getenv("TMDB_TOKEN") or os.getenv("TMDB_API_KEY"))
    return {
        "tmdb_token": os.getenv("TMDB_TOKEN", "") if environment_tmdb else settings.get("tmdb_token", ""),
        "tmdb_key": os.getenv("TMDB_API_KEY", "") if environment_tmdb else settings.get("tmdb_key", ""),
        "brave_key": os.getenv("BRAVE_SEARCH_API_KEY") or settings.get("brave_key", ""),
        "language": os.getenv("TMDB_LANGUAGE") or settings.get("language", "en-US"),
    }
