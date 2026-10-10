# ==========================================================================
"""web_search.py
Provide web search operations for explicit application requests.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx

from lourihna_films.core.exceptions import ServiceError
from lourihna_films.core.http import get_json


class BraveSearch:
    """Documented Brave Web Search adapter. Offset is a page index."""

    def __init__(self, client: httpx.AsyncClient, key: str) -> None:
        self.client, self.key = client, key
        self.lock = asyncio.Lock()
        self.last_request = 0.0
        self.more = False

    async def search(self, query: str, page: int = 1) -> list[dict[str, Any]]:
        """Query the selected provider or catalog and preserve its pagination contract."""
        if not self.key:
            raise ServiceError(
                "Video search needs a Brave Search API key. Add it in Settings, or paste an OK.ru video URL."
            )
        if not 1 <= page <= 10:
            raise ServiceError("Brave Search supports at most 10 result pages.")
        async with self.lock:
            await asyncio.sleep(max(0, 1.1 - (time.monotonic() - self.last_request)))
            self.last_request = time.monotonic()
            data = await get_json(
                self.client,
                "https://api.search.brave.com/res/v1/web/search",
                headers={"X-Subscription-Token": self.key},
                params={
                    "q": f"site:ok.ru/video {query}",
                    "count": 20,
                    "offset": page - 1,
                    "text_decorations": False,
                },
            )
            self.more = (
                bool(data.get("query", {}).get("more_results_available", False))
                and page < 10
            )
            return data.get("web", {}).get("results", [])
