# ==========================================================================
"""discovery_service.py
Real public collections with a durable snapshot for offline startup.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from lourihna_films.database.repositories import Repository
    from lourihna_films.services.search_service import SearchService

import asyncio

from lourihna_films.core.exceptions import ServiceError
from lourihna_films.core.policy import DISCOVERY_SOURCE_TIMEOUT
from lourihna_films.providers.archive import COLLECTIONS


class DiscoveryService:
    """Aggregate independent public collections with deadlines and retry cursors."""

    def __init__(self, search: SearchService, repository: Repository) -> None:
        self.search, self.repo = search, repository

    async def load(
        self,
        page: str,
        number: int = 1,
        active: list[str] | None = None,
        on_row: Callable[[dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        """Load independent public collections with deadlines and optional incremental row delivery."""
        categories = (
            [page]
            if page in COLLECTIONS
            else ["Movies", "Series", "Documentaries", "Animation"]
        )

        async def collection(category):
            key = f"collection-v2:{category}:{number}"
            cached = self.repo.cache_get(key)
            if cached is not None:
                return cached
            from lourihna_films.providers.archive import ArchiveProvider

            provider = ArchiveProvider(self.search.providers["archive"].client)
            videos = await provider.search(
                "", page=number, collection=COLLECTIONS[category]
            )
            items = [{**video.card(), "category": category} for video in videos]
            row = {
                "title": category + " · Internet Archive",
                "items": items,
                "source": category,
                "more": provider.more,
            }
            self.repo.save_videos(items)
            self.repo.cache_put(key, "", "archive", row, ttl=21600)
            return row

        async def okru():
            query = {"Series": "series episode", "Documentaries": "documentary"}.get(
                page, "full movie"
            )
            data = await self.search.search(query, number, remember=False)
            return {
                "title": "Public discovery · OK.ru",
                "items": data["items"],
                "notice": data.get("notice", ""),
                "source": "okru",
                "more": data["more"],
            }

        sources = [*categories, "okru"]
        if active is not None:
            sources = [source for source in sources if source in active]

        async def fetch(source):
            """Fetch and normalize available public metadata for the requested video identifier."""
            try:
                row = await asyncio.wait_for(
                    okru() if source == "okru" else collection(source),
                    timeout=DISCOVERY_SOURCE_TIMEOUT,
                )
            except TimeoutError as exc:
                raise ServiceError(
                    "Public source timed out. Retry to check again."
                ) from exc
            if on_row and row["items"]:
                on_row(row)
            return row

        results = await asyncio.gather(
            *(fetch(source) for source in sources), return_exceptions=True
        )
        rows, errors, remaining = [], [], []
        for source, result in zip(sources, results):
            if isinstance(result, BaseException):
                if not isinstance(result, ServiceError):
                    raise result
                errors.append(str(result))
                remaining.append(source)
                if source != "okru":
                    stale = self.repo.cache_get(
                        f"collection-v2:{source}:{number}", allow_stale=True
                    )
                    if stale:
                        rows.append(stale)
            else:
                if result.get("notice"):
                    errors.append(result["notice"])
                if result.get("more"):
                    remaining.append(source)
                if result["items"]:
                    rows.append(result)
        return {
            "rows": rows,
            "notice": " ".join(dict.fromkeys(errors)),
            "active": sources if errors else remaining,
            "number": number - 1 if errors else number,
        }
