# ==========================================================================
"""logging.py
Configure bounded application logs without exposing provider credentials.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_MAX_BYTES = 1_000_000
LOG_BACKUP_COUNT = 3


def configure_logging(directory: Path) -> None:
    """Configure bounded local diagnostics while suppressing HTTP credential-bearing URLs."""
    handler = RotatingFileHandler(
        directory / "lourihna_films.log",
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.WARNING)
    # HTTP request URLs may contain API keys. Never enable wire logging.
    logging.getLogger("httpx").setLevel(logging.CRITICAL)
    logging.getLogger("httpcore").setLevel(logging.CRITICAL)
