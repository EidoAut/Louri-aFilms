# ==========================================================================
"""metadata_service.py
Cached public metadata enrichment without modifying the user's library.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from lourihna_films.database.repositories import Repository
    from lourihna_films.providers.public_metadata import PublicMetadata

from lourihna_films.models.okru_identity import video_id_from_url

METADATA_TTL = 86400
NEGATIVE_TTL = 300


class MetadataService:
    """Enrich known video identities with cached and public metadata."""

    def __init__(self, repository: Repository, reader: PublicMetadata) -> None:
        self.repo, self.reader = repository, reader
        self.notice = ""

    async def enrich(
        self, items: list[dict[str, Any]], refresh: bool = False
    ) -> list[dict[str, Any]]:
        """Merge cached or public metadata into a bounded set of video cards."""
        result, notices = [], []
        for item in items:
            identifier = (
                video_id_from_url(item.get("original_url", ""))
                if item.get("provider") == "okru"
                else None
            )
            if not identifier:
                result.append(dict(item))
                continue
            key = "metadata:" + identifier
            fields = None if refresh else self.repo.cache_get(key)
            stale = False
            if fields is None:
                already_blocked = self.reader.blocked
                fields = await self.reader.fetch(identifier)
                if self.reader.notice:
                    notices.append(self.reader.notice)
                if not fields:
                    previous = self.repo.cache_get(key, allow_stale=True)
                    if previous:
                        fields, stale = previous, True
                        notices.append(
                            "Using cached public metadata; current availability is unknown."
                        )
                if not stale and not already_blocked:
                    self.repo.cache_put(
                        key,
                        identifier,
                        "okru-public-html",
                        fields,
                        ttl=METADATA_TTL if fields else NEGATIVE_TTL,
                    )
            card = dict(item)
            for name, value in fields.items():
                if value is not None and (
                    name != "title" or not card.get("local_title")
                ):
                    card[name] = value
            if fields.get("thumbnail_url"):
                card["poster"] = fields["thumbnail_url"]
            if fields.get("description"):
                card["overview"] = fields["description"]
            card["metadata_status"] = (
                "Cached public metadata (stale)"
                if stale
                else "Public page metadata"
                if fields
                else "Metadata unavailable; link saved"
            )
            result.append(card)
        self.notice = " ".join(dict.fromkeys(notices))
        return result
