# ==========================================================================
"""okru.py
OK.ru provider adapter; search, identity and row normalization stay separate.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

from typing import TYPE_CHECKING

from lourihna_films.providers.result_normalization import (
    normalize_title as normalize_title,
)

if TYPE_CHECKING:
    from lourihna_films.models.video import VideoResult
    from lourihna_films.providers.base import VideoProvider
    from lourihna_films.providers.direct_search import DirectPublicSearch
    from lourihna_films.providers.public_search import PublicSearch
    from lourihna_films.providers.web_search import BraveSearch

from lourihna_films.core.exceptions import ServiceError
from lourihna_films.models.okru_identity import OKRuIdentity, video_id_from_url
from lourihna_films.models.video import VideoResult
from lourihna_films.providers.base import VideoProvider
from lourihna_films.providers.result_normalization import (
    normalize_results,
)


class OKRuProvider(VideoProvider):
    """Adapt public OK.ru discovery results to the common video provider contract."""

    def __init__(
        self, web_search: DirectPublicSearch | BraveSearch | PublicSearch | None
    ) -> None:
        self.web_search = web_search
        self.more = False

    @property
    def cache_namespace(self) -> str:
        """Identify the active discovery implementation for cache isolation."""
        return "normalized-v2:" + getattr(
            self.web_search, "cache_namespace", type(self.web_search).__name__
        )

    @property
    def notice(self) -> str:
        """Expose provider limitations without treating missing results as verified availability."""
        return getattr(self.web_search, "notice", "")

    async def get_video(self, video_id: str) -> VideoResult:
        """Resolve a supported provider identifier into a normalized video record."""
        identity = OKRuIdentity(video_id)
        return VideoResult(
            id=video_id,
            provider="okru",
            title=f"OK.ru video {video_id}",
            original_url=identity.original_url,
            embed_url=identity.embed_url,
        )

    async def get_embed_url(self, video_id: str) -> str:
        """Return the supported official embedding URL for the identifier."""
        return OKRuIdentity(video_id).embed_url

    async def search(self, query: str, page: int = 1) -> list[VideoResult]:
        """Query the selected provider or catalog and preserve its pagination contract."""
        self.more = False
        direct = video_id_from_url(query)
        if direct:
            return [await self.get_video(direct)] if page == 1 else []
        if query.startswith(("http:", "https:")):
            raise ServiceError("Unsupported URL. Use https://ok.ru/video/<numeric ID>.")
        rows = await self.web_search.search(query, page)
        self.more = self.web_search.more
        return normalize_results(
            rows, getattr(self.web_search, "source_name", "OK.ru search")
        )
