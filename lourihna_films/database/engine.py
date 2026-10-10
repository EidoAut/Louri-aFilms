# ==========================================================================
"""engine.py
Create SQLite engines and application schemas on explicit request.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


from sqlalchemy import create_engine, text

from lourihna_films.database.models import Base


def create_database(path: str | Path) -> Engine:
    """Create the SQLite engine and application tables at the supplied path."""
    engine = create_engine(
        f"sqlite:///{path}", connect_args={"check_same_thread": False, "timeout": 10}
    )
    with engine.begin() as conn:
        version = conn.execute(text("PRAGMA user_version")).scalar()
        if version not in (0, 1, 2):
            raise RuntimeError("This database requires a newer LourihnaFilms version.")
        conn.execute(text("PRAGMA journal_mode=WAL"))
        Base.metadata.create_all(conn)
        # Version 2 is additive: all version 1 tables and data remain intact.
        conn.execute(text("PRAGMA user_version=2"))
    return engine
