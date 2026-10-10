# ==========================================================================
"""public_http.py
Bounded, paced public HTML transport shared by discovery and metadata.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from urllib.robotparser import RobotFileParser

    from lourihna_films.core.public_http import PublicPageReader

import asyncio
import re
from urllib.parse import unquote, urlsplit
from urllib.robotparser import RobotFileParser

from lourihna_films.core.exceptions import ServiceError

PAGE_LIMIT = 2_000_000
ROBOTS_LIMIT = 256_000
REQUEST_TIMEOUT = 8
REQUEST_DELAY = 1
MAX_CRAWL_DELAY = 15
CHALLENGES = (
    "cf-chl-",
    "challenge-form",
    "anomaly-modal",
    "g-recaptcha",
    "verify you are human",
)


class PublicPageError(ServiceError):
    """Own PublicPageError state and its explicit application contracts."""

    def __init__(self, message: str, reason: str = "unavailable") -> None:
        super().__init__(message)
        self.reason = reason


class PublicPageReader:
    """Own PublicPageReader state and its explicit application contracts."""

    def __init__(
        self, client: httpx.AsyncClient, origin: str = "https://ok.ru"
    ) -> None:
        self.client, self.origin = client, origin
        self.robots, self.blocked, self.last_request = None, False, 0
        self.lock = asyncio.Lock()

    async def _read(self, url, limit):
        async with self.client.stream(
            "GET",
            url,
            headers={"User-Agent": "LourihnaFilms/0.3 public-video-discovery"},
            timeout=REQUEST_TIMEOUT,
            follow_redirects=False,
        ) as response:
            status = response.status_code
            if status in (404, 410):
                raise PublicPageError("Public video page was not found.", "missing")
            if status != 200:
                raise PublicPageError(
                    f"Public source unavailable (HTTP {status}); no access bypass attempted.",
                    "restricted"
                    if status in (401, 403, 429) or 300 <= status < 400
                    else "unavailable",
                )
            chunks, size = [], 0
            async for chunk in response.aiter_bytes():
                size += len(chunk)
                if size > limit:
                    raise PublicPageError(
                        "Public response exceeds the size limit.", "oversize"
                    )
                chunks.append(chunk)
            document = b"".join(chunks).decode(
                response.encoding or "utf-8", errors="replace"
            )
            if any(marker in document.lower() for marker in CHALLENGES):
                raise PublicPageError(
                    "Public source requires browser verification; discovery stopped.",
                    "restricted",
                )
            return document

    async def read(self, url: str, limit: int = PAGE_LIMIT) -> str:
        """Fetch a bounded public document while respecting robots policy, pacing and access errors."""
        parts = urlsplit(url)
        if parts.scheme + "://" + parts.netloc != self.origin:
            raise PublicPageError("Unsupported public source origin.", "invalid")
        async with self.lock:
            if self.blocked:
                raise PublicPageError(
                    "Public discovery stopped after an access error.", "restricted"
                )
            try:
                if self.robots is None:
                    document = await self._read(
                        self.origin + "/robots.txt", ROBOTS_LIMIT
                    )
                    self.robots = RobotFileParser()
                    self.robots.parse(document.splitlines())
                if not robots_allow(self.robots, url):
                    raise PublicPageError(
                        "Public source is restricted by robots rules.", "restricted"
                    )
                delay = max(
                    REQUEST_DELAY, self.robots.crawl_delay("LourihnaFilms") or 0
                )
                if delay > MAX_CRAWL_DELAY:
                    raise PublicPageError(
                        "Public source requests a longer crawl delay.", "restricted"
                    )
                loop = asyncio.get_running_loop()
                await asyncio.sleep(max(0, delay - (loop.time() - self.last_request)))
                self.last_request = loop.time()
                return await self._read(url, limit)
            except PublicPageError as exc:
                # A missing individual video must not prevent checking other videos.
                if exc.reason != "missing" or self.robots is None:
                    self.blocked = True
                raise
            except (httpx.HTTPError, LookupError) as exc:
                self.blocked = True
                raise PublicPageError("Public source could not be reached.") from exc


def robots_allow(parser: RobotFileParser, url: str) -> bool:
    """Apply longest-match Allow/Disallow rules, including * and end anchors."""
    entry = next(
        (entry for entry in parser.entries if entry.applies_to("LourihnaFilms")),
        parser.default_entry,
    )
    if entry is None:
        return True
    parts = urlsplit(url)
    path = parts.path + ("?" + parts.query if parts.query else "")
    matches = []
    for rule in entry.rulelines:
        pattern = unquote(rule.path)
        anchored = pattern.endswith("$")
        pattern = pattern[:-1] if anchored else pattern
        expression = (
            "^" + re.escape(pattern).replace(r"\*", ".*") + ("$" if anchored else "")
        )
        if re.search(expression, path):
            matches.append((len(pattern.replace("*", "")), rule.allowance))
    return max(matches)[1] if matches else True
