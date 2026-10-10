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
