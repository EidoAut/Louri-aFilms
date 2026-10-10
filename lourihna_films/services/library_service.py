# ==========================================================================
"""library_service.py
Provide library service operations for explicit application requests.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from lourihna_films.database.repositories import Repository
    from lourihna_films.services.metadata_service import MetadataService

import re

from lourihna_films.core.exceptions import ServiceError
from lourihna_films.providers.okru import OKRuProvider, video_id_from_url
from lourihna_films.providers.public_metadata import PublicMetadata
from lourihna_films.services.metadata_service import MetadataService


def extract_links(text: str) -> tuple[list[str], int]:
    """Extract unique supported video identifiers and count rejected links."""
    candidates = re.findall(r"https?://[^\s<>\"']+", text, re.IGNORECASE)
    identifiers, rejected = [], 0
    for candidate in candidates:
        identifier = video_id_from_url(candidate.rstrip(".,;)]}"))
        if identifier is None:
            rejected += 1
        elif identifier not in identifiers:
            identifiers.append(identifier)
    if not identifiers:
        raise ServiceError(
            "No supported OK.ru video links found. Paste https://ok.ru/video/<numeric ID> URLs."
        )
    if len(identifiers) > 100:
        raise ServiceError(
            "Import up to 100 unique video links at a time. Split this list into smaller batches."
        )
    return identifiers, rejected


class LibraryService:
    """Preserve imported public links and coordinate optional metadata enrichment."""

    def __init__(self, repository: Repository, client: httpx.AsyncClient) -> None:
        self.repo = repository
        self.metadata = PublicMetadata(client)

    async def import_links(
        self, text: str, category: str | None = None, refresh: bool = False
    ) -> dict[str, Any]:
        """Persist valid links before fetching optional metadata; report unavailable items."""
        identifiers, rejected = extract_links(text)
        cards, unavailable = [], 0
        provider = OKRuProvider(None)
        # Save valid links first, so cancellation/offline operation never loses them.
        placeholders = [
            (await provider.get_video(identifier)).card() for identifier in identifiers
        ]
        self.repo.save_videos(placeholders, category)
        cards = await MetadataService(self.repo, self.metadata).enrich(
            placeholders, refresh=refresh
        )
        self.repo.save_videos(cards, category)
        unavailable = sum(
            card["metadata_status"].startswith("Metadata unavailable") for card in cards
        )
        keys = {"okru:" + identifier for identifier in identifiers}
        cards = [item for item in self.repo.library() if item["key"] in keys]
        return {
            "items": cards,
            "more": False,
            "notice": f"Saved {len(cards)} video link(s). Metadata unavailable for {unavailable}. Unsupported links ignored: {rejected}. Playback availability is unverified.",
        }
