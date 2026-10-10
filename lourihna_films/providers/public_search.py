# ==========================================================================
"""public_search.py
Best-effort public web discovery without credentials.

This is NOT an OK.ru API. Results depend on a public search page being accessible;
no authentication, CAPTCHA handling or access-control bypass is attempted.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from lourihna_films.providers.public_search import PublicSearch

from html.parser import HTMLParser
from urllib.parse import parse_qs, urlsplit

from lourihna_films.core.exceptions import ServiceError


class _Results(HTMLParser):
    """Own _Results state and its explicit application contracts."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links = []
        self.current = None
        self.depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Process an HTML parser opening-tag callback using the source schema."""
        if tag != "a":
            return
        attributes = dict(attrs)
        if "result__a" in attributes.get("class", "").split():
            self.current = [attributes.get("href", ""), ""]

    def handle_data(self, data: str) -> None:
        """Accumulate text from the current supported HTML element."""
        if self.current is not None:
            self.current[1] += data

    def handle_endtag(self, tag: str) -> None:
        """Close the current parsed HTML element according to the source schema."""
        if tag == "a" and self.current is not None:
            self.links.append(tuple(self.current))
            self.current = None


def target_url(href: str) -> str:
    """Decode public search result redirects; final URL is validated by OKRuProvider."""
    try:
        parsed = urlsplit(href)
    except ValueError:
        return ""
    if parsed.hostname and parsed.hostname in {
        "duckduckgo.com",
        "html.duckduckgo.com",
        "www.duckduckgo.com",
    }:
        return parse_qs(parsed.query).get("uddg", [""])[0]
    return href


class PublicSearch:
    """Public HTML search, best effort. Does not promise global catalog coverage."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client
        self.more = False

    async def search(self, query: str, page: int = 1) -> list[dict[str, Any]]:
        """Query the selected provider or catalog and preserve its pagination contract."""
        self.more = False
        if page != 1:
            return []
        try:
            response = await self.client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": f"site:ok.ru/video/ {query}"},
                headers={"User-Agent": "LourihnaFilms/0.3.0 (public video discovery)"},
                follow_redirects=False,
                timeout=15,
            )
            if response.status_code != 200:
                raise ServiceError(
                    f"Public search is unavailable (HTTP {response.status_code}). Try again later or configure Brave Search."
                )
            if any(
                marker in response.text.lower()
                for marker in ("challenge-form", "anomaly-modal", "captcha")
            ):
                raise ServiceError(
                    "Public OK.ru search requires human verification. Use a public video URL, Internet Archive or Library."
                )
            parser = _Results()
            parser.feed(response.text)
            if not parser.links and "no-results" not in response.text:
                raise ServiceError(
                    "Public OK.ru search is unavailable. Try Internet Archive, Library, or paste a public OK.ru link."
                )
            self.more = False
            return [
                {"url": target_url(url), "title": title, "description": ""}
                for url, title in parser.links
            ]
        except httpx.HTTPError as exc:
            raise ServiceError(
                "Public search could not be reached. Check your connection or configure Brave Search."
            ) from exc
