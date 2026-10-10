# ==========================================================================
"""base.py
Define the provider contract used by discovery and playback services.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lourihna_films.models.video import VideoResult
    from lourihna_films.providers.base import VideoProvider
from abc import ABC, abstractmethod

from lourihna_films.models.video import VideoResult


class VideoProvider(ABC):
    """Provide normalized discovery records and official playback identities."""

    @abstractmethod
    async def search(self, query: str, page: int = 1) -> list[VideoResult]:
        """Return real candidates for a one-based result page."""
        ...

    @abstractmethod
    async def get_video(self, video_id: str) -> VideoResult:
        """Return the metadata available for one provider identifier."""
        ...

    @abstractmethod
    async def get_embed_url(self, video_id: str) -> str | None:
        """Return an official embed URL, or None when embedding is unavailable."""
        ...
