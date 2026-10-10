import asyncio
import hashlib
import json
from teleputin.core.policy import METADATA_TTL, ARTWORK_BATCH_TIMEOUT
from teleputin.core.http import get_json
from teleputin.core.exceptions import ServiceError
from teleputin.models.movie import CatalogItem


class TMDBService:
    def __init__(self, client, token="", key="", language="en-US", repository=None, artwork=None, translator=None, background_artwork=False):
        self.client, self.token, self.key, self.language = client, token, key, language
        self.repository, self.artwork = repository, artwork
        self.notice = ""
        self.translator = translator
        self.background_artwork = background_artwork

    async def request(self, path, **params):
        if not (self.token or self.key):
            raise ServiceError("Connect TMDB in Settings to discover movies and series. You can still open OK.ru URLs in Search.")
        params.setdefault("language", self.language)
        cache_key = "tmdb:" + hashlib.sha256(json.dumps([path, params], sort_keys=True).encode()).hexdigest()
        if self.repository:
            cached = self.repository.cache_get(cache_key)
            if cached is not None: return cached
        headers = {}
        if self.token: headers["Authorization"] = f"Bearer {self.token}"
        else: params["api_key"] = self.key
        try:
            result = await get_json(self.client, f"https://api.themoviedb.org/3/{path}", params=params, headers=headers)
        except ServiceError:
            cached = self.repository.cache_get(cache_key, allow_stale=True) if self.repository else None
            if cached is None: raise
            self.notice = "TMDB is unavailable. Showing cached metadata."
            return cached
        if self.repository: self.repository.cache_put(cache_key, "", "tmdb", result, ttl=METADATA_TTL)
        return result

    @staticmethod
    def image(path, size="w500"):
        return f"https://image.tmdb.org/t/p/{size}{path}" if path and path.startswith("/") else ""

    def item(self, row, kind):
        return CatalogItem(id=row["id"], kind=kind, title=row.get("title") or row.get("name") or "Untitled", year=(row.get("release_date") or row.get("first_air_date") or "")[:4], poster=self.image(row.get("poster_path")), backdrop=self.image(row.get("backdrop_path"), "w1280"), overview=row.get("overview") or "No description available.", rating=row.get("vote_average") or 0).card()

    async def listing(self, path, kind="movie", **params):
        data = await self.request(path, **params)
        items = [self.item(x, kind) for x in data.get("results", [])]
        return await self.decorate(items)

    async def decorate(self, items):
        if not self.artwork: return items
        if self.background_artwork:
            return [self.artwork.preview(item) for item in items]
        try:
            return await asyncio.wait_for(asyncio.gather(*(self.artwork.card(self.client, item) for item in items)), timeout=ARTWORK_BATCH_TIMEOUT)
        except TimeoutError:
            # Metadata stays usable even when artwork delivery is slow.
            return items

    async def trending_movies(self): return await self.listing("trending/movie/week")
    async def popular_movies(self): return await self.listing("movie/popular")
    async def popular_series(self): return await self.listing("tv/popular", "tv")
    async def discover(self, genre): return await self.listing("discover/movie", with_genres=genre)
    async def search(self, query, kind="movie", page=1): return await self.listing(f"search/{kind}", kind, query=query, page=page)

    async def details(self, identifier, kind):
        if kind not in ("movie", "tv"): raise ServiceError("Unsupported catalog type.")
        row = await self.request(f"{kind}/{int(identifier)}", append_to_response="alternative_titles,recommendations,credits")
        data = self.item(row, kind)
        if not row.get("overview"):
            try:
                fallback = await self.request(f"{kind}/{int(identifier)}", language="en-US")
                original = fallback.get("overview", "")
                if original:
                    data.update(overview=original, overview_original=original, overview_language="en")
                    if self.translator and self.language.split("-")[0] != "en":
                        data["overview"] = await self.translator.translate(self.client, original, self.language)
                        data.update(overview_translated=True, overview_language=self.language)
            except ServiceError:
                data["translation_notice"] = "No se pudo traducir. Se conserva la sinopsis disponible."
        alt = row.get("alternative_titles", {})
        data.update(genres=[x["name"] for x in row.get("genres", [])], runtime=row.get("runtime") or next(iter(row.get("episode_run_time", [])), None), alternatives=list(dict.fromkeys(x["title"] for x in alt.get("titles", alt.get("results", [])) if x.get("title"))), seasons=row.get("seasons", []), related=[self.item(x, kind) for x in row.get("recommendations", {}).get("results", [])])
        data["original_title"] = row.get("original_title") or row.get("original_name") or data["title"]
        data["directors"] = list(dict.fromkeys(x.get("name", "") for x in row.get("credits", {}).get("crew", []) if x.get("job") == "Director"))
        data["tagline"] = row.get("tagline", "")
        data["related"] = await self.decorate(data["related"])
        return (await self.decorate([data]))[0]

    async def episodes(self, identifier, season):
        data = await self.request(f"tv/{int(identifier)}/season/{int(season)}")
        return await self.decorate([{**x, "still": self.image(x.get("still_path"), "w300")} for x in data.get("episodes", [])])
