# ==========================================================================
"""test_providers.py
Verify providers contracts using isolated fixtures.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

import httpx
import pytest

from lourihna_films.core.exceptions import ServiceError
from lourihna_films.providers.okru import (
    OKRuProvider,
    normalize_title,
    video_id_from_url,
)
from lourihna_films.providers.web_search import BraveSearch
from lourihna_films.services.tmdb_service import TMDBService


@pytest.mark.parametrize(
    "url",
    [
        "https://ok.ru.evil.com/video/123",
        "https://evil.com/video/123",
        "https://ok.ru@evil.com/video/123",
        "https://user@ok.ru/video/123",
        "file:///video/123",
        "https://ok.ru/video/123/other",
        "https://ok.ru/video/-1",
        "https://ok.ru/video/１２３",
        "https://ok.ru:123/video/123",
        "https://ok.ru/video/1%2f2",
        "https://ok.ru/live/123",
    ],
)
def test_reject_unsupported_urls(url):
    assert video_id_from_url(url) is None


@pytest.mark.parametrize(
    "url",
    [
        "https://ok.ru/video/123?fromTime=5",
        "https://www.ok.ru/videoembed/123",
        "http://m.ok.ru/video/123/",
    ],
)
def test_canonical_ids(url):
    assert video_id_from_url(url) == "123"


async def test_direct_url_without_credentials():
    async with httpx.AsyncClient() as client:
        provider = OKRuProvider(BraveSearch(client, ""))
        (video,) = await provider.search("https://ok.ru/video/123")
        assert video.embed_url == "https://ok.ru/videoembed/123"
        assert video.is_embeddable is None
        with pytest.raises(ServiceError, match="API key"):
            await provider.search("cinema")


async def test_search_deduplicates_and_retains_unknown_availability():
    def handler(request):
        assert request.url.params["offset"] == "1"
        assert request.headers["X-Subscription-Token"] == "test"
        return httpx.Response(
            200,
            json={
                "query": {"more_results_available": True},
                "web": {
                    "results": [
                        {
                            "url": "https://ok.ru/video/12",
                            "title": "  <b>Кино</b> &amp; Cinema ",
                        },
                        {"url": "https://ok.ru/videoembed/12"},
                        {"url": "https://evil.com/video/44"},
                    ]
                },
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = OKRuProvider(BraveSearch(client, "test"))
        rows = await provider.search("movie", 2)
        assert len(rows) == 1 and rows[0].title == "Кино & Cinema"
        assert rows[0].is_embeddable is None and provider.more


async def test_rate_limit_long_retry_is_respected():
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(429, headers={"Retry-After": "60"})
        )
    ) as client:
        with pytest.raises(ServiceError, match="rate limited"):
            await BraveSearch(client, "test").search("film")


async def test_auth_failure_does_not_expose_secret():
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(401))
    ) as client:
        with pytest.raises(ServiceError) as error:
            await TMDBService(client, key="secret-value").popular_movies()
        assert "secret-value" not in str(error.value)


async def test_tmdb_details_alternatives_seasons_and_related():
    def handler(request):
        assert request.headers["Authorization"] == "Bearer test"
        assert request.url.path == "/3/tv/42"
        return httpx.Response(
            200,
            json={
                "id": 42,
                "name": "Example",
                "first_air_date": "2024-01-01",
                "genres": [{"name": "Drama"}],
                "seasons": [{"season_number": 1}],
                "alternative_titles": {"results": [{"title": "Other title"}]},
                "recommendations": {"results": [{"id": 43, "name": "Related"}]},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        item = await TMDBService(client, token="test").details(42, "tv")
        assert item["alternatives"] == ["Other title"] and item["year"] == "2024"
        assert item["related"][0]["kind"] == "tv"
        assert item["seasons"][0]["season_number"] == 1


def test_title_normalization():
    assert normalize_title("  Ｃｉｎｅｍａ  &amp;  Кино ") == "Cinema & Кино"
