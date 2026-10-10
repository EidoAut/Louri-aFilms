import hashlib
from teleputin.core.exceptions import ServiceError
from teleputin.providers.okru import normalize_title


class SearchService:
    def __init__(self, providers, repository, metadata=None):
        self.providers, self.repository = providers, repository
        self.metadata = metadata

    async def search(self, query, page=1, provider="okru", remember=True):
        query = normalize_title(query)[:500]
        if not query: return {"items": [], "more": False}
        adapter = self.providers[provider]
        namespace = getattr(adapter, "cache_namespace", type(getattr(adapter, "web_search", adapter)).__name__)
        key = hashlib.sha256(f"{provider}:{namespace}:{query.casefold()}:{page}".encode()).hexdigest()
        if remember: self.repository.remember_query(query)
        cached = self.repository.cache_get(key)
        if cached is not None:
            self.repository.save_videos(cached["items"])
            return cached
        adapter = self.providers[provider]
        try:
            videos = await adapter.search(query, page)
        except ServiceError:
            stale = self.repository.cache_get(key, allow_stale=True)
            if stale is not None:
                return {**stale, "notice": "Source unavailable. Showing cached search results."}
            raise
        data = {"items": [v.card() for v in videos], "more": bool(getattr(adapter, "more", False))}
        if getattr(adapter, "notice", ""): data["notice"] = adapter.notice
        self.repository.save_videos(data["items"])
        self.repository.cache_put(key, query, provider, data)
        return data
