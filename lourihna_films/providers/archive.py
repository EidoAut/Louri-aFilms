# ==========================================================================
"""archive.py
Public Archive search, metadata and declared public playback files.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from lourihna_films.models.video import VideoResult

import re
from urllib.parse import quote, urlsplit

from lourihna_films.core.exceptions import ServiceError
from lourihna_films.models.video import VideoResult
from lourihna_films.providers.okru import normalize_title

COLLECTIONS = {
    "Movies": "feature_films",
    "Series": "classic_tv",
    "Documentaries": "prelinger",
    "Animation": "animationandcartoons",
}


def public_files(data: dict[str, Any], identifier: str | int) -> list[dict[str, Any]]:
    """Use only files declared public by the official item metadata API."""
    metadata = data.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    restricted = (
        data.get("is_dark"),
        data.get("is_restricted"),
        data.get("nodownload"),
        metadata.get("access-restricted-item"),
        metadata.get("nodownload"),
    )
    if any(str(value).lower() in ("true", "1") for value in restricted):
        raise ServiceError("Este vídeo no está disponible para reproducir aquí.")
    choices = set()
    files = data.get("files", [])
    if not isinstance(files, list):
        files = []
    for item in files:
        if not isinstance(item, dict) or str(item.get("private", "false")).lower() in (
            "true",
            "1",
        ):
            continue
        name = item.get("name", "")
        if (
            not isinstance(name, str)
            or not name
            or any(x in ("..", ".") for x in name.replace("\\", "/").split("/"))
            or name.startswith(("/", "\\"))
        ):
            continue
        extension = name.rsplit(".", 1)[-1].lower()
        if extension not in ("mp4", "webm", "ogv"):
            continue
        try:
            size = int(item.get("size", 0))
        except (ValueError, TypeError, OverflowError):
            size = 0
        choices.add(
            (
                {"mp4": 0, "webm": 1, "ogv": 2}[extension],
                size if size > 0 else 10**12,
                name,
            )
        )
    if not choices:
        raise ServiceError(
            "Esta ficha ya no contiene archivos de vídeo. Prueba otra fuente."
        )
    return [
        {
            "url": f"https://archive.org/download/{quote(identifier, safe='')}/{quote(name, safe='')}",
            "quality": name.rsplit(".", 1)[-1],
        }
        for extension, _, name in sorted(choices)[:20]
    ]


def archive_id_from_url(url: str) -> str | None:
    """Extract a safe Internet Archive item identity from its official page URL."""
    try:
        parts = urlsplit(url.strip())
        if (
            parts.scheme not in ("http", "https")
            or parts.hostname not in {"archive.org", "www.archive.org"}
            or parts.username
            or parts.password
            or parts.port not in (None, 80, 443)
        ):
            return None
        match = re.fullmatch(
            r"/(?:details|embed)/([A-Za-z0-9][A-Za-z0-9_.-]{0,99})/?", parts.path
        )
        return match[1] if match else None
    except ValueError:
        return None


def plain(value: object) -> str:
    """Normalize public HTML text into a displayable plain string."""
    if isinstance(value, list):
        value = " / ".join(str(x) for x in value)
    return normalize_title(str(value or ""))[:10000]


class ArchiveProvider:
    """Search official Internet Archive collections and public media metadata."""

    cache_namespace = "archive-v1"

    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client
        self.more = False

    async def _json(self, url, **kwargs):
        try:
            response = await self.client.get(
                url, timeout=15, follow_redirects=False, **kwargs
            )
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict) or data.get("error"):
                raise ValueError()
            return data
        except (httpx.HTTPError, ValueError) as exc:
            raise ServiceError(
                "Internet Archive is unavailable. Your saved videos remain in Library."
            ) from exc

    def _video(self, item):
        identifier = str(item.get("identifier", ""))
        url = f"https://archive.org/details/{identifier}"
        if archive_id_from_url(url) != identifier:
            return None
        if str(item.get("access-restricted-item", "false")).lower() in ("true", "1"):
            return None
        return VideoResult(
            id=identifier,
            provider="archive",
            title=plain(item.get("title")) or identifier,
            description=plain(item.get("description")),
            thumbnail_url=f"https://archive.org/services/img/{identifier}",
            original_url=url,
            embed_url=f"https://archive.org/embed/{identifier}",
        )

    async def search(
        self, query: str, page: int = 1, collection: str | None | None = None
    ) -> list[VideoResult]:
        """Query the selected provider or catalog and preserve its pagination contract."""
        self.more = False
        if not 1 <= page <= 500:
            return []
        direct = archive_id_from_url(query)
        if direct:
            return [await self.get_video(direct)] if page == 1 else []
        # User input is a literal phrase, never an injected Lucene filter.
        words = re.findall(r"[^\W_]+", query, re.UNICODE)
        terms = " AND ".join('"' + word + '"' for word in words)
        filters = "mediatype:movies AND NOT access-restricted-item:true"
        if collection:
            if collection not in COLLECTIONS.values():
                raise ServiceError("Unsupported public collection.")
            filters += f" AND collection:{collection}"
        if terms:
            filters += f" AND ({terms})"
        data = await self._json(
            "https://archive.org/advancedsearch.php",
            params={
                "q": filters,
                "output": "json",
                "rows": 20,
                "page": page,
                "fl[]": [
                    "identifier",
                    "title",
                    "description",
                    "access-restricted-item",
                ],
                "sort[]": "downloads desc",
            },
        )
        result = data.get("response")
        if not isinstance(result, dict) or not isinstance(result.get("docs"), list):
            raise ServiceError(
                "Internet Archive returned an unrecognized search response."
            )
        self.more = page < 500 and page * 20 < int(result.get("numFound", 0))
        return [
            video
            for item in result["docs"]
            if isinstance(item, dict) and (video := self._video(item))
        ]

    async def get_video(self, identifier: str | int) -> VideoResult:
        """Resolve a supported provider identifier into a normalized video record."""
        if (
            archive_id_from_url(f"https://archive.org/details/{identifier}")
            != identifier
        ):
            raise ServiceError("Unsupported Internet Archive identifier.")
        data = await self._json(f"https://archive.org/metadata/{identifier}")
        metadata = data.get("metadata", {})
        if not isinstance(metadata, dict) or metadata.get("mediatype") != "movies":
            raise ServiceError("This Archive item is not an available public video.")
        video = self._video({**metadata, "identifier": identifier})
        if not video:
            raise ServiceError("This Archive item has restricted access.")
        for file in data.get("files", []):
            if not isinstance(file, dict) or str(
                file.get("private", "false")
            ).lower() in ("true", "1"):
                continue
            try:
                duration = float(file.get("length", 0))
                if 0 < duration < 31536000:
                    video.duration_seconds = int(duration)
                    break
            except (TypeError, ValueError):
                pass
        return video

    async def get_embed_url(self, identifier: str | int) -> str:
        """Return the supported official embedding URL for the identifier."""
        return (await self.get_video(identifier)).embed_url

    async def playback_sources(self, identifier: str | int) -> list[dict[str, Any]]:
        """Return available permitted public formats without bypassing access restrictions."""
        if (
            archive_id_from_url(f"https://archive.org/details/{identifier}")
            != identifier
        ):
            raise ServiceError("Enlace de vídeo no válido.")
        data = await self._json(f"https://archive.org/metadata/{identifier}")
        return public_files(data, identifier)
