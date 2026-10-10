# ==========================================================================
"""unified_search.py
Federate independent searches without confusing catalog entries with videos.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from lourihna_films.database.repositories import Repository
    from lourihna_films.services.search_service import SearchService
    from lourihna_films.services.tmdb_service import TMDBService

import asyncio
import logging


async def search_all(
    query: str,
    search: SearchService,
    tmdb: TMDBService,
    repository: Repository,
    metadata_enabled: bool,
    cursors: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Search supported providers using independent cursors and merge real results."""
    pages = (
        {
            **{name: 1 for name in search.providers},
            **({"movie": 1, "tv": 1} if metadata_enabled else {}),
        }
        if cursors is None
        else dict(cursors)
    )
    repository.remember_query(query)

    async def fetch(name, page):
        """Fetch and normalize available public metadata for the requested video identifier."""
        try:
            if name in ("movie", "tv"):
                items = await tmdb.search(query, name, page)
                return {"items": items, "more": len(items) == 20 and page < 500}
            return await search.search(query, page, provider=name, remember=False)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logging.warning(
                "Search provider %s unavailable (%s)", name, type(exc).__name__
            )
            return {"items": [], "more": False, "notice": "unavailable"}

    primary = None
    if cursors is None and "okru" in pages:
        primary = await fetch("okru", pages.pop("okru"))
        if primary["items"]:
            pages = {
                name: page for name, page in pages.items() if name in ("movie", "tv")
            }
    results = await asyncio.gather(*(fetch(name, page) for name, page in pages.items()))
    if primary is not None:
        pages = {"okru": 1, **pages}
        results = [primary, *results]
    # Saved items remain available even if every remote provider fails.
    items = repository.library(query) if cursors is None else []
    unique = {item["key"]: item for item in items}
    following, notices = {}, []
    for (name, page), result in zip(pages.items(), results):
        for item in result["items"]:
            unique.setdefault(item["key"], item)
        if result.get("more"):
            following[name] = page + 1
        if result.get("notice"):
            notices.append(name)
    return {
        "items": list(unique.values()),
        "more": bool(following),
        "cursors": following,
        "notice": ", ".join(notices),
    }
