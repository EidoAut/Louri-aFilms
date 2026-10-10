# ==========================================================================
"""test_artwork_background.py
Verify artwork background contracts using isolated fixtures.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

import asyncio

import httpx
import pytest

from lourihna_films.services.artwork_cache import ArtworkCache
from lourihna_films.services.tmdb_service import TMDBService


@pytest.mark.asyncio
async def test_metadata_does_not_wait_for_images_and_cache_work_is_deduplicated(
    tmp_path, monkeypatch
):
    cache = ArtworkCache(tmp_path)
    started = asyncio.Event()
    release = asyncio.Event()
    calls = []

    async def slow(client, url):
        calls.append(url)
        started.set()
        await release.wait()
        return url

    monkeypatch.setattr(cache, "get", slow)
    async with httpx.AsyncClient() as client:
        service = TMDBService(client, artwork=cache, background_artwork=True)
        item = {"poster": "https://image.tmdb.org/t/p/w500/test.jpg"}
        assert await asyncio.wait_for(service.decorate([item]), timeout=0.2) == [item]
        await started.wait()
        assert await service.decorate([item]) == [item]
        assert not cache.worker.done()
        release.set()
        await cache.worker
        assert calls == [item["poster"]]


@pytest.mark.asyncio
async def test_preview_uses_persistent_cache_without_network(tmp_path):
    import hashlib

    cache = ArtworkCache(tmp_path)
    url = "https://image.tmdb.org/t/p/w500/test.jpg"
    filename = tmp_path / (hashlib.sha256(url.encode()).hexdigest() + ".img")
    filename.write_bytes(b"cached")
    assert cache.preview({"poster": url})["poster"] == filename.as_uri()
    assert cache.worker is None
