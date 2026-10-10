# ==========================================================================
"""search_service.py
Provide search service operations for explicit application requests.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from lourihna_films.database.repositories import Repository
    from lourihna_films.providers.base import VideoProvider
    from lourihna_films.services.metadata_service import MetadataService
    from lourihna_films.services.search_service import SearchService

import hashlib

from lourihna_films.core.exceptions import ServiceError
from lourihna_films.providers.okru import normalize_title


class SearchService:
    """Coordinate provider search with persistent snapshots and query history."""

    def __init__(
        self,
        providers: dict[str, VideoProvider],
        repository: Repository,
        metadata: MetadataService | None = None,
    ) -> None:
        self.providers, self.repository = providers, repository
        self.metadata = metadata

    async def search(
        self, query: str, page: int = 1, provider: str = "okru", remember: bool = True
    ) -> dict[str, Any]:
        """Query the selected provider or catalog and preserve its pagination contract."""
        query = normalize_title(query)[:500]
        if not query:
            return {"items": [], "more": False}
        adapter = self.providers[provider]
        namespace = getattr(
            adapter,
            "cache_namespace",
            type(getattr(adapter, "web_search", adapter)).__name__,
        )
        key = hashlib.sha256(
            f"{provider}:{namespace}:{query.casefold()}:{page}".encode()
        ).hexdigest()
        if remember:
            self.repository.remember_query(query)
        cached = self.repository.cache_get(key)
        if cached is not None:
            self.repository.save_videos(cached["items"])
            return cached
        adapter = self.providers[provider]
        try:
            videos = await adapter.search(query, page)
        except ServiceError:
            stale = self.repository.cache_get(key, allow_stale=True)
            if stale is not None:
                return {
                    **stale,
                    "notice": "Source unavailable. Showing cached search results.",
                }
            raise
        data = {
            "items": [v.card() for v in videos],
            "more": bool(getattr(adapter, "more", False)),
        }
        if getattr(adapter, "notice", ""):
            data["notice"] = adapter.notice
        self.repository.save_videos(data["items"])
        self.repository.cache_put(key, query, provider, data)
        return data
