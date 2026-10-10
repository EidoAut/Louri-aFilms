import asyncio
from pathlib import Path
import httpx
import pytest
from teleputin.core.exceptions import ServiceError
from teleputin.core.public_http import PublicPageReader, PublicPageError, robots_allow
from teleputin.models.okru_identity import OKRuIdentity, video_id_from_url
from teleputin.providers.result_normalization import normalize_results
from teleputin.providers.public_metadata import PublicMetadata
from teleputin.providers.direct_search import DirectPublicSearch
from teleputin.providers.okru import OKRuProvider
from teleputin.services.metadata_service import MetadataService
from teleputin.services.candidate_service import CandidateService
from teleputin.services.playback_service import resolve_okru
from teleputin.database.engine import create_database
from teleputin.database.repositories import Repository

HTML = '<meta property="og:type" content="video.other"><meta property="og:url" content="https://ok.ru/video/123"><meta property="og:title" content="Public title"><meta property="video:duration" content="120">'

@pytest.fixture
def repo(tmp_path, monkeypatch):
    monkeypatch.setattr("teleputin.core.public_http.REQUEST_DELAY", 0)
    engine = create_database(tmp_path / "test.db")
    yield Repository(engine)
    engine.dispose()


def test_identity_rejects_bad_urls_and_playback_ignores_stored_embed():
    for value in [None, "https://ok.ru.evil.test/video/123", "https://user@ok.ru/video/123", "https://ok.ru:bad/video/123", "file:///video/123"]:
        assert video_id_from_url(value) is None
    item = resolve_okru({"kind": "video", "provider": "okru", "id": "wrong", "original_url": "http://m.ok.ru/video/123", "embed_url": "https://evil.test/stream.m3u8"})
    assert item["embed_url"] == "https://ok.ru/videoembed/123" and item["id"] == "123"
    with pytest.raises(ServiceError): OKRuIdentity("1/script")


def test_normalization_merges_duplicate_metadata_and_skips_malformed_rows():
    rows = [None, {"url": 12}, {"url": "https://ok.ru/video/123", "title": "A &amp; B", "thumbnail": 12, "duration_seconds": True}, {"url": "https://ok.ru/videoembed/123", "description": "<b>Description</b>", "duration_seconds": 5400, "thumbnail": {"src": "https://example.com/thumb.jpg"}}, {"url": "https://ok.ru/video/456", "title": ["bad"], "thumbnail": {"src": "https://host:bad/image"}}]
    videos = normalize_results(rows)
    assert len(videos) == 2
    assert videos[0].title == "A & B" and videos[0].duration_seconds == 5400
    assert videos[0].description == "Description" and videos[0].thumbnail_url
    assert videos[0].is_embeddable is None
    assert videos[1].title == "OK.ru video 456" and videos[1].thumbnail_url is None


@pytest.mark.parametrize("status", [302, 401, 403, 429, 500])
async def test_transport_stops_batch_on_access_error(repo, status):
    calls = []
    def handler(request):
        calls.append(request.url.path)
        return httpx.Response(200, text="User-agent: *\nAllow: /") if request.url.path == "/robots.txt" else httpx.Response(status)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        reader = PublicPageReader(client)
        with pytest.raises(PublicPageError): await reader.read("https://ok.ru/video/123")
        with pytest.raises(PublicPageError): await reader.read("https://ok.ru/video/456")
    assert calls == ["/robots.txt", "/video/123"]


async def test_missing_video_does_not_block_next_video(repo):
    def handler(request):
        if request.url.path == "/robots.txt": return httpx.Response(200, text="User-agent: *\nAllow: /")
        return httpx.Response(404) if request.url.path == "/video/999" else httpx.Response(200, text=HTML)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        reader = PublicMetadata(client)
        assert await reader.fetch("999") == {} and not reader.blocked
        assert (await reader.fetch("123"))["title"] == "Public title"


async def test_challenge_and_response_limit(repo):
    for document in ["<html>Verify you are human</html>", "x" * 101]:
        def handler(request):
            return httpx.Response(200, text="User-agent: *\nAllow: /" if request.url.path == "/robots.txt" else document)
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            reader = PublicPageReader(client)
            with pytest.raises(PublicPageError): await reader.read("https://ok.ru/video/123", limit=100)
            assert reader.blocked


async def test_search_and_metadata_share_robots_and_preserve_fallback_provenance(repo):
    class Fallback:
        more = False
        async def search(self, *args): return [{"url": "https://ok.ru/video/123", "title": "External result"}]
    calls = []
    def handler(request):
        calls.append(request.url.path)
        if request.url.path == "/robots.txt": return httpx.Response(200, text="User-agent: *\nAllow: /")
        return httpx.Response(200, text="No readable search markup" if request.url.path == "/video/search" else HTML)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        reader = PublicPageReader(client)
        provider = OKRuProvider(DirectPublicSearch(client, Fallback(), reader))
        rows = await provider.search("Film")
        assert rows[0].source_name == "External web search"
        assert (await PublicMetadata(client, reader).fetch("123"))["title"] == "Public title"
    assert calls.count("/robots.txt") == 1


async def test_enrichment_is_pure_uses_cache_and_preserves_existing_metadata(repo):
    calls = []
    def handler(request):
        calls.append(request.url.path)
        return httpx.Response(200, text="User-agent: *\nAllow: /" if request.url.path == "/robots.txt" else HTML)
    card = (await OKRuProvider(None).get_video("123")).card()
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        service = MetadataService(repo, PublicMetadata(client))
        result = await service.enrich([card])
        assert result[0]["title"] == "Public title"
        assert card["title"] == "OK.ru video 123" and repo.library() == []
        await service.enrich([card])
    assert calls == ["/robots.txt", "/video/123"]
    repo.cache_put("metadata:123", "123", "okru-public-html", {"title": "Saved title"}, ttl=-1)
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(403))) as client:
        service = MetadataService(repo, PublicMetadata(client))
        result = await service.enrich([card])
        assert result[0]["title"] == "Saved title"
        assert "stale" in result[0]["metadata_status"] and "cached" in service.notice


async def test_candidate_metadata_failure_never_replaces_search_title_with_placeholder(repo):
    class Search:
        async def search(self, *args, **kwargs):
            return {"items": [{"kind": "video", "provider": "okru", "id": "123", "key": "okru:123", "title": "Film 1973", "original_url": "https://ok.ru/video/123", "duration_seconds": 5400}], "more": False}
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(403))) as client:
        result = await CandidateService(Search(), repo, client).find({"title": "Film", "year": "1973"})
    assert result["items"][0]["title"] == "Film 1973"
    assert repo.library()[0]["title"] == "Film 1973"
    assert result["items"][0]["duration_seconds"] == 5400


def test_runtime_has_no_catalog_dependency():
    root = Path(__file__).resolve().parents[1] / "teleputin"
    for relative in ["providers/rarefilmm.py", "services/catalog_service.py"]:
        assert not (root / relative).exists()
    for path in (root / "ui").rglob("*.qml"):
        assert "RareFilmm" not in path.read_text(encoding="utf-8")
    controller = (root / "controllers/application_controller.py").read_text(encoding="utf-8")
    assert "rarefilmm.com" not in controller and "RareFilmmProvider" not in controller


async def test_shared_transport_paces_concurrent_page_requests(repo, monkeypatch):
    monkeypatch.setattr("teleputin.core.public_http.REQUEST_DELAY", 0.03)
    times = []
    def handler(request):
        if request.url.path == "/robots.txt": return httpx.Response(200, text="User-agent: *\nAllow: /")
        times.append(asyncio.get_running_loop().time())
        return httpx.Response(200, text="page")
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        reader = PublicPageReader(client)
        await asyncio.gather(reader.read("https://ok.ru/video/123"), reader.read("https://ok.ru/video/456"))
    assert times[1] - times[0] >= 0.025


def test_robots_rules_cover_search_query():
    from urllib.robotparser import RobotFileParser
    parser = RobotFileParser()
    parser.parse(["User-agent: *", "Disallow: /video/search?*private*", "Allow: /video/search?public$"])
    assert not robots_allow(parser, "https://ok.ru/video/search?q=private")
    assert robots_allow(parser, "https://ok.ru/video/search?public")
