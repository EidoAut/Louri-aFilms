# ==========================================================================
"""compatibility.py
Migrate legacy application data without deleting or overwriting originals.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

import os
import shutil
import sqlite3
import tempfile
from contextlib import closing

LEGACY_DIRECTORY = "TelePutin"
LEGACY_DATABASE = "teleputin.db"
LEGACY_DATA_ENV = "TELEPUTIN_DATA_DIR"
DATABASE_NAME = "lourihna_films.db"


def migrate_data(destination: Path, legacy: Path) -> None:
    """Copy a consistent SQLite snapshot; preserve existing destination data."""
    destination.mkdir(parents=True, exist_ok=True)
    source_database = legacy / LEGACY_DATABASE
    target_database = destination / DATABASE_NAME
    if target_database.exists() or not source_database.is_file():
        return
    with tempfile.TemporaryDirectory(prefix="migration-", dir=destination) as directory:
        staging = Path(directory) / DATABASE_NAME
        with closing(
            sqlite3.connect(source_database.as_uri() + "?mode=ro", uri=True)
        ) as source:
            with closing(sqlite3.connect(staging)) as target:
                source.backup(target)
                if target.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise RuntimeError("Existing library could not be migrated safely.")
        for name in ("artwork", "translation-models"):
            old_directory, new_directory = legacy / name, destination / name
            if old_directory.is_dir() and not new_directory.exists():
                shutil.copytree(old_directory, new_directory)
        # Hard-link publication fails rather than replacing a destination created concurrently.
        try:
            os.link(staging, target_database)
        except FileExistsError:
            return


def legacy_location(default_base: Path) -> Path:
    """Locate previous data only; all new writes use the new application directory."""
    return Path(os.environ.get(LEGACY_DATA_ENV) or default_base / LEGACY_DIRECTORY)
