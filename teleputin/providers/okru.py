"""OK.ru provider adapter; search, identity and row normalization stay separate."""
from teleputin.models.okru_identity import OKRuIdentity, video_id_from_url
from teleputin.providers.result_normalization import normalize_title, normalize_results
from teleputin.models.video import VideoResult
from teleputin.providers.base import VideoProvider
from teleputin.core.exceptions import ServiceError


class OKRuProvider(VideoProvider):
    def __init__(self, web_search):
        self.web_search = web_search
        self.more = False

    @property
    def cache_namespace(self):
        return "normalized-v2:" + getattr(self.web_search, "cache_namespace", type(self.web_search).__name__)

    @property
    def notice(self): return getattr(self.web_search, "notice", "")

    async def get_video(self, video_id):
        identity = OKRuIdentity(video_id)
        return VideoResult(id=video_id, provider="okru", title=f"OK.ru video {video_id}", original_url=identity.original_url, embed_url=identity.embed_url)

    async def get_embed_url(self, video_id): return OKRuIdentity(video_id).embed_url

    async def search(self, query, page=1):
        self.more = False
        direct = video_id_from_url(query)
        if direct: return [await self.get_video(direct)] if page == 1 else []
        if query.startswith(("http:", "https:")):
            raise ServiceError("Unsupported URL. Use https://ok.ru/video/<numeric ID>.")
        rows = await self.web_search.search(query, page)
        self.more = self.web_search.more
        return normalize_results(rows, getattr(self.web_search, "source_name", "OK.ru search"))
