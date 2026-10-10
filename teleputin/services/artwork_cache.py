"""Bounded local artwork cache restricted to TMDB's official image host."""
import asyncio
import hashlib
from pathlib import Path
from urllib.parse import urlsplit
import httpx
from teleputin.core.policy import ARTWORK_MAX_BYTES, ARTWORK_BUDGET_BYTES, ARTWORK_CONCURRENCY, ARTWORK_TIMEOUT, ARTWORK_QUEUE_LIMIT


class ArtworkCache:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.limit = asyncio.Semaphore(ARTWORK_CONCURRENCY)
        self.pending = {}
        self.worker = None

    def preview(self, item):
        """Return cached artwork immediately and warm missing files independently."""
        result = dict(item)
        for field in ("poster", "backdrop", "still"):
            url = item.get(field, "")
            if not url.startswith("https://image.tmdb.org/"):
                continue
            filename = self.directory / (hashlib.sha256(url.encode()).hexdigest() + ".img")
            if filename.is_file():
                result[field] = filename.resolve().as_uri()
            elif len(self.pending) < ARTWORK_QUEUE_LIMIT:
                self.pending[url] = None
        if self.pending and (self.worker is None or self.worker.done()):
            self.worker = asyncio.create_task(self._warm())
        return result

    async def _warm(self):
        # This client outlives individual catalog requests and closes on shutdown.
        async with httpx.AsyncClient(follow_redirects=False) as client:
            while self.pending:
                urls = list(self.pending)[:ARTWORK_CONCURRENCY]
                await asyncio.gather(*(self.get(client, url) for url in urls))
                for url in urls:
                    self.pending.pop(url, None)

    async def get(self, client, url):
        if not url: return ""
        try:
            parsed = urlsplit(url)
            port = parsed.port
        except ValueError: return ""
        if parsed.scheme != "https" or parsed.hostname != "image.tmdb.org" or parsed.username or parsed.password or port not in (None, 443): return ""
        filename = self.directory / (hashlib.sha256(url.encode()).hexdigest() + ".img")
        if filename.is_file():
            filename.touch()
            return filename.resolve().as_uri()
        async with self.limit:
            if filename.is_file(): return filename.resolve().as_uri()
            try:
                async with client.stream("GET", url, timeout=ARTWORK_TIMEOUT, follow_redirects=False) as response:
                    response.raise_for_status()
                    if response.headers.get("content-type", "").split(";")[0] not in ("image/jpeg", "image/png", "image/webp"): return url
                    data = bytearray()
                    async for chunk in response.aiter_bytes():
                        data.extend(chunk)
                        if len(data) > ARTWORK_MAX_BYTES: return url
                if not data: return url
                # Unique files avoid partially visible artwork during interrupted writes.
                temporary = filename.with_suffix(".part")
                temporary.write_bytes(data)
                temporary.replace(filename)
                self.prune()
                return filename.resolve().as_uri()
            except (httpx.HTTPError, OSError):
                return url

    def prune(self):
        files = sorted(self.directory.glob("*.img"), key=lambda p: p.stat().st_mtime)
        total = sum(p.stat().st_size for p in files)
        for file in files:
            if total <= ARTWORK_BUDGET_BYTES: break
            total -= file.stat().st_size
            file.unlink(missing_ok=True)

    async def card(self, client, item):
        fields = [key for key in ("poster", "backdrop", "still") if item.get(key)]
        values = await asyncio.gather(*(self.get(client, item[key]) for key in fields))
        return {**item, **dict(zip(fields, values))}
