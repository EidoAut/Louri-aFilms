"""Strict OK.ru identity; constructing an embed URL never proves playback."""
import re
from dataclasses import dataclass
from urllib.parse import urlsplit
from teleputin.core.exceptions import ServiceError

def video_id_from_url(url: str) -> str | None:
    if not isinstance(url, str): return None
    try:
        parts = urlsplit(url.strip())
        if parts.scheme not in ("http", "https") or parts.hostname not in {"ok.ru", "www.ok.ru", "m.ok.ru"} or parts.username or parts.password or parts.port not in (None, 80, 443):
            return None
        match = re.fullmatch(r"/(?:video|videoembed)/([0-9]{1,20})/?", parts.path)
        return match[1] if match else None
    except ValueError:
        return None


@dataclass(frozen=True)
class OKRuIdentity:
    identifier: str

    def __post_init__(self):
        if not isinstance(self.identifier, str) or not re.fullmatch(r"[0-9]{1,20}", self.identifier):
            raise ServiceError("Unsupported OK.ru video identifier.")

    @classmethod
    def from_url(cls, url):
        identifier = video_id_from_url(url) if isinstance(url, str) else None
        if not identifier: raise ServiceError("Unsupported URL. Use https://ok.ru/video/<numeric ID>.")
        return cls(identifier)

    @property
    def original_url(self): return f"https://ok.ru/video/{self.identifier}"

    @property
    def embed_url(self): return f"https://ok.ru/videoembed/{self.identifier}"
