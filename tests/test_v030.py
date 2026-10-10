# ==========================================================================
"""test_v030.py
Verify v030 contracts using isolated fixtures.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from lourihna_films.core.exceptions import ServiceError
from lourihna_films.database.engine import create_database
from lourihna_films.database.models import SearchCache, WatchHistory
from lourihna_films.database.repositories import Repository
from lourihna_films.providers.direct_search import DirectPublicSearch, PublicVideoCards
from lourihna_films.providers.okru import OKRuProvider
from lourihna_films.services.artwork_cache import ArtworkCache
from lourihna_films.services.candidate_service import CandidateService, queries, rank
from lourihna_films.services.tmdb_service import TMDBService


@pytest.fixture
def repo(tmp_path):
    engine = create_database(tmp_path / "test.db")
    yield Repository(engine)
    engine.dispose()


async def test_tmdb_cache_language_isolation_and_no_secret(repo):
    calls = []

    def handler(request):
        calls.append(request)
        assert request.url.params["api_key"] == "private-key"
        return httpx.Response(
            200, json={"results": [{"id": 1, "title": request.url.params["language"]}]}
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        service = TMDBService(client, key="private-key", repository=repo)
        assert (await service.popular_movies())[0]["title"] == "en-US"
        await service.popular_movies()
        service.language = "es-ES"
        assert (await service.popular_movies())[0]["title"] == "es-ES"
    assert len(calls) == 2
    with Session(repo.engine) as session:
        for row in session.scalars(select(SearchCache)):
            assert "private-key" not in str([row.key, row.query, row.results])


async def test_tmdb_offline_uses_stale_metadata(repo):
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(
                200, json={"results": [{"id": 1, "title": "Saved film"}]}
            )
        )
    ) as client:
        await TMDBService(client, key="key", repository=repo).popular_movies()
    repo.expire_discovery()
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda r: httpx.Response(404))
    ) as client:
        service = TMDBService(client, key="key", repository=repo)
        assert (await service.popular_movies())[0]["title"] == "Saved film"
        assert "cached" in service.notice


async def test_tmdb_original_title_directors_and_local_artwork(repo, tmp_path):
    def handler(request):
        if request.url.host == "image.tmdb.org":
            return httpx.Response(
                200, content=b"image-bytes", headers={"content-type": "image/jpeg"}
            )
        return httpx.Response(
            200,
            json={
                "id": 1,
                "title": "Localized",
                "original_title": "Original",
                "poster_path": "/poster.jpg",
                "credits": {"crew": [{"job": "Director", "name": "Director"}]},
                "alternative_titles": {"titles": [{"title": "Alternative"}]},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        card = await TMDBService(
            client, key="key", repository=repo, artwork=ArtworkCache(tmp_path / "art")
        ).details(1, "movie")
        assert card["original_title"] == "Original" and card["directors"] == [
            "Director"
        ]
        assert card["alternatives"] == ["Alternative"]
        assert card["poster"].startswith("file:///")


async def test_artwork_reuses_disk_and_rejects_other_hosts(tmp_path):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(
            200, content=b"image", headers={"content-type": "image/png"}
        )

    cache = ArtworkCache(tmp_path)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        assert await cache.get(client, "https://evil.test/image") == ""
        first = await cache.get(client, "https://image.tmdb.org/t/p/w500/a.png")
        assert first == await cache.get(client, "https://image.tmdb.org/t/p/w500/a.png")
    assert len(calls) == 1
    assert len(list(tmp_path.glob("*.img"))) == 1


async def test_artwork_redirect_and_size_limits(tmp_path, monkeypatch):
    monkeypatch.setattr("lourihna_films.services.artwork_cache.ARTWORK_MAX_BYTES", 4)
    cache = ArtworkCache(tmp_path)
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(
                200, content=b"too-large", headers={"content-type": "image/png"}
            )
        )
    ) as client:
        await cache.get(client, "https://image.tmdb.org/t/p/w500/a.png")
    assert not list(tmp_path.glob("*.img"))
    calls = []

    def redirect(request):
        calls.append(request)
        return httpx.Response(302, headers={"location": "https://evil.test"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(redirect)) as client:
        await cache.get(client, "https://image.tmdb.org/t/p/w500/a.png")
    assert len(calls) == 1


def test_queries_bounded_original_alternatives_year_director():
    result = queries(
        {
            "title": "Film",
            "original_title": "Original",
            "alternatives": ["Other", "More", "Film"],
            "year": "2020",
            "directors": ["Director"],
        }
    )
    assert result == ["Film 2020", "Film 2020 Director", "Original 2020", "Other 2020"]


def test_ranking_deduplicates_and_prefers_runtime_over_trailers():
    catalog = {"title": "A Film", "year": "2020", "runtime": 100, "kind": "movie"}
    candidates = [
        {"key": "okru:1", "title": "A Film 2020 Trailer", "duration_seconds": 120},
        {"key": "okru:2", "title": "A Film 2020", "duration_seconds": 5990},
        {"key": "okru:2", "title": "A Film 2020"},
        {"key": "okru:3", "title": "Unrelated"},
    ]
    result = rank(candidates, catalog)
    assert len(result) == 3 and result[0]["key"] == "okru:2"
    assert "Similar runtime" in result[0]["match_reason"]
    assert "is_embeddable" not in result[0]


CARD = '<div class="video_search_result_video-card"><div><a href="/video/123"><img class="video-card_img" src="https://iv.okcdn.ru/test.jpg" alt="Film"></a><div class="video-card_duration">1:30:20</div></div><h3><a href="/video/123" data-tsid="video-name">Film 2020</a></h3><div data-tsid="video-description">Public <a>description</a></div></div>'


def test_public_card_parser_uses_visible_html_only():
    parser = PublicVideoCards()
    parser.feed(CARD)
    assert len(parser.rows) == 1
    assert parser.rows[0]["title"] == "Film 2020"
    assert parser.rows[0]["duration_seconds"] == 5420
    assert parser.rows[0]["description"] == "Public description"
    assert parser.rows[0]["url"] == "https://ok.ru/video/123"


async def test_direct_search_obeys_robots_and_uses_fallback():
    class Fallback:
        more = False

        async def search(self, query, page):
            return [{"url": "https://ok.ru/video/456", "title": "Fallback"}]

    calls = []

    def handler(request):
        calls.append(request.url.path)
        return httpx.Response(200, text="User-agent: *\nDisallow: /video/search")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        service = DirectPublicSearch(client, Fallback())
        result = await service.search("film")
        assert result[0]["title"] == "Fallback" and service.blocked
        await service.search("different")
    assert calls == ["/robots.txt"]


async def test_direct_public_results_have_duration_and_no_auth():
    class Fallback:
        async def search(self, *args):
            raise AssertionError("Should use direct search")

    def handler(request):
        assert "Authorization" not in request.headers
        return httpx.Response(
            200,
            text="User-agent: *\nAllow: /"
            if request.url.path == "/robots.txt"
            else CARD,
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = OKRuProvider(DirectPublicSearch(client, Fallback()))
        result = await provider.search("Film")
        assert result[0].duration_seconds == 5420
        assert result[0].is_embeddable is None
        assert provider.more is False


async def test_candidate_challenge_stops_variant_queries(repo):
    class Search:
        calls = 0

        async def search(self, *args, **kwargs):
            self.calls += 1
            raise ServiceError("Human verification required")

    search = Search()
    result = await CandidateService(search, repo, None).find(
        {"title": "A", "original_title": "B"}
    )
    assert search.calls == 1 and result["items"] == []
    assert "verification" in result["notice"]


def test_continue_watching_is_explicit_and_never_fabricates_position(repo):
    video = {
        "provider": "okru",
        "id": "1",
        "key": "okru:1",
        "title": "Film",
        "kind": "video",
    }
    repo.record_open(video)
    assert repo.continuing() == []
    repo.keep_watching("okru", "1", True)
    repo.record_open(video)
    assert len(repo.continuing()) == 1
    with Session(repo.engine) as session:
        assert session.scalar(select(WatchHistory)).position is None
    repo.keep_watching("okru", "1", False)
    assert repo.continuing() == []


def test_environment_key_overrides_saved_token(monkeypatch):
    from lourihna_films.core.config import credentials

    monkeypatch.delenv("TMDB_TOKEN", raising=False)
    monkeypatch.setenv("TMDB_API_KEY", "environment-key")
    values = credentials({"tmdb_token": "saved-token"})
    assert values["tmdb_key"] == "environment-key" and values["tmdb_token"] == ""


def test_organizing_video_preserves_continue_watching(repo):
    item = {
        "provider": "okru",
        "id": "2",
        "key": "okru:2",
        "kind": "video",
        "title": "Film",
        "original_url": "https://ok.ru/video/2",
    }
    repo.save_videos([item])
    repo.record_open(item)
    repo.keep_watching("okru", "2", True)
    repo.organize("okru:2", "Personal title", "Classics")
    assert repo.continuing()[0]["title"] == "Personal title"
    assert repo.continuing()[0]["category"] == "Classics"
