# ==========================================================================
"""test_controller.py
Verify controller contracts using isolated fixtures.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QCoreApplication

from lourihna_films.controllers.application_controller import ApplicationController
from lourihna_films.database.engine import create_database
from lourihna_films.database.repositories import Repository


@pytest.fixture
def controller(tmp_path, monkeypatch):
    async def offline_metadata(self, video_id):
        return {}

    async def empty_archive(self, query, page=1, collection=None):
        return []

    async def empty_public(self, query, page=1):
        return []

    async def formats(client, url):
        return [{"url": "https://vd296.okcdn.ru/test", "quality": "low"}]

    monkeypatch.setattr(
        "lourihna_films.providers.public_media.resolve_public_formats", formats
    )
    monkeypatch.setattr(
        "lourihna_films.providers.archive.ArchiveProvider.search", empty_archive
    )
    monkeypatch.setattr(
        "lourihna_films.providers.direct_search.DirectPublicSearch.search", empty_public
    )
    monkeypatch.setattr(
        "lourihna_films.providers.public_metadata.PublicMetadata.fetch",
        offline_metadata,
    )
    for name in ("TMDB_TOKEN", "TMDB_API_KEY", "BRAVE_SEARCH_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    app = QCoreApplication.instance() or QCoreApplication([])
    engine = create_database(tmp_path / "controller.db")
    controller = ApplicationController(Repository(engine))
    yield controller, app
    controller.shutdown()
    engine.dispose()


def test_qml_state_updates_only_dependent_bindings(controller):
    """Busy/playback notifications must not re-evaluate catalog model bindings."""
    from PySide6.QtCore import QUrl
    from PySide6.QtQml import QQmlComponent, QQmlEngine

    backend, app = controller
    engine = QQmlEngine()
    engine.rootContext().setContextProperty("backend", backend)
    component = QQmlComponent(engine)
    component.setData(
        b"""import QtQml
        QtObject {
            property int rowChanges: 0
            property int busyChanges: 0
            property var rows: backend.viewState.rows
            property bool busy: backend.viewState.busy
            onRowsChanged: rowChanges++
            onBusyChanged: busyChanges++
        }""",
        QUrl(),
    )
    observer = component.create()
    assert observer is not None, component.errors()
    backend.update(rows=[{"title": "Catalog", "items": [{"key": "movie:1"}]}])
    count = observer.property("rowChanges")
    backend.update(busy=True, playbackPhase="loading")
    app.processEvents()
    assert observer.property("busy") is True
    assert observer.property("rowChanges") == count
    backend.update(rows=[{"title": "Series", "items": []}])
    assert observer.property("rowChanges") == count + 1
    backend.update(rows=[{"title": "Series", "items": []}], busy=True)
    assert observer.property("rowChanges") == count + 1
    assert observer.property("busyChanges") == 1
    observer.deleteLater()
    app.processEvents()


def test_direct_url_completes_via_qt_signal(controller):
    controller, app = controller
    controller.search("https://ok.ru/video/123", "OK.ru")
    deadline = time.monotonic() + 15
    while controller.state["busy"] and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    assert not controller.state["busy"]
    assert controller.state["results"][0]["id"] == "123"
    controller.play(controller.state["results"][0])
    assert controller.state["player"]["embed_url"] == "https://ok.ru/videoembed/123"
    controller.navigate("My List")
    assert controller.state["player"] == {}


def test_obsolete_response_does_not_overwrite_navigation(controller):
    controller, app = controller
    controller.generations["details"] = 4
    controller.update(details={"title": "Current"})
    controller._receive("details", 3, {"title": "Stale"}, "")
    assert controller.state["details"]["title"] == "Current"


def test_failed_load_more_can_retry_same_page(controller):
    controller, app = controller
    controller.generations["search"] = 1
    controller.update(searchPage=2, results=[{"id": "123"}], more=True)
    controller._receive("search", 1, None, "Network unavailable")
    assert controller.state["searchPage"] == 1
    assert controller.state["more"] is True
    assert controller.state["results"] == [{"id": "123"}]


def test_catalog_requires_tmdb_but_explore_remains_available(controller, monkeypatch):
    controller, app = controller
    calls = []

    async def discover(self, page, on_row=None):
        calls.append(page)
        return {"rows": [], "notice": "Public source offline"}

    monkeypatch.setattr(
        "lourihna_films.services.discovery_service.DiscoveryService.load", discover
    )
    for page in ("Home", "Movies", "Series", "Documentaries"):
        controller.navigate(page)
        assert not controller.state["busy"]
        assert controller.state["rows"] == []
        assert controller.state["tmdbAvailable"] is False
    controller.navigate("Explore")
    wait_for_result(controller, app)
    assert calls == ["Explore"]
    assert "Algunas fuentes" in controller.state["message"]
    assert controller.repo.recent_searches() == []


def test_import_populates_home_and_local_search(controller):
    controller, app = controller
    controller.importLinks("https://ok.ru/video/123", "Documentaries")
    deadline = time.monotonic() + 15
    while controller.state["busy"] and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    assert len(controller.state["results"]) == 1
    controller.organize("okru:123", "Space documentary", "Documentaries")
    controller.navigate("Explore")
    assert controller.state["rows"][0]["items"][0]["title"] == "Space documentary"
    controller.search("Space", "Library")
    deadline = time.monotonic() + 15
    while controller.state["busy"] and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    assert controller.state["results"][0]["id"] == "123"


def test_utf8_file_import_and_invalid_file(controller, tmp_path):
    controller, app = controller
    file = tmp_path / "links.txt"
    file.write_text(
        "\ufeffPublic links\nhttps://ok.ru/video/123\nhttps://ok.ru/video/456",
        encoding="utf-8",
    )
    controller.importFile(file.as_uri(), "Concerts")
    deadline = time.monotonic() + 15
    while controller.state["busy"] and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    assert len(controller.repo.library(category="Concerts")) == 2
    controller.importFile("https://example.com/links.txt", "General")
    assert "1 MB" in controller.state["message"]


def wait_for_result(controller, app):
    deadline = time.monotonic() + 15
    while controller.state["busy"] and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    assert not controller.state["busy"]


def test_archive_player_validates_metadata_and_returns_to_search(
    controller, monkeypatch
):
    from lourihna_films.models.video import VideoResult

    controller, app = controller
    calls = []

    async def metadata(self, identifier):
        calls.append(identifier)
        return VideoResult(
            id=identifier,
            provider="archive",
            title="Film",
            original_url="https://archive.org/details/film",
            embed_url="https://archive.org/embed/film",
        )

    monkeypatch.setattr(
        "lourihna_films.providers.archive.ArchiveProvider.get_video", metadata
    )
    controller.update(page="Search", query="Film", results=[{"key": "archive:film"}])
    controller.play(
        {
            "kind": "video",
            "provider": "archive",
            "original_url": "https://archive.org/details/film",
            "embed_url": "https://evil.test",
        }
    )
    wait_for_result(controller, app)
    assert calls == ["film"]
    assert controller.state["player"]["embed_url"] == "https://archive.org/embed/film"
    controller.backFromPlayer()
    assert controller.state["page"] == "Search"
    assert controller.state["query"] == "Film"
    assert controller.state["player"] == {}
    assert controller.state["results"] == [{"key": "archive:film"}]


def test_restricted_archive_does_not_record_player_history(controller, monkeypatch):
    from lourihna_films.core.exceptions import ServiceError

    controller, app = controller

    async def denied(self, identifier):
        raise ServiceError("Restricted item")

    monkeypatch.setattr(
        "lourihna_films.providers.archive.ArchiveProvider.get_video", denied
    )
    controller.play(
        {
            "kind": "video",
            "provider": "archive",
            "original_url": "https://archive.org/details/film",
        }
    )
    wait_for_result(controller, app)
    assert controller.state["player"] == {}
    assert controller.repo.history() == []
    assert "No se pudo" in controller.state["message"]


def test_tmdb_is_primary_home_source(controller, monkeypatch):
    controller, app = controller
    controller.config["tmdb_key"] = "test"
    controller.update(tmdbAvailable=True)
    calls = []

    async def catalog(self, path, kind="movie", **params):
        calls.append(path)
        return [{"id": 1, "key": kind + ":1", "kind": kind, "title": "Catalog title"}]

    async def fail(*args):
        raise AssertionError("Home must not query public videos")

    monkeypatch.setattr(
        "lourihna_films.services.tmdb_service.TMDBService.listing", catalog
    )
    monkeypatch.setattr(
        "lourihna_films.services.discovery_service.DiscoveryService.load", fail
    )
    controller.navigate("Home")
    wait_for_result(controller, app)
    assert len(controller.state["rows"]) == 5
    assert "trending/movie/week" in calls
    assert all(
        row["items"][0]["kind"] in ("movie", "tv") for row in controller.state["rows"]
    )


def test_federated_search_keeps_working_source(controller, monkeypatch):
    from lourihna_films.core.exceptions import ServiceError
    from lourihna_films.models.video import VideoResult

    controller, app = controller

    async def broken(self, query, page=1):
        raise ServiceError("OK.ru offline")

    async def archive(self, query, page=1, collection=None):
        return [
            VideoResult(
                id="film",
                provider="archive",
                title="Film",
                original_url="https://archive.org/details/film",
            )
        ]

    monkeypatch.setattr(
        "lourihna_films.providers.direct_search.DirectPublicSearch.search", broken
    )
    monkeypatch.setattr(
        "lourihna_films.providers.archive.ArchiveProvider.search", archive
    )
    controller.search("Film", "Discover")
    wait_for_result(controller, app)
    assert controller.state["results"][0]["provider"] == "archive"
    assert "Algunas fuentes" in controller.state["message"]


def test_catalog_selection_searches_candidates_without_autoplay(
    controller, monkeypatch
):
    controller, app = controller
    controller.update(tmdbAvailable=True)
    catalog = {"kind": "movie", "id": 7, "key": "movie:7", "title": "Film"}

    async def details(self, identifier, kind):
        return catalog

    async def candidates(self, item):
        assert item == catalog
        return {"items": [{"key": "okru:1", "title": "Candidate"}], "notice": ""}

    monkeypatch.setattr(
        "lourihna_films.services.tmdb_service.TMDBService.details", details
    )
    monkeypatch.setattr(
        "lourihna_films.services.candidate_service.CandidateService.find", candidates
    )
    controller.select(catalog)
    wait_for_result(controller, app)
    assert controller.state["page"] == "Details"
    assert controller.state["candidates"][0]["key"] == "okru:1"
    assert controller.state["player"] == {}


def test_late_candidate_response_cannot_replace_new_screen(controller):
    controller, app = controller
    controller.generations["candidates"] = 2
    controller.update(page="Search", candidates=[])
    controller._receive("candidates", 1, {"items": [{"key": "okru:1"}]}, "")
    assert controller.state["candidates"] == []


def test_settings_accepts_v3_key_and_encrypts_it(controller, monkeypatch):
    from lourihna_films.core.secrets import reveal

    controller, app = controller
    submitted = []
    monkeypatch.setattr(
        controller, "submit", lambda tag, operation: submitted.append(tag)
    )
    key = "a" * 32
    controller.saveSettings(key, "", "es-ES")
    saved = controller.repo.settings()
    assert saved["tmdb_key"] != key and reveal(saved["tmdb_key"]) == key
    assert saved["tmdb_token"] == ""
    assert controller.config["tmdb_key"] == key
    assert controller.state["tmdbAvailable"] is True
    assert submitted == ["settings"]


def test_legacy_catalog_favorite_does_not_contact_former_catalog(
    controller, monkeypatch
):
    controller, app = controller

    def submit(*args):
        raise AssertionError("Legacy entry must not trigger a catalog request")

    monkeypatch.setattr(controller, "submit", submit)
    entry = {
        "kind": "catalog",
        "key": "rarefilmm:old",
        "title": "Old saved title",
        "source_entry": {"source_url": "https://rarefilmm.com/2020/01/old/"},
    }
    controller.favorite(entry)
    controller.select(entry)
    assert controller.state["details"]["title"] == entry["title"]
    assert controller.state["favorites"][0]["key"] == entry["key"]
    assert "no longer" in controller.state["message"]


def test_playback_rejects_known_embed_denial(controller):
    controller, app = controller
    controller.play(
        {
            "kind": "video",
            "provider": "okru",
            "original_url": "https://ok.ru/video/123",
            "is_embeddable": False,
        }
    )
    assert not controller.state["player"]
    assert "Embedding is unavailable" in controller.state["message"]


def test_official_embed_browser_fallback_uses_existing_validated_opener(
    controller, monkeypatch
):
    controller, app = controller
    opened = []
    monkeypatch.setattr(
        "lourihna_films.controllers.application_controller.QDesktopServices.openUrl",
        lambda url: opened.append(url.toString()) or True,
    )
    controller.openExternal("https://ok.ru/videoembed/4160762481308")
    controller.openExternal("https://ok.ru.evil.test/videoembed/4160762481308")
    assert opened == ["https://ok.ru/videoembed/4160762481308"]


def test_buffered_source_stays_ephemeral_and_cancels_on_exit(controller, monkeypatch):
    controller, app = controller

    async def resolve(client, url):
        assert url == "https://ok.ru/video/123"
        return [
            {"url": "https://vd296.okcdn.ru/video?token=temporary", "quality": "low"}
        ]

    monkeypatch.setattr(
        "lourihna_films.providers.public_media.resolve_public_formats", resolve
    )
    controller.play(
        {
            "kind": "video",
            "provider": "okru",
            "id": "123",
            "key": "okru:123",
            "title": "Fixture",
            "original_url": "https://ok.ru/video/123",
        }
    )
    controller.playBuffered()
    deadline = time.monotonic() + 5
    while controller.state["busy"] and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    assert controller.state["bufferedMedia"]["quality"] == "low"
    assert "temporary" not in str(controller.repo.history())
    controller.navigate("Search")
    assert not controller.state["bufferedMedia"]
    assert not controller.state["player"]


def test_automatic_playback_retries_only_available_sources(controller, monkeypatch):
    controller, app = controller

    async def sources(client, url):
        return [
            {"url": "https://vd296.okcdn.ru/a", "quality": "hd"},
            {"url": "https://vd296.okcdn.ru/b", "quality": "low"},
        ]

    monkeypatch.setattr(
        "lourihna_films.providers.public_media.resolve_public_formats", sources
    )
    item = {
        "kind": "video",
        "provider": "okru",
        "original_url": "https://ok.ru/video/123",
        "title": "Fixture",
    }
    controller.play(item)
    wait_for_result(controller, app)
    assert controller.state["playbackPhase"] == "native"
    session = controller.state["playbackSession"]
    controller.playbackFailed("okru:123", session - 1, 1)
    assert controller.state["bufferedMedia"]["quality"] == "hd"
    controller.playbackFailed("okru:123", session, 1)
    assert controller.state["bufferedMedia"]["quality"] == "low"
    controller.playbackFailed("okru:123", session, 1)
    assert controller.state["playbackPhase"] == "web"
    controller.backFromPlayer()
    controller.playbackFailed("okru:123", session, 1)
    assert controller.state["playbackPhase"] == "idle"
    assert controller.state["bufferedMedia"] == {}


def test_progress_resume_finish_and_stale_session(controller):
    controller, app = controller
    item = {
        "kind": "video",
        "provider": "okru",
        "original_url": "https://ok.ru/video/123",
        "title": "Fixture",
    }
    controller.play(item)
    wait_for_result(controller, app)
    session = controller.state["playbackSession"]
    controller.saveProgress("okru:123", session, 12000, 60000, False)
    controller.saveProgress("okru:123", session - 1, 45000, 60000, False)
    controller.backFromPlayer()
    assert controller.repo.continuing()[0]["position_ms"] == 12000
    controller.play(item)
    wait_for_result(controller, app)
    assert controller.state["player"]["position_ms"] == 12000
    controller.finishPlayback()
    assert not controller.repo.continuing()
    controller.play(item)
    wait_for_result(controller, app)
    assert controller.state["player"]["position_ms"] == 0


def test_volume_and_interface_preferences_are_separate_from_metadata(controller):
    controller, app = controller
    metadata_language = controller.state["language"]
    controller.setVolume(0.35, True)
    controller.savePreferences("gl", False)
    assert controller.repo.settings()["volume"] == "0.35"
    assert controller.repo.settings()["muted"] == "true"
    assert controller.state["language"] == metadata_language
    assert controller.state["uiLanguage"] == "gl"
    assert controller.state["motion"] is False


def test_default_search_prioritizes_okru(controller, monkeypatch):
    controller, app = controller
    calls = []

    async def search(self, query, page=1, provider="okru", remember=True):
        calls.append(provider)
        return {"items": [{"key": provider + ":123", "kind": "video"}], "more": False}

    monkeypatch.setattr(
        "lourihna_films.services.search_service.SearchService.search", search
    )
    controller.search("film")
    wait_for_result(controller, app)
    assert set(calls) == {"okru"}
    assert len(controller.state["results"]) == 1
    assert controller.state["searchMode"] == "All"


def test_manual_quality_selection_retains_full_choice_list(controller):
    controller, app = controller
    sources = [
        {"url": "https://example.test/" + str(i), "quality": str(i)} for i in range(5)
    ]
    controller.update(
        bufferedMedia={**sources[0], "sources": sources, "index": 0},
        player={"key": "okru:1", "provider": "okru"},
        playbackSession=1,
    )
    controller.selectQuality(4)
    assert controller.state["bufferedMedia"]["index"] == 4
    controller.selectQuality(99)
    assert controller.state["bufferedMedia"]["index"] == 4
    controller.selectQuality(0)
    for _ in range(3):
        controller.playbackFailed("okru:1", 1, 1)
    assert controller.state["playbackPhase"] == "web"


def test_navigation_reuses_catalog_without_remote_reload(controller, monkeypatch):
    controller, app = controller
    rows = [{"title": "Cached", "items": []}]
    controller.catalog_pages["Movies"] = (time.monotonic(), rows)
    calls = []
    monkeypatch.setattr(controller, "submit", lambda *args: calls.append(args))
    controller.navigate("Movies")
    controller.navigate("Settings")
    controller.navigate("Movies")
    assert controller.state["rows"] == rows
    assert calls == []
    controller.update(tmdbAvailable=True)
    controller.refreshCatalog()
    assert len(calls) == 1


def test_reselecting_loading_menu_does_not_restart_request(controller, monkeypatch):
    controller, app = controller
    controller.update(page="Explore", busy=True)
    calls = []
    monkeypatch.setattr(controller, "cancel_pending", lambda: calls.append("cancel"))
    controller.navigate("Explore")
    assert not calls


def test_explore_appends_deduplicates_and_retries_without_skipping(
    controller, monkeypatch
):
    controller, app = controller
    controller.update(
        page="Explore",
        exploreItems=[{"key": "okru:1"}],
        exploreMore=True,
        exploreNumber=1,
    )
    controller.explore_active = ["okru"]
    calls = []

    def submit(tag, operation):
        calls.append(tag)
        controller.generations[tag] = len(calls)
        controller.update(busy=True)

    monkeypatch.setattr(controller, "submit", submit)
    controller.moreExplore()
    controller.moreExplore()
    assert calls == ["exploreMore"]
    controller._receive("exploreMore", 1, None, "offline")
    assert controller.state["exploreNumber"] == 1
    assert controller.state["exploreError"]
    controller.moreExplore()
    controller._receive(
        "exploreMore",
        2,
        {
            "rows": [{"items": [{"key": "okru:1"}, {"key": "okru:2"}]}],
            "active": [],
            "number": 2,
        },
        "",
    )
    assert [x["key"] for x in controller.state["exploreItems"]] == ["okru:1", "okru:2"]
    assert not controller.state["exploreMore"]
    controller.moreExplore()
    assert len(calls) == 2


def test_catalog_shows_fast_row_before_slow_source(controller, monkeypatch):
    import asyncio

    from lourihna_films.services.tmdb_service import TMDBService

    controller, app = controller

    async def fast(self):
        return [{"key": "tv:1", "title": "Ready"}]

    async def slow(self, *args):
        await asyncio.sleep(30)
        return []

    monkeypatch.setattr(TMDBService, "popular_series", fast)
    monkeypatch.setattr(TMDBService, "trending_movies", slow)
    monkeypatch.setattr(TMDBService, "discover", slow)
    controller.update(tmdbAvailable=True)
    controller.load_catalog("Home")
    deadline = time.monotonic() + 5
    while not controller.state["rows"] and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    assert controller.state["rows"][0]["items"][0]["title"] == "Ready"
    assert controller.state["busy"]
    generation = controller.generations["catalog"]
    controller.navigate("Settings")
    before = controller.state["rows"]
    controller._catalog_progress("Home", generation, {"title": "Late", "items": []})
    assert controller.state["rows"] == before


def test_explore_displays_fast_collection_while_search_is_pending(
    controller, monkeypatch
):
    import asyncio

    from lourihna_films.services.search_service import SearchService

    controller, app = controller
    controller.repo.cache_put(
        "collection-v2:Movies:1",
        "",
        "archive",
        {
            "title": "Movies",
            "items": [{"key": "archive:ready"}],
            "source": "Movies",
            "more": False,
        },
        ttl=60,
    )

    async def slow(self, *args, **kwargs):
        await asyncio.sleep(30)
        return {"items": [], "more": False}

    monkeypatch.setattr(SearchService, "search", slow)
    controller.navigate("Explore")
    deadline = time.monotonic() + 5
    while not controller.state["exploreItems"] and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    assert controller.state["exploreItems"] == [{"key": "archive:ready"}]
    assert controller.state["busy"]


def test_large_explore_payload_is_not_copied_into_general_ui_state(controller):
    import json

    controller, app = controller
    notifications = []
    controller.exploreItemsChanged.connect(lambda: notifications.append(True))
    entries = [{"key": f"test:{index}", "title": "Test"} for index in range(2000)]
    controller.update(exploreItems=entries)
    controller.update(busy=True)
    assert "exploreItems" not in controller.uiState
    assert json.loads(controller.exploreItemsJson) == entries
    assert notifications == [True]


def test_startup_with_malformed_saved_credentials(tmp_path, monkeypatch):
    from lourihna_films.core import secrets

    for name in ("TMDB_TOKEN", "TMDB_API_KEY", "BRAVE_SEARCH_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(secrets, "WINDOWS", True)
    _app = QCoreApplication.instance() or QCoreApplication([])
    engine = create_database(tmp_path / "invalid-credentials.db")
    repo = Repository(engine)
    repo.save_settings({"tmdb_token": "dpapi:a", "ui_language": "gl"})
    backend = None
    try:
        backend = ApplicationController(repo)
        assert not backend.state["tmdbAvailable"]
        assert backend.state["uiLanguage"] == "gl"
        backend.forgetCredentials()
        assert repo.settings()["tmdb_token"] == ""
    finally:
        if backend is not None:
            backend.shutdown()
        engine.dispose()
