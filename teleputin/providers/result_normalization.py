"""Convert heterogeneous public search rows into validated, deduplicated videos."""
import html
import re
import unicodedata
from urllib.parse import urlsplit
from teleputin.models.okru_identity import OKRuIdentity, video_id_from_url
from teleputin.models.video import VideoResult


def normalize_title(value):
    if not isinstance(value, str): return ""
    return " ".join(unicodedata.normalize("NFKC", html.unescape(re.sub(r"<[^>]+>", "", value))).split())


def public_image_url(value):
    if not isinstance(value, str): return None
    try:
        parts = urlsplit(value)
        return value if parts.scheme == "https" and parts.hostname and not parts.username and not parts.password and parts.port in (None, 443) else None
    except ValueError:
        return None


def normalize_results(rows, source="OK.ru search"):
    videos = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("url"), str): continue
        identifier = video_id_from_url(row["url"])
        if not identifier: continue
        identity = OKRuIdentity(identifier)
        title = normalize_title(row.get("title"))[:1000]
        description = normalize_title(row.get("description"))[:10000]
        thumbnail = row.get("thumbnail")
        image = public_image_url(thumbnail.get("src")) if isinstance(thumbnail, dict) else None
        duration = row.get("duration_seconds")
        duration = duration if isinstance(duration, int) and not isinstance(duration, bool) and duration >= 0 else None
        video = videos.get(identifier)
        if video is None:
            video = VideoResult(id=identifier, provider="okru", title=title or f"OK.ru video {identifier}", original_url=identity.original_url, embed_url=identity.embed_url, source_name=source)
            videos[identifier] = video
        if title and video.title == f"OK.ru video {identifier}": video.title = title
        if description and not video.description: video.description = description
        if image and not video.thumbnail_url: video.thumbnail_url = image
        if duration is not None and video.duration_seconds is None: video.duration_seconds = duration
    return list(videos.values())
