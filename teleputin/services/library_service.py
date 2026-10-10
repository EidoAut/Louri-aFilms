import re
from teleputin.core.exceptions import ServiceError
from teleputin.providers.okru import OKRuProvider, video_id_from_url
from teleputin.providers.public_metadata import PublicMetadata
from teleputin.services.metadata_service import MetadataService


def extract_links(text):
    candidates = re.findall(r"https?://[^\s<>\"']+", text, re.IGNORECASE)
    identifiers, rejected = [], 0
    for candidate in candidates:
        identifier = video_id_from_url(candidate.rstrip(".,;)]}"))
        if identifier is None: rejected += 1
        elif identifier not in identifiers: identifiers.append(identifier)
    if not identifiers: raise ServiceError("No supported OK.ru video links found. Paste https://ok.ru/video/<numeric ID> URLs.")
    if len(identifiers) > 100: raise ServiceError("Import up to 100 unique video links at a time. Split this list into smaller batches.")
    return identifiers, rejected


class LibraryService:
    def __init__(self, repository, client):
        self.repo = repository
        self.metadata = PublicMetadata(client)

    async def import_links(self, text, category=None, refresh=False):
        identifiers, rejected = extract_links(text)
        cards, unavailable = [], 0
        provider = OKRuProvider(None)
        # Save valid links first, so cancellation/offline operation never loses them.
        placeholders = [(await provider.get_video(identifier)).card() for identifier in identifiers]
        self.repo.save_videos(placeholders, category)
        cards = await MetadataService(self.repo, self.metadata).enrich(placeholders, refresh=refresh)
        self.repo.save_videos(cards, category)
        unavailable = sum(card["metadata_status"].startswith("Metadata unavailable") for card in cards)
        keys = {"okru:" + identifier for identifier in identifiers}
        cards = [item for item in self.repo.library() if item["key"] in keys]
        return {"items": cards, "more": False, "notice": f"Saved {len(cards)} video link(s). Metadata unavailable for {unavailable}. Unsupported links ignored: {rejected}. Playback availability is unverified."}
