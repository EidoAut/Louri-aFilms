# ==========================================================================
"""test_discovery.py
Verify discovery contracts using isolated fixtures.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

import httpx
import pytest

from lourihna_films.core.exceptions import ServiceError
from lourihna_films.database.engine import create_database
from lourihna_films.database.repositories import Repository
from lourihna_films.providers.archive import ArchiveProvider, archive_id_from_url
from lourihna_films.providers.public_search import PublicSearch, target_url
from lourihna_films.services.discovery_service import DiscoveryService
from lourihna_films.services.search_service import SearchService


@pytest.fixture
def repo(tmp_path):
    engine = create_database(tmp_path / "discovery.db")
    yield Repository(engine)
    engine.dispose()


@pytest.mark.parametrize(
    "url",
    [
        "https://archive.org.evil.test/details/a",
        "https://user@archive.org/details/a",
        "https://archive.org:444/details/a",
        "https://archive.org/details/../admin",
        "https://archive.org/details/a%2fb",
        "file:///details/a",
    ],
)
def test_archive_rejects_unsupported_urls(url):
    assert archive_id_from_url(url) is None


async def test_archive_search_uses_official_api_and_preserves_unknown_playback():
    def handler(request):
        assert request.url.path == "/advancedsearch.php"
        assert "mediatype:movies" in request.url.params["q"]
        assert "NOT access-restricted-item:true" in request.url.params["q"]
        assert "collection:secret" not in request.url.params["q"]
        return httpx.Response(
            200,
            json={
                "response": {
                    "numFound": 21,
                    "docs": [
                        {
                            "identifier": "public-film",
                            "title": "<b>Public</b> Film",
                            "description": ["One", "Two"],
                        },
                        {"identifier": "restricted", "access-restricted-item": "true"},
                        {"identifier": "../evil"},
                    ],
                }
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = ArchiveProvider(client)
        result = await provider.search("collection:secret")
        assert len(result) == 1 and provider.more
        assert result[0].title == "Public Film"
        assert result[0].is_embeddable is None
        assert result[0].embed_url == "https://archive.org/embed/public-film"


@pytest.mark.parametrize(
    "metadata",
    [
        {"mediatype": "movies", "access-restricted-item": "true"},
        {"mediatype": "texts"},
        {},
    ],
)
async def test_archive_restricted_or_nonvideo_cannot_play(metadata):
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(200, json={"metadata": metadata})
        )
    ) as client:
        with pytest.raises(ServiceError):
            await ArchiveProvider(client).get_embed_url("item")


async def test_archive_metadata_duration_and_library(repo):
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(
                200,
                json={
                    "metadata": {"mediatype": "movies", "title": "Film"},
                    "files": [{"length": "123.4"}],
                },
            )
        )
    ) as client:
        video = await ArchiveProvider(client).get_video("film")
        assert video.duration_seconds == 123
        repo.save_videos([video.card()], "Movies")
        repo.organize("archive:film", "My title", "Classics")
        repo.save_videos([video.card()])
        assert repo.library()[0]["title"] == "My title"
        assert repo.library()[0]["category"] == "Classics"
        repo.toggle_favorite(repo.library()[0])
        repo.record_open(video.card())
        assert repo.favorites()[0]["provider"] == "archive"
        assert repo.history()[0]["provider"] == "archive"


async def test_challenge_is_error_not_empty_results():
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(
                200, text='<form id="challenge-form">Verify you are human</form>'
            )
        )
    ) as client:
        with pytest.raises(ServiceError, match="verification"):
            await PublicSearch(client).search("film")


async def test_public_search_does_not_guess_pagination():
    def handler(request):
        raise AssertionError("No invented page request")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        search = PublicSearch(client)
        assert await search.search("film", 2) == []
        assert search.more is False


def test_redirect_only_decodes_exact_search_host():
    assert target_url(
        "https://evilduckduckgo.com/?uddg=https%3A%2F%2Fok.ru%2Fvideo%2F1"
    ).startswith("https://evilduckduckgo.com")
    assert (
        target_url("//duckduckgo.com/l/?uddg=https%3A%2F%2Fok.ru%2Fvideo%2F1")
        == "https://ok.ru/video/1"
    )


async def test_partial_discovery_uses_cache_without_search_history(repo):
    def handler(request):
        return httpx.Response(
            200,
            json={
                "response": {
                    "numFound": 1,
                    "docs": [{"identifier": "film", "title": "A film"}],
                }
            },
        )

    class Offline:
        async def search(self, query, page):
            raise ServiceError("OK.ru search offline")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        search = SearchService(
            {"archive": ArchiveProvider(client), "okru": Offline()}, repo
        )
        result = await DiscoveryService(search, repo).load("Movies")
        assert result["rows"][0]["items"][0]["id"] == "film"
        assert result["notice"] == "OK.ru search offline"
        assert repo.recent_searches() == []
        repo.cache_put(
            "collection-v2:Movies:1", "", "archive", result["rows"][0], ttl=-1
        )
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda r: httpx.Response(503))
    ) as client:
        search = SearchService(
            {"archive": ArchiveProvider(client), "okru": Offline()}, repo
        )
        offline = await DiscoveryService(search, repo).load("Movies")
        assert offline["rows"] == result["rows"]
        assert "Internet Archive" in offline["notice"]


async def test_backend_cache_isolation_and_automatic_queries(repo):
    class Provider:
        more = False
        cache_namespace = "one"

        async def search(self, query, page):
            return []

    provider = Provider()
    service = SearchService({"okru": provider}, repo)
    await service.search("movie", remember=False)
    assert repo.recent_searches() == []
    provider.cache_namespace = "two"

    async def fail(query, page):
        raise ServiceError("different provider")

    provider.search = fail
    with pytest.raises(ServiceError):
        await service.search("movie")


async def test_discovery_pages_preserve_independent_collection_end_flags(repo):
    requests = []

    def handler(request):
        number = int(request.url.params["page"])
        query = request.url.params["q"]
        requests.append((number, query))
        total = 40 if "feature_films" in query else 1
        return httpx.Response(
            200,
            json={
                "response": {
                    "numFound": total,
                    "docs": [{"identifier": f"film{number}", "title": "Film"}],
                }
            },
        )

    class Empty:
        more = False

        async def search(self, query, page):
            return []

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        service = DiscoveryService(
            SearchService({"archive": ArchiveProvider(client), "okru": Empty()}, repo),
            repo,
        )
        first = await service.load("Explore")
        assert first["active"] == ["Movies"]
        second = await service.load("Explore", 2, first["active"])
        assert second["active"] == []
        assert len(requests) == 5
        assert requests[-1][0] == 2
        assert second["rows"][0]["items"][0]["id"] == "film2"
        assert repo.recent_searches() == []


async def test_discovery_deadline_keeps_fast_results_and_cancels_slow_source(
    repo, monkeypatch
):
    import asyncio

    monkeypatch.setattr(
        "lourihna_films.services.discovery_service.DISCOVERY_SOURCE_TIMEOUT", 0.05
    )
    cancelled = asyncio.Event()

    class Stalled:
        more = False

        async def search(self, query, page):
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()

    def handler(request):
        return httpx.Response(
            200,
            json={
                "response": {
                    "numFound": 1,
                    "docs": [{"identifier": "ready", "title": "Ready"}],
                }
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        service = DiscoveryService(
            SearchService(
                {"archive": ArchiveProvider(client), "okru": Stalled()}, repo
            ),
            repo,
        )
        result = await asyncio.wait_for(service.load("Movies"), timeout=1)
    assert cancelled.is_set()
    assert result["rows"][0]["items"][0]["id"] == "ready"
    assert "timed out" in result["notice"]
    assert result["number"] == 0
    assert "okru" in result["active"]
