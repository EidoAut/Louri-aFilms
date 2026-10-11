# ==========================================================================
"""test_storage.py
Verify storage contracts using isolated fixtures.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

import pytest
from sqlalchemy import text

from lourihna_films.database.engine import create_database
from lourihna_films.database.repositories import Repository
from lourihna_films.providers.okru import OKRuProvider
from lourihna_films.services.search_service import SearchService


@pytest.fixture
def repository(tmp_path):
    engine = create_database(tmp_path / "test.db")
    yield Repository(engine)
    engine.dispose()


def test_favorites_persist_and_toggle(repository):
    item = {"key": "movie:1", "id": 1, "title": "Кино", "kind": "movie"}
    repository.toggle_favorite(item)
    assert Repository(repository.engine).favorites() == [item]
    repository.toggle_favorite(item)
    assert repository.favorites() == []


def test_cache_expiry(repository):
    repository.cache_put("expired", "query", "okru", {"items": []}, ttl=-1)
    assert repository.cache_get("expired") is None
    repository.cache_put("valid", "query", "okru", {"items": [1]})
    assert repository.cache_get("valid") == {"items": [1]}


@pytest.mark.parametrize("scope", ["search", "watch", "all"])
def test_clear_history_preserves_unselected_data(repository, scope):
    """History deletion must preserve the library, favorites and other history."""
    item = {
        "key": "okru:123",
        "id": "123",
        "provider": "okru",
        "kind": "video",
        "title": "Saved film",
        "original_url": "https://ok.ru/video/123",
    }
    repository.save_videos([item])
    repository.toggle_favorite(item)
    repository.record_open(item)
    repository.save_progress("okru", "123", 12000, 60000, False)
    repository.remember_query("Film")
    repository.cache_put("search", "Film", "okru", {"items": [item]})
    repository.save_settings({"volume": "0.6"})
    library, favorites = repository.library(), repository.favorites()
    repository.clear_history(scope)
    reopened = Repository(repository.engine)
    assert bool(reopened.history()) == (scope == "search")
    assert bool(reopened.recent_searches()) == (scope == "watch")
    assert bool(reopened.cache_get("search")) == (scope == "watch")
    assert reopened.library() == library
    assert reopened.favorites() == favorites
    assert reopened.settings()["volume"] == "0.6"


def test_invalid_history_scope_does_not_delete(repository):
    repository.remember_query("Keep")
    with pytest.raises(ValueError):
        repository.clear_history("invalid")
    assert repository.recent_searches() == ["Keep"]


async def test_search_cache_and_history(repository):
    provider = OKRuProvider(None)
    service = SearchService({"okru": provider}, repository)
    first = await service.search("https://ok.ru/video/123")
    assert first == await service.search("https://ok.ru/video/123")
    assert repository.recent_searches() == ["https://ok.ru/video/123"]
    repository.record_open(first["items"][0])
    repository.record_open(first["items"][0])
    assert len(repository.history()) == 1
    with repository.engine.connect() as connection:
        assert (
            connection.execute(text("SELECT position FROM watch_history")).scalar()
            is None
        )
    repository.clear_history()
    assert repository.history() == [] and repository.recent_searches() == []


def test_future_schema_is_not_downgraded(tmp_path):
    path = tmp_path / "future.db"
    engine = create_database(path)
    with engine.begin() as c:
        c.execute(text("PRAGMA user_version=99"))
    engine.dispose()
    with pytest.raises(RuntimeError, match="newer"):
        create_database(path)


def test_windows_credential_roundtrip():
    import os

    if os.name != "nt":
        pytest.skip("Windows DPAPI")
    from lourihna_films.core.secrets import protect, reveal

    encrypted = protect("secret-123")
    assert "secret-123" not in encrypted
    assert reveal(encrypted) == "secret-123"


@pytest.mark.parametrize("finished", [False, True])
def test_pending_preserves_progress_unless_restarting_a_finished_video(
    repository, finished
):
    video = {
        "key": "okru:123",
        "id": "123",
        "provider": "okru",
        "kind": "video",
        "title": "Pending fixture",
    }
    repository.record_open(video)
    repository.save_progress("okru", "123", 5000, 10000, finished)
    repository.keep_watching("okru", "123", True)
    item = Repository(repository.engine).continuing()[0]
    assert item["key"] == video["key"]
    assert not item["finished"]
    assert item["position_ms"] == (0 if finished else 5000)
    assert item["duration_ms"] == 10000
    repository.keep_watching("okru", "123", False)
    assert repository.continuing() == []


def test_removing_finished_video_from_pending_preserves_completion(repository):
    repository.record_open(
        {"key": "okru:123", "id": "123", "provider": "okru", "title": "Fixture"}
    )
    repository.save_progress("okru", "123", 10000, 10000, True)
    repository.keep_watching("okru", "123", False)
    assert repository.history()[0]["finished"]


@pytest.mark.parametrize("value", ["dpapi:a", "dpapi:@@@", "dpapi:\u00f1"])
def test_malformed_credentials_have_a_recoverable_error(monkeypatch, value):
    from lourihna_films.core import secrets

    monkeypatch.setattr(secrets, "WINDOWS", True)
    with pytest.raises(RuntimeError, match="saved credential is invalid"):
        secrets.reveal(value)


def test_invalid_decrypted_text_has_a_recoverable_error(monkeypatch):
    from lourihna_films.core import secrets

    monkeypatch.setattr(secrets, "WINDOWS", True)
    monkeypatch.setattr(secrets, "transform", lambda *args: b"\xff")
    with pytest.raises(RuntimeError, match="saved credential is invalid"):
        secrets.reveal("dpapi:YQ==")
