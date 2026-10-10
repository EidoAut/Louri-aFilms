import asyncio
import time
from teleputin.core.http import get_json
from teleputin.core.exceptions import ServiceError


class BraveSearch:
    """Documented Brave Web Search adapter. Offset is a page index."""
    def __init__(self, client, key):
        self.client, self.key = client, key
        self.lock = asyncio.Lock()
        self.last_request = 0.0
        self.more = False

    async def search(self, query, page=1):
        if not self.key:
            raise ServiceError("Video search needs a Brave Search API key. Add it in Settings, or paste an OK.ru video URL.")
        if not 1 <= page <= 10:
            raise ServiceError("Brave Search supports at most 10 result pages.")
        async with self.lock:
            await asyncio.sleep(max(0, 1.1 - (time.monotonic() - self.last_request)))
            self.last_request = time.monotonic()
            data = await get_json(self.client, "https://api.search.brave.com/res/v1/web/search", headers={"X-Subscription-Token": self.key}, params={"q": f"site:ok.ru/video {query}", "count": 20, "offset": page - 1, "text_decorations": False})
            self.more = bool(data.get("query", {}).get("more_results_available", False)) and page < 10
            return data.get("web", {}).get("results", [])
