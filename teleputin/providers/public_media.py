"""Resolve media explicitly published in an anonymous OK.ru page.

Independent implementation; no third-party downloader code is copied. Never
call private metadata endpoints, use cookies, decrypt media, or cache signed URLs.
"""
import json
from html.parser import HTMLParser
from urllib.parse import urlsplit

from teleputin.core.exceptions import ServiceError
from teleputin.core.public_http import PublicPageReader
from teleputin.models.okru_identity import OKRuIdentity

QUALITY_ORDER = ("mobile", "lowest", "low", "sd", "hd", "full", "quad", "ultra")


def media_url_allowed(value):
    try:
        parts = urlsplit(value)
        host = parts.hostname or ""
        return (parts.scheme == "https" and not parts.username and not parts.password
                and parts.port in (None, 443) and host.endswith(".okcdn.ru")
                and bool(parts.path) and not parts.fragment)
    except (ValueError, TypeError):
        return False


class MediaParser(HTMLParser):
    def __init__(self, identifier):
        super().__init__(convert_charrefs=True)
        self.identifier = identifier
        self.formats = []

    def handle_starttag(self, tag, attrs):
        raw = dict(attrs).get("data-options")
        if not raw:
            return
        try:
            options = json.loads(raw)
            metadata = options.get("flashvars", {}).get("metadata", {})
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
            if metadata.get("provider") != "UPLOADED_ODKL":
                return
            movie = metadata.get("movie", {})
            # Do not accidentally select a recommended or unrelated video.
            if str(movie.get("id", "")) != self.identifier:
                return
            if metadata.get("drm") or metadata.get("licenseUrl"):
                return
            for item in metadata.get("videos", []):
                if not isinstance(item, dict):
                    continue
                name, url = item.get("name"), item.get("url")
                if not item.get("disallowed") and name in QUALITY_ORDER and isinstance(url, str) and media_url_allowed(url):
                    self.formats.append((QUALITY_ORDER.index(name), url))
        except (ValueError, TypeError, AttributeError):
            return


async def resolve_public_formats(client, original_url):
    identity = OKRuIdentity.from_url(original_url)
    document = await PublicPageReader(client).read(identity.original_url)
    parser = MediaParser(identity.identifier)
    parser.feed(document)
    if not parser.formats:
        raise ServiceError("This public page does not expose a supported video file. Use the official player; no restricted source was accessed.")
    # Prefer the best published rendition. Re-resolve each time: CDN links expire.
    ordered = sorted(set(parser.formats), key=lambda item: (item[0] > QUALITY_ORDER.index("hd"), -item[0]))
    return [{"url": url, "quality": QUALITY_ORDER[quality]} for quality, url in ordered]


async def resolve_public_media(client, original_url):
    return (await resolve_public_formats(client, original_url))[0]
