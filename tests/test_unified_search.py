# ==========================================================================
"""test_unified_search.py
Verify unified search contracts using isolated fixtures.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from lourihna_films.services.unified_search import search_all


@pytest.mark.asyncio
async def test_okru_is_primary_and_exhausted_sources_not_repeated():
    calls = []

    async def public(query, page, provider, remember):
        calls.append((provider, page))
        await asyncio.sleep(0)
        return {
            "items": [{"key": provider + str(page)}],
            "more": provider == "archive" and page == 1,
        }

    search = SimpleNamespace(
        providers={"okru": object(), "archive": object()}, search=public
    )
    tmdb = SimpleNamespace(
        search=AsyncMock(side_effect=lambda q, kind, page: [{"key": kind}])
    )
    repo = SimpleNamespace(
        remember_query=Mock(),
        library=Mock(return_value=[{"key": "okru1", "local_title": True}]),
    )
    result = await search_all("film", search, tmdb, repo, True)
    assert {x["key"] for x in result["items"]} == {"okru1", "movie", "tv"}
    assert result["items"][0]["local_title"]
    assert result["cursors"] == {}
    second = await search_all("film", search, tmdb, repo, True, result["cursors"])
    assert not second["more"]
    assert calls == [("okru", 1)]
    assert tmdb.search.await_count == 2
    assert repo.library.call_count == 1


@pytest.mark.asyncio
async def test_failed_provider_keeps_other_results_without_credentials():
    async def public(query, page, provider, remember):
        if provider == "okru":
            raise RuntimeError("private diagnostic")
        return {"items": [{"key": "archive:1"}], "more": False}

    search = SimpleNamespace(
        providers={"okru": object(), "archive": object()}, search=public
    )
    tmdb = SimpleNamespace(search=AsyncMock())
    repo = SimpleNamespace(
        remember_query=Mock(), library=Mock(return_value=[{"key": "local:1"}])
    )
    result = await search_all("film", search, tmdb, repo, False)
    assert len(result["items"]) == 2
    assert result["notice"] == "okru"
    tmdb.search.assert_not_awaited()


@pytest.mark.asyncio
async def test_cancellation_propagates():
    search = SimpleNamespace(
        providers={"okru": object()},
        search=AsyncMock(side_effect=asyncio.CancelledError),
    )
    repo = SimpleNamespace(remember_query=Mock(), library=Mock(return_value=[]))
    with pytest.raises(asyncio.CancelledError):
        await search_all("film", search, None, repo, False)
