"""Read only public HTML metadata; never internal player state or media streams."""
import math
import json
import re
from html.parser import HTMLParser
from teleputin.core.public_http import PublicPageReader, robots_allow
from teleputin.core.exceptions import ServiceError
from teleputin.models.okru_identity import OKRuIdentity, video_id_from_url
from teleputin.providers.result_normalization import normalize_title, public_image_url


def duration_seconds(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0:
        return int(value)
    value = str(value or "")
    if value.isdigit(): return int(value)
    match = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?", value)
    if match and any(match.groups()):
        h, m, s = (float(x or 0) for x in match.groups())
        return int(h * 3600 + m * 60 + s)
    return None


class MetadataParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta, self.documents = {}, []
        self.json_script = False
        self.script = ""

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == "meta":
            key = attrs.get("property") or attrs.get("name") or attrs.get("itemprop")
            if key and attrs.get("content"): self.meta[key.lower()] = attrs["content"]
        if tag == "script" and attrs.get("type", "").lower() == "application/ld+json":
            self.json_script, self.script = True, ""

    def handle_data(self, value):
        if self.json_script: self.script += value

    def handle_endtag(self, tag):
        if tag == "script" and self.json_script:
            try: self.documents.append(json.loads(self.script))
            except (ValueError, RecursionError): pass
            self.json_script = False


def parse_public_metadata(document, video_id):
    parser = MetadataParser()
    parser.feed(document)
    meta = parser.meta
    canonical = meta.get("og:url")
    if canonical and video_id_from_url(canonical) != video_id: return {}
    videos = []
    def visit(node, depth=0):
        if depth > 12: return
        if isinstance(node, list):
            for child in node: visit(child, depth + 1)
        elif isinstance(node, dict):
            types = node.get("@type", [])
            if "VideoObject" in (types if isinstance(types, list) else [types]): videos.append(node)
            if "@graph" in node: visit(node["@graph"], depth + 1)
    for document in parser.documents: visit(document)
    matching = [v for v in videos if any(video_id_from_url(str(v.get(k, ""))) == video_id for k in ("url", "embedUrl", "contentUrl"))]
    video = matching[0] if matching else videos[0] if len(videos) == 1 and not any(videos[0].get(k) for k in ("url", "embedUrl")) else {}
    # Generic login, challenge and error-page titles are not video metadata.
    if not video and not meta.get("og:type", "").startswith("video"): return {}
    title = video.get("name") or meta.get("og:title")
    description = video.get("description") or meta.get("og:description") or meta.get("description")
    image = video.get("thumbnailUrl") or meta.get("og:image")
    if isinstance(image, list): image = next(iter(image), None)
    image = public_image_url(image)
    result = {"title": normalize_title(title)[:1000] if isinstance(title, str) else None,
              "description": normalize_title(description)[:10000] if isinstance(description, str) else None,
              "thumbnail_url": image,
              "duration_seconds": duration_seconds(video.get("duration") or meta.get("video:duration") or meta.get("duration"))}
    return {key: value for key, value in result.items() if value is not None}


class PublicMetadata:
    def __init__(self, client, reader=None):
        self.reader = reader or PublicPageReader(client)
        self.notice = ""

    @property
    def blocked(self): return self.reader.blocked

    async def fetch(self, video_id):
        self.notice = ""
        try:
            identity = OKRuIdentity(video_id)
            document = await self.reader.read(identity.original_url)
            fields = parse_public_metadata(document, video_id)
            if not fields: self.notice = "Public page contains no matching video metadata; playback remains unverified."
            return fields
        except (ServiceError, ValueError, RecursionError) as exc:
            self.notice = str(exc)
            return {}
