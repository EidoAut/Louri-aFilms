import httpx
import pytest
from sqlalchemy import text
from teleputin.core.exceptions import ServiceError
from teleputin.database.engine import create_database
from teleputin.database.repositories import Repository
from teleputin.providers.public_metadata import PublicMetadata, parse_public_metadata, duration_seconds
from teleputin.services.library_service import LibraryService, extract_links


@pytest.fixture
def repo(tmp_path):
    engine = create_database(tmp_path / "library.db")
    yield Repository(engine)
    engine.dispose()


HTML = '''<html><head><meta property="og:type" content="video.other">
<meta property="og:url" content="https://ok.ru/video/123">
<meta property="og:title" content="Space &amp; Кино">
<meta property="og:description" content="Public description">
<meta property="og:image" content="https://example.com/poster.jpg">
<meta property="video:duration" content="125"></head></html>'''


def test_opengraph_metadata():
    fields = parse_public_metadata(HTML, "123")
    assert fields == {"title": "Space & Кино", "description": "Public description", "thumbnail_url": "https://example.com/poster.jpg", "duration_seconds": 125}
    assert parse_public_metadata(HTML, "999") == {}
    assert parse_public_metadata('<title>Sign in</title><meta property="og:title" content="Login">', "123") == {}


def test_json_ld_and_invalid_duration():
    fields = parse_public_metadata('''<script type="application/ld+json">{"@graph":[{"@type":"VideoObject","name":"Film","embedUrl":"https://ok.ru/videoembed/123","duration":"PT1H2M3S","thumbnailUrl":["https://example.com/image.jpg"]}]}</script>''', "123")
    assert fields["duration_seconds"] == 3723 and fields["title"] == "Film"
    assert duration_seconds("PT") is None and duration_seconds("unknown") is None


def test_link_import_validates_and_deduplicates():
    ids, ignored = extract_links('https://ok.ru/video/123\n<a href="https://www.ok.ru/videoembed/123">x</a>\nhttps://ok.ru.evil.org/video/1\nhttps://ok.ru/video/456')
    assert ids == ["123", "456"] and ignored == 1
    with pytest.raises(ServiceError): extract_links("no links")
    with pytest.raises(ServiceError): extract_links("\n".join(f"https://ok.ru/video/{i}" for i in range(101)))


async def test_import_cache_offline_library_and_categories(repo):
    calls = []
    def handler(request):
        calls.append(request.url.path)
        return httpx.Response(200, text="User-agent: *\nAllow: /" if request.url.path == "/robots.txt" else HTML)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        service = LibraryService(repo, client)
        result = await service.import_links("https://ok.ru/video/123", "Documentaries")
        assert result["items"][0]["title"] == "Space & Кино"
        assert result["items"][0]["is_embeddable"] is None
        await service.import_links("https://ok.ru/video/123")
        assert calls == ["/robots.txt", "/video/123"]
        repo.organize("okru:123", "My own title", "Space")
        await service.import_links("https://ok.ru/video/123", refresh=True)
    assert repo.library("my own", "Space")[0]["title"] == "My own title"
    repo.clear_history()
    assert len(repo.library()) == 1


@pytest.mark.parametrize("status", [302, 401, 403, 429, 500])
async def test_restricted_pages_saved_without_bypass(repo, status):
    calls = []
    def handler(request):
        calls.append(str(request.url))
        if request.url.path == "/robots.txt": return httpx.Response(200, text="User-agent: *\nAllow: /")
        return httpx.Response(status, headers={"Location": "https://other.example/private"})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await LibraryService(repo, client).import_links("https://ok.ru/video/123\nhttps://ok.ru/video/456")
    assert len(result["items"]) == 2 and len(calls) == 2
    assert all(item["is_embeddable"] is None for item in result["items"])
    assert "Metadata unavailable for 2" in result["notice"]


async def test_robot_restriction_prevents_page_fetch():
    calls = []
    def handler(request):
        calls.append(request.url.path)
        return httpx.Response(200, text="User-agent: *\nDisallow: /video/")
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        assert await PublicMetadata(client).fetch("123") == {}
    assert calls == ["/robots.txt"]


def test_robots_wildcards_and_longest_allow():
    from urllib.robotparser import RobotFileParser
    from teleputin.providers.public_metadata import robots_allow
    parser = RobotFileParser()
    parser.parse(["User-agent: *", "Disallow: /video/*", "Allow: /video/123$"])
    assert robots_allow(parser, "https://ok.ru/video/123")
    assert not robots_allow(parser, "https://ok.ru/video/1234")


def test_v1_upgrade_recovers_cached_videos_and_preserves_favorites(tmp_path):
    from teleputin.database.models import Base, LibraryVideo
    from sqlalchemy import create_engine
    path = tmp_path / "old.db"
    engine = create_engine(f"sqlite:///{path}")
    Base.metadata.create_all(engine, tables=[table for table in Base.metadata.sorted_tables if table.name != "library_videos"])
    with engine.begin() as c: c.execute(text("PRAGMA user_version=1"))
    old = Repository(engine)
    item = {"id": "123", "key": "okru:123", "kind": "video", "provider": "okru", "title": "Recovered", "original_url": "https://ok.ru/video/123"}
    old.toggle_favorite(item)
    old.cache_put("old-cache", "Recovered", "okru", {"items": [item]}, ttl=-1)
    engine.dispose()
    upgraded = create_database(path)
    repo = Repository(upgraded)
    repo.recover_library()
    assert repo.library()[0]["title"] == "Recovered"
    assert len(repo.favorites()) == 1
    repo.recover_library()
    assert len(repo.library()) == 1
    with upgraded.connect() as c: assert c.execute(text("PRAGMA user_version")).scalar() == 2
    upgraded.dispose()
