# ==========================================================================
"""application_controller.py
Qt facade. All HTTP work lives on one owned asyncio worker thread.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from lourihna_films.database.repositories import Repository
    from lourihna_films.providers.direct_search import DirectPublicSearch
    from lourihna_films.providers.public_search import PublicSearch
    from lourihna_films.providers.web_search import BraveSearch
    from lourihna_films.services.artwork_cache import ArtworkCache
    from lourihna_films.services.metadata_service import MetadataService
    from lourihna_films.services.search_service import SearchService
    from lourihna_films.services.tmdb_service import TMDBService

import asyncio
import concurrent.futures
import json
import logging
import threading
import time

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices

from lourihna_films.core.config import credentials
from lourihna_films.core.exceptions import ServiceError
from lourihna_films.core.policy import CATALOG_NAVIGATION_TTL, CATALOG_ROWS
from lourihna_films.core.secrets import protect, reveal
from lourihna_films.providers.archive import ArchiveProvider, archive_id_from_url
from lourihna_films.providers.direct_search import DirectPublicSearch
from lourihna_films.providers.okru import OKRuProvider
from lourihna_films.providers.public_metadata import PublicMetadata
from lourihna_films.providers.public_search import PublicSearch
from lourihna_films.providers.web_search import BraveSearch
from lourihna_films.services.artwork_cache import ArtworkCache
from lourihna_films.services.candidate_service import CandidateService
from lourihna_films.services.discovery_service import DiscoveryService
from lourihna_films.services.library_service import LibraryService
from lourihna_films.services.metadata_service import MetadataService
from lourihna_films.services.playback_service import resolve_okru
from lourihna_films.services.search_service import SearchService
from lourihna_films.services.tmdb_service import TMDBService


class ApplicationController(QObject):
    """Own Qt state, asynchronous service requests and playback-session transitions."""

    changed = Signal()
    exploreItemsChanged = Signal()
    completed = Signal(str, int, object, str)
    catalogProgress = Signal(str, int, object)

    def __init__(self, repository: Repository, recover: bool = True) -> None:
        super().__init__()
        self.repo = repository
        if recover:
            repository.recover_library()
        from lourihna_films.services.translation_service import TranslationService

        self.translator = TranslationService(
            Path(repository.engine.url.database).parent / "translation-models",
            repository,
        )
        self.artwork = ArtworkCache(
            Path(repository.engine.url.database).parent / "artwork"
        )
        self._state = {
            "page": "Home",
            "rows": [],
            "results": [],
            "favorites": repository.favorites(),
            "history": repository.history(),
            "recent": repository.recent_searches(),
            "details": {},
            "episodes": [],
            "player": {},
            "query": "",
            "searchPage": 1,
            "more": False,
            "busy": False,
            "message": "",
            "configured": "",
            "candidates": [],
            "candidateNotice": "",
            "candidatesBusy": False,
            "continuing": repository.continuing(),
        }
        self.catalog_pages = {}
        self.explore_active = []
        self.update(
            exploreItems=[], exploreMore=False, exploreNumber=0, exploreError=False
        )
        self.generations = {}
        self.futures = {}
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(
            target=self._run, name="lourihna_films-network", daemon=True
        )
        self.thread.start()
        self.completed.connect(self._receive)
        self.catalogProgress.connect(self._catalog_progress)
        self._configure()
        saved = self.repo.settings()
        try:
            volume = min(1.0, max(0.0, float(saved.get("volume", "0.8"))))
        except ValueError:
            volume = 0.8
        self.update(
            volume=volume,
            muted=saved.get("muted") == "true",
            uiLanguage=saved.get("ui_language", "es"),
            motion=saved.get("motion", "true") == "true",
            bufferedMedia={},
            playbackPhase="idle",
            playbackError="",
        )

    def _run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
        self.loop.close()

    @Property("QVariantMap", notify=changed)
    def state(self) -> dict[str, Any]:
        """Return the complete controller snapshot for internal callers and tests."""
        return self._state

    @Property("QVariantMap", notify=changed)
    def uiState(self) -> dict[str, Any]:
        # Large discovery payloads must not be copied for every button binding.
        """Return lightweight UI state without the separately delivered discovery payload."""
        return {
            key: value for key, value in self._state.items() if key != "exploreItems"
        }

    @Property(str, notify=exploreItemsChanged)
    def exploreItemsJson(self) -> None:
        """Serialize the discovery snapshot only when its dedicated model changes."""
        return json.dumps(self._state.get("exploreItems", []))

    def update(self, **values: Any) -> None:
        """Merge explicit state changes and notify the QML bindings on the GUI thread."""
        self._state = {**self._state, **values}
        self.changed.emit()
        if "exploreItems" in values:
            self.exploreItemsChanged.emit()

    def cancel_pending(self) -> None:
        """Invalidate outstanding request generations before cancelling owned work."""
        for tag, future in list(self.futures.items()):
            self.generations[tag] = self.generations.get(tag, 0) + 1
            future.cancel()
        self.futures.clear()
        self.update(busy=False, candidatesBusy=False)

    def _configure(self):
        saved = self.repo.settings()
        for key in ("tmdb_token", "tmdb_key", "brave_key"):
            try:
                saved[key] = reveal(saved.get(key, ""))
            except RuntimeError:
                saved[key] = ""
        self.config = credentials(saved)
        connected = bool(self.config["tmdb_token"] or self.config["tmdb_key"])
        from lourihna_films.core.secrets import WINDOWS

        self.update(
            translationEnabled=saved.get("translate_synopsis", "true") == "true",
            language=self.config["language"],
            credentialSessionOnly=not WINDOWS,
            tmdbAvailable=connected,
            braveAvailable=bool(self.config["brave_key"]),
            tmdbEnabled=connected,
            configured="Catálogo conectado"
            if connected
            else "Configura TMDB para explorar su catálogo",
        )

    async def _services(self, operation):
        async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
            tmdb = TMDBService(
                client,
                self.config["tmdb_token"],
                self.config["tmdb_key"],
                self.config["language"],
                repository=self.repo,
                artwork=self.artwork,
                translator=self.translator
                if self._state.get("translationEnabled")
                else None,
                background_artwork=True,
            )
            metadata = PublicMetadata(client)
            search = SearchService(
                {
                    "okru": OKRuProvider(
                        DirectPublicSearch(
                            client,
                            BraveSearch(client, self.config["brave_key"])
                            if self.config["brave_key"]
                            else PublicSearch(client),
                            reader=metadata.reader,
                        )
                    ),
                    "archive": ArchiveProvider(client),
                },
                self.repo,
                MetadataService(self.repo, metadata),
            )
            return await operation(tmdb, search)

    def submit(
        self,
        tag: str,
        operation: Callable[[TMDBService, SearchService], Awaitable[Any]],
    ) -> None:
        """Schedule a service operation and deliver only its current-generation result to Qt."""
        generation = self.generations.get(tag, 0) + 1
        self.generations[tag] = generation
        old = self.futures.get(tag)
        if old:
            old.cancel()
        self.update(busy=True, loadingTask=tag, message="")
        future = asyncio.run_coroutine_threadsafe(self._services(operation), self.loop)
        self.futures[tag] = future

        def done(result):
            try:
                self.completed.emit(tag, generation, result.result(), "")
            except concurrent.futures.CancelledError:
                pass
            except ServiceError as exc:
                self.completed.emit(tag, generation, None, str(exc))
            except Exception as exc:
                # Keep stack locations without exception messages that may contain signed URLs.
                import traceback

                logging.error(
                    "Operation %s failed (%s)\n%s",
                    tag,
                    type(exc).__name__,
                    "".join(traceback.format_tb(exc.__traceback__)),
                )
                self.completed.emit(
                    tag,
                    generation,
                    None,
                    "This operation failed. Please try again. See the local log for the error type.",
                )

        future.add_done_callback(done)

    @Slot(str, int, object)
    def _catalog_progress(self, page, generation, row):
        if self._state["page"] != page or self.generations.get("catalog") != generation:
            return
        if page == "Explore":
            items = {item["key"]: item for item in self._state["exploreItems"]}
            items.update((item["key"], item) for item in row["items"])
            self.update(exploreItems=list(items.values()))
        else:
            rows = [
                value for value in self._state["rows"] if value["title"] != row["title"]
            ]
            rows.append(row)
            order = {
                title: index
                for index, (title, _) in enumerate(CATALOG_ROWS.get(page, []))
            }
            rows.sort(key=lambda value: order.get(value["title"], len(order)))
            self.update(rows=rows)

    @Slot(str, int, object, str)
    def _receive(self, tag, generation, data, error):
        if self.generations.get(tag) != generation:
            return
        self.futures.pop(tag, None)
        changes = {"busy": bool(self.futures), "message": error}
        if error:
            logging.warning("Operation %s failed (%s)", tag, "source-unavailable")
            changes["message"] = "No se pudo completar la acción. Prueba de nuevo."
        if (
            tag == "exploreMore"
            or (tag == "catalog" and self._state["page"] == "Explore")
        ) and error:
            changes["exploreError"] = True
        if tag == "buffered" and error:
            changes.update(
                bufferedMedia={},
                playbackPhase="error"
                if self._state["player"].get("provider") == "archive"
                else "web",
                playbackError="Este vídeo no está disponible. Prueba otra fuente.",
                message="",
            )
        if tag == "candidates":
            changes.update(candidatesBusy=False, candidateNotice=error, message="")
        if error and tag == "search" and self._state["searchPage"] > 1:
            changes["searchPage"] = self._state["searchPage"] - 1
        if not error:
            if tag == "exploreMore" or (
                tag == "catalog" and self._state["page"] == "Explore"
            ):
                previous = self._state["exploreItems"] if tag == "exploreMore" else []
                items = [item for row in data["rows"] for item in row["items"]]
                unique = {item["key"]: item for item in previous + items}
                self.explore_active = data.get("active", [])
                changes.update(
                    exploreItems=list(unique.values()),
                    exploreMore=bool(self.explore_active),
                    exploreNumber=data.get("number", 1),
                    exploreError=bool(data.get("notice")),
                )
            if tag == "catalog":
                self.catalog_pages[self._state["page"]] = (
                    time.monotonic(),
                    data["rows"],
                )
                changes.update(
                    rows=data["rows"],
                    message="Algunas fuentes no están disponibles ahora."
                    if data.get("notice")
                    else "",
                )
            elif tag == "play":
                self._open_player(data)
            elif tag == "buffered":
                changes.update(
                    bufferedMedia={
                        **data[0],
                        "index": 0,
                        "attempts": 0,
                        "sources": data,
                    },
                    playbackPhase="native",
                    playbackError="",
                )
            elif tag == "details":
                changes.update(
                    details=data, episodes=[], favorites=self.repo.favorites()
                )
            elif tag == "candidates":
                changes.update(
                    candidates=data["items"], candidateNotice=data.get("notice", "")
                )
            elif tag == "settings":
                changes["message"] = "Catálogo conectado. Ya puedes explorar películas."
            elif tag == "episodes":
                changes["episodes"] = data
            elif tag == "search":
                self.search_cursors = data.get("cursors")
                previous = (
                    self._state["results"] if self._state["searchPage"] > 1 else []
                )
                unique = {x["key"]: x for x in previous + data["items"]}
                changes.update(
                    results=list(unique.values()),
                    more=data["more"],
                    recent=self.repo.recent_searches(),
                )
                changes["message"] = (
                    "Algunas fuentes no están disponibles ahora."
                    if data.get("notice")
                    else ""
                )
        changes["busy"] = bool(self.futures)
        self.update(**changes)
        if tag == "details" and not error and data.get("kind") in ("movie", "tv"):
            self.findCandidates()

    @Slot(str)
    def navigate(self, page: str) -> None:
        """Switch the visible page and start or reuse its catalog request."""
        if page == self._state["page"] and (
            self._state["busy"] or self._state.get("rows")
        ):
            return
        self.cancel_pending()
        if page != "Player":
            self.update(player={}, bufferedMedia={})
        self.update(page=page, message="")
        if page in ("Home", "Movies", "Series", "Documentaries", "Explore"):
            self.load_catalog(page)

    def load_catalog(self, page: str) -> None:
        """Publish cached rows first and fetch missing provider rows asynchronously."""
        cached = self.catalog_pages.get(page)
        if cached and time.monotonic() - cached[0] < CATALOG_NAVIGATION_TTL:
            self.update(rows=cached[1])
            return
        generation = self.generations.get("catalog", 0) + 1

        def publish(row):
            self.catalogProgress.emit(page, generation, row)

        if page == "Explore":
            self.update(
                rows=self.local_rows(page),
                exploreItems=self.repo.library(),
                exploreMore=False,
                exploreNumber=0,
                exploreError=False,
            )

            async def explore(tmdb, search):
                data = await DiscoveryService(search, self.repo).load(
                    page, on_row=publish
                )
                return {**data, "rows": data["rows"] + self.local_rows(page)}

            self.submit("catalog", explore)
            return
        if not self._state["tmdbAvailable"]:
            self.update(rows=self.local_rows(page))
            return
        self.update(rows=cached[1] if cached else [])

        async def catalog(tmdb, search):
            jobs = []
            for title, kind in CATALOG_ROWS.get(page, CATALOG_ROWS["Home"]):
                if kind == "trending":
                    job = tmdb.trending_movies()
                elif kind == "series":
                    job = tmdb.popular_series()
                elif kind == "movies":
                    job = tmdb.popular_movies()
                else:
                    job = tmdb.discover(kind)
                jobs.append((title, job))

            async def fetch(title, job):
                """Fetch and normalize available public metadata for the requested video identifier."""
                items = await job
                if items:
                    publish({"title": title, "items": items})
                return items

            results = await asyncio.gather(
                *(fetch(title, job) for title, job in jobs), return_exceptions=True
            )
            rows, errors = [], []
            for (title, _), result in zip(jobs, results):
                if isinstance(result, ServiceError):
                    errors.append(str(result))
                elif isinstance(result, BaseException):
                    raise result
                elif result:
                    rows.append({"title": title, "items": result})
            if tmdb.notice:
                errors.append(tmdb.notice)
            return {"rows": rows, "notice": " ".join(dict.fromkeys(errors))}

        self.submit("catalog", catalog)

    @Slot()
    def moreExplore(self) -> None:
        """Request the next discovery page unless an operation is already pending."""
        if (
            self._state["page"] != "Explore"
            or self._state["busy"]
            or not self._state["exploreMore"]
        ):
            return
        number = self._state["exploreNumber"] + 1
        active = list(self.explore_active)
        self.update(exploreError=False)

        async def operation(tmdb, search):
            return await DiscoveryService(search, self.repo).load(
                "Explore", number, active
            )

        self.submit("exploreMore", operation)

    def local_rows(self, page: str) -> list[dict[str, Any]]:
        """Group saved videos by category without performing network requests."""
        category = page if page in ("Movies", "Series", "Documentaries") else None
        items = self.repo.library(category=category)
        rows = (
            [
                {
                    "title": "Tu colección" if category is None else category,
                    "items": items,
                }
            ]
            if items
            else []
        )
        if category is None:
            for name in sorted({item.get("category", "General") for item in items}):
                grouped = [
                    item for item in items if item.get("category", "General") == name
                ]
                rows.append({"title": name, "items": grouped})
        return rows

    @Slot(bool)
    def setMetadataEnabled(self, enabled: bool) -> None:
        """Persist whether the optional metadata catalog should be used."""
        self.repo.save_settings({"tmdb_enabled": "yes" if enabled else "no"})
        self.update(tmdbEnabled=enabled)

    @Slot(str, str)
    def importLinks(self, text: str, category: str | None) -> None:
        """Import supported public links and preserve them even when metadata is unavailable."""
        self.catalog_pages.clear()
        self.cancel_pending()
        self.update(
            page="Search",
            query="",
            results=[],
            more=False,
            searchPage=1,
            player={},
            searchMode="Library",
        )

        async def operation(tmdb, search):
            async with httpx.AsyncClient(timeout=8, follow_redirects=False) as client:
                return await LibraryService(self.repo, client).import_links(
                    text, category
                )

        self.submit("search", operation)

    @Slot(str, str)
    def importFile(self, url: str, category: str | None) -> None:
        """Read a local link list and pass its contents to the import pipeline."""
        path = Path(QUrl(url).toLocalFile())
        try:
            if (
                not QUrl(url).isLocalFile()
                or not path.is_file()
                or path.stat().st_size > 1_000_000
            ):
                raise ValueError()
            self.importLinks(path.read_text(encoding="utf-8-sig"), category)
        except (ValueError, OSError, UnicodeError):
            self.update(message="Elige un archivo de enlaces de menos de 1 MB.")

    @Slot(str, str, str)
    def organize(self, key: str, title: str, category: str | None) -> None:
        """Persist an explicit local title and category for the selected library item."""
        self.catalog_pages.clear()
        item = self.repo.organize(key, title, category)
        if item:
            self.update(
                details=item,
                favorites=self.repo.favorites(),
                message="Guardado en tu colección.",
            )

    @Slot()
    def refreshMetadata(self) -> None:
        """Refresh metadata for existing library videos without discarding saved links."""
        item = self._state["details"]

        async def operation(tmdb, search):
            async with httpx.AsyncClient(timeout=8, follow_redirects=False) as client:
                result = await LibraryService(self.repo, client).import_links(
                    item["original_url"], refresh=True
                )
                return result["items"][0]

        if item.get("provider") == "archive":

            async def operation(tmdb, search):
                video = (await search.providers["archive"].get_video(item["id"])).card()
                video["metadata_status"] = "Public Archive metadata"
                self.repo.save_videos([video])
                return next(x for x in self.repo.library() if x["key"] == video["key"])

        self.submit("details", operation)

    @Slot(str, str)
    def search(self, query: str, mode: str = "All") -> None:
        """Query the selected provider or catalog and preserve its pagination contract."""
        query = query.strip()[:500]
        if not query:
            return
        self.cancel_pending()
        self.search_cursors = None
        self.search_mode = mode
        label = "OK.ru" if mode in ("OK.ru", "Web search (optional)") else mode
        self.update(
            page="Search",
            query=query,
            searchPage=1,
            results=[],
            more=False,
            player={},
            searchMode=label,
        )
        self._search(query, 1)

    def _search(self, query, page):
        mode = getattr(self, "search_mode", "All")
        cursors = getattr(self, "search_cursors", None)

        async def operation(tmdb, search):
            from lourihna_films.providers.okru import video_id_from_url

            if video_id_from_url(query):
                self.repo.remember_query(query)
                async with httpx.AsyncClient(
                    timeout=8, follow_redirects=False
                ) as client:
                    return await LibraryService(self.repo, client).import_links(query)
            if archive_id_from_url(query):
                return await search.search(query, page, provider="archive")
            if mode == "All":
                from lourihna_films.services.unified_search import search_all

                return await search_all(
                    query,
                    search,
                    tmdb,
                    self.repo,
                    self._state["tmdbAvailable"],
                    cursors,
                )
            if mode == "Internet Archive":
                return await search.search(query, page, provider="archive")
            if mode == "Discover":
                results = await asyncio.gather(
                    search.search(query, page),
                    search.search(query, page, provider="archive"),
                    return_exceptions=True,
                )
                items, notices, more = [], [], False
                for result in results:
                    if isinstance(result, ServiceError):
                        notices.append(str(result))
                    elif isinstance(result, BaseException):
                        raise result
                    else:
                        items.extend(result["items"])
                        more = more or result["more"]
                        if result.get("notice"):
                            notices.append(result["notice"])
                if not items and notices:
                    items = self.repo.library(query)[(page - 1) * 40 : page * 40]
                    if items:
                        notices.append("Showing matching saved videos.")
                return {"items": items, "more": more, "notice": " ".join(notices)}
            if mode == "Library":
                self.repo.remember_query(query)
                if query.startswith(("https:", "http:")):
                    raise ServiceError(
                        "Unsupported URL. Paste an OK.ru /video/<numeric ID> link."
                    )
                items = self.repo.library(query)
                return {
                    "items": items[(page - 1) * 40 : page * 40],
                    "more": len(items) > page * 40,
                    "notice": "Searching your saved collection.",
                }
            if mode in ("OK.ru", "Web search (optional)"):
                return await search.search(query, page)
            self.repo.remember_query(query)
            items = await tmdb.search(
                query, "movie" if mode == "Movies" else "tv", page
            )
            return {"items": items, "more": len(items) == 20 and page < 500}

        self.submit("search", operation)

    @Slot()
    def more(self) -> None:
        """Request the next result page while retaining previously displayed results."""
        if self._state["busy"] or not self._state["more"]:
            return
        page = self._state["searchPage"] + 1
        self.update(searchPage=page)
        self._search(self._state["query"], page)

    @Slot("QVariantMap")
    def select(self, item: dict[str, Any]) -> None:
        """Open the selected catalog or video detail page without assuming availability."""
        if self._state["page"] not in ("Details", "Player"):
            self._details_return = self._state["page"]
        self.cancel_pending()
        self.update(
            page="Details",
            details=item,
            episodes=[],
            player={},
            candidates=[],
            candidateNotice="",
            candidatesBusy=False,
        )
        if item.get("kind") == "video" and not item.get("metadata_status"):
            self.refreshMetadata()
        elif item.get("kind") == "catalog":
            # Preserve older saved entries without contacting their former catalog.
            self.update(
                message="This saved catalog entry is no longer a discovery source. Search its title on OK.ru."
            )
        elif item.get("kind") in ("movie", "tv") and self._state["tmdbAvailable"]:
            self.submit(
                "details", lambda tmdb, search: tmdb.details(item["id"], item["kind"])
            )

    @Slot()
    def backFromDetails(self) -> None:
        """Return to the catalog page recorded before opening details."""
        self.cancel_pending()
        self.update(page=getattr(self, "_details_return", "Home"), message="")

    @Slot()
    def findCandidates(self) -> None:
        """Resolve real public candidates for the current catalog entry asynchronously."""
        catalog = dict(self._state["details"])
        if catalog.get("kind") not in ("movie", "tv", "catalog"):
            return
        self.update(candidatesBusy=True, candidateNotice="", candidates=[])

        async def operation(tmdb, search):
            return await CandidateService(search, self.repo, tmdb.client).find(catalog)

        self.submit("candidates", operation)

    @Slot(int)
    def season(self, number: int) -> None:
        """Load episode metadata for the requested season number."""
        self.update(episodes=[])
        identifier = self._state["details"]["id"]
        self.submit("episodes", lambda tmdb, search: tmdb.episodes(identifier, number))

    @Slot("QVariantMap")
    def findEpisode(self, episode: dict[str, Any]) -> None:
        """Create the selected episode query and discover matching public sources."""
        catalog = {
            **self._state["details"],
            "season_number": int(episode.get("season_number", 1)),
            "episode_number": int(episode.get("episode_number", 1)),
            "episode_title": episode.get("name", ""),
        }
        self.cancel_pending()
        self.update(candidatesBusy=True, candidates=[], candidateNotice="")
        self.submit(
            "candidates",
            lambda tmdb, search: CandidateService(search, self.repo, tmdb.client).find(
                catalog
            ),
        )

    @Slot("QVariantMap")
    def favorite(self, item: dict[str, Any]) -> None:
        """Toggle the selected item in the persistent local favorites list."""
        self.repo.toggle_favorite(item)
        self.update(favorites=self.repo.favorites())

    @Slot("QVariantMap")
    def play(self, item: dict[str, Any]) -> None:
        """Prepare the selected source and record its library playback session."""
        if item.get("kind") != "video":
            return
        self.cancel_pending()
        # Reconstruct from the provider rather than trusting persisted/embed data.

        self._player_return = (
            self._state["page"] if self._state["page"] != "Player" else "Home"
        )
        if item.get("provider") == "archive":
            identifier = archive_id_from_url(item.get("original_url", ""))
            if not identifier:
                self.update(message="Este enlace no es compatible.")
                return

            async def operation(tmdb, search):
                video = (await search.providers["archive"].get_video(identifier)).card()
                self.repo.save_videos([video])
                return video

            self.submit("play", operation)
            return
        try:
            video = resolve_okru(item)
        except ServiceError as exc:
            self.update(message=str(exc))
            return
        self._open_player(video)

    def _open_player(self, video):
        if self._state["page"] == "Details" and any(
            x.get("key") == video["key"] for x in self._state["candidates"]
        ):
            video = {
                **video,
                "catalog": self._state["details"],
                "catalog_association": {
                    "method": "user-selected-candidate",
                    "match_score": video.get("match_score"),
                    "source": video.get("source_name", video.get("provider")),
                },
            }
        self.repo.record_open(video)
        history = self.repo.history()
        stored = next((item for item in history if item["key"] == video["key"]), video)
        self.update(
            page="Player",
            player={
                **video,
                "position_ms": 0
                if stored.get("finished")
                else stored.get("position_ms", 0),
            },
            bufferedMedia={},
            playbackPhase="loading",
            playbackError="",
            history=history,
            continuing=self.repo.continuing(),
            message="",
        )
        self.playBuffered()

    @Slot()
    def stopBuffered(self) -> None:
        """Release the current native playback state."""
        self.cancel_pending()
        self.update(bufferedMedia={})

    @Slot()
    def playBuffered(self) -> None:
        """Resolve permitted public media formats for native buffered playback."""
        video = self._state.get("player", {})
        if video.get("provider") not in ("okru", "archive"):
            return
        self.cancel_pending()
        stored = next(
            (
                item
                for item in self.repo.history()
                if item.get("key") == video.get("key")
            ),
            {},
        )
        video = {
            **video,
            "position_ms": 0
            if stored.get("finished")
            else stored.get("position_ms", video.get("position_ms", 0)),
        }
        self.update(
            player=video,
            bufferedMedia={},
            playbackPhase="loading",
            playbackError="",
            playbackSession=self._state.get("playbackSession", 0) + 1,
        )

        async def operation(tmdb, search):
            from lourihna_films.providers.public_media import resolve_public_formats

            if video["provider"] == "archive":
                return await search.providers["archive"].playback_sources(video["id"])
            async with httpx.AsyncClient(follow_redirects=False) as client:
                return await resolve_public_formats(client, video["original_url"])

        self.submit("buffered", operation)

    @Slot(str, int, int)
    def playbackFailed(self, key: str, session: int, error_code: int) -> None:
        """Handle only failures belonging to the active playback session."""
        if key != self._state.get("player", {}).get(
            "key"
        ) or session != self._state.get("playbackSession", 0):
            return
        logging.warning(
            "Playback failed provider=%s code=%s",
            self._state["player"].get("provider"),
            error_code,
        )
        current = self._state.get("bufferedMedia", {})
        sources, index = current.get("sources", []), current.get("index", 0) + 1
        if index < len(sources) and current.get("attempts", 0) < 2:
            self.update(
                bufferedMedia={
                    **sources[index],
                    "index": index,
                    "attempts": current.get("attempts", 0) + 1,
                    "sources": sources,
                }
            )
        else:
            self.update(bufferedMedia={}, playbackPhase="web", playbackError="")

    @Slot(int)
    def selectQuality(self, index: int) -> None:
        """Select an available format index without inventing provider qualities."""
        current = self._state.get("bufferedMedia", {})
        sources = current.get("sources", [])
        if 0 <= index < len(sources) and index != current.get("index", 0):
            self.update(
                bufferedMedia={
                    **sources[index],
                    "index": index,
                    "attempts": 0,
                    "sources": sources,
                }
            )

    @Slot(str, int, float, float, bool)
    def saveProgress(
        self, key: str, session: int, position: int, duration: int, finished: bool
    ) -> None:
        """Persist playback progress in milliseconds for the matching active session."""
        video = self._state.get("player", {})
        if key != video.get("key") or session != self._state.get("playbackSession", 0):
            return
        self.repo.save_progress(
            video["provider"], video["id"], position, duration, finished
        )
        # Avoid rebuilding playback bindings on every progress checkpoint.

    @Slot(float, bool)
    def setVolume(self, volume: float, muted: bool) -> None:
        """Clamp and persist playback volume together with the mute preference."""
        import math

        if not math.isfinite(volume):
            return
        volume = min(1.0, max(0.0, volume))
        self.repo.save_settings({"volume": str(volume), "muted": str(muted).lower()})
        self.update(volume=volume, muted=muted)

    @Slot(str, bool)
    def savePreferences(self, language: str, motion: bool) -> None:
        """Persist the interface language and motion preference."""
        if language not in ("es", "gl"):
            return
        self.repo.save_settings(
            {"ui_language": language, "motion": str(motion).lower()}
        )
        self.update(uiLanguage=language, motion=motion)

    @Slot(str, int, str)
    def mediaDiagnostic(self, key: str, code: str, detail: str) -> None:
        """Log bounded playback diagnostics without exposing signed media URLs."""
        if key != self._state.get("player", {}).get("key"):
            return
        import re

        detail = re.sub(r"https?://\S+", "[source]", detail)
        detail = re.sub(
            r"(?i)(bearer\s+\S+|(?:token|api_key|sig|password)\s*[=:]\s*\S+)",
            "[redacted]",
            detail,
        )
        logging.warning("Media code=%s detail=%s", code, detail[:300])

    @Slot()
    def finishPlayback(self) -> None:
        """Mark the active video as completed in local history."""
        video = self._state.get("player", {})
        if video:
            self.repo.save_progress(video["provider"], video["id"], 0, 0, True)
            self.backFromPlayer()

    @Slot(bool)
    def keepWatching(self, enabled: bool) -> None:
        """Persist whether the active video belongs in the continue-watching list."""
        video = self._state["player"]
        if not video:
            return
        self.repo.keep_watching(video["provider"], video["id"], enabled)
        self.update(
            continuing=self.repo.continuing(),
            history=self.repo.history(),
            message="Añadido a pendientes." if enabled else "Eliminado de pendientes.",
        )

    @Slot()
    def backFromPlayer(self) -> None:
        """Close playback and restore the previous browsing page."""
        self.cancel_pending()
        self.update(
            page=getattr(self, "_player_return", "Home"),
            player={},
            bufferedMedia={},
            playbackPhase="idle",
            history=self.repo.history(),
            continuing=self.repo.continuing(),
            message="",
        )

    @Slot()
    def refreshCatalog(self) -> None:
        """Expire discovery snapshots and explicitly reload the current catalog."""
        page = self._state["page"]
        if page not in ("Home", "Movies", "Series", "Documentaries", "Explore"):
            return
        self.cancel_pending()
        self.catalog_pages.clear()
        self.repo.expire_discovery()
        self.load_catalog(page)

    @Slot(str)
    def openExternal(self, url: str) -> None:
        """Open a validated public URL in the system browser."""
        from lourihna_films.providers.okru import video_id_from_url

        if (
            video_id_from_url(url)
            or archive_id_from_url(url)
            or url
            in (
                "https://www.themoviedb.org",
                "https://www.themoviedb.org/settings/api",
                "https://api-dashboard.search.brave.com",
            )
        ):
            QDesktopServices.openUrl(QUrl(url))

    @Slot(bool)
    def setTranslationEnabled(self, enabled: bool) -> None:
        """Persist the optional local synopsis-translation preference."""
        self.repo.save_settings({"translate_synopsis": str(enabled).lower()})
        self.update(translationEnabled=enabled)

    @Slot(str, str, str)
    def saveSettings(self, token: str, brave: str, language: str) -> None:
        """Validate and protect provider credentials before updating session configuration."""
        try:
            values = {"language": language or "en-US"}
            if token.strip():
                import re

                credential = token.strip().removeprefix("Bearer ")
                is_key = bool(re.fullmatch(r"[0-9a-fA-F]{32}", credential))
                values["tmdb_key"] = protect(credential) if is_key else ""
                values["tmdb_token"] = "" if is_key else protect(credential)
            if brave.strip():
                values["brave_key"] = protect(brave.strip())
            self.repo.save_settings(values)
            self._configure()
            self.catalog_pages.clear()
            self.repo.expire_discovery()
            if self._state["tmdbAvailable"]:

                async def validate(tmdb, search):
                    from lourihna_films.core.http import get_json

                    params = {} if tmdb.token else {"api_key": tmdb.key}
                    headers = (
                        {"Authorization": f"Bearer {tmdb.token}"} if tmdb.token else {}
                    )
                    return await get_json(
                        tmdb.client,
                        "https://api.themoviedb.org/3/configuration",
                        params=params,
                        headers=headers,
                    )

                self.submit("settings", validate)
            else:
                self.update(message="Ajustes guardados.")
        except RuntimeError as exc:
            self.update(message=str(exc))

    @Slot()
    def forgetCredentials(self) -> None:
        """Remove persisted provider credentials and clear affected catalog snapshots."""
        self.catalog_pages.clear()
        from lourihna_films.core.secrets import SESSION_SECRETS

        SESSION_SECRETS.clear()
        self.repo.save_settings({"tmdb_token": "", "tmdb_key": "", "brave_key": ""})
        self._configure()
        self.update(message="Claves guardadas eliminadas.")

    @Slot()
    def clearHistory(self) -> None:
        """Clear local viewing history and notify the interface."""
        self.repo.clear_history()
        self.update(history=[], continuing=[], recent=[], message="Historial borrado.")

    @Slot(str)
    def notify(self, message: str) -> None:
        """Publish a user-facing message without changing the current page."""
        self.update(message=message)

    def shutdown(self) -> None:
        """Cancel and await owned workers before releasing the event loop."""

        async def cancel_all():
            tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

        try:
            asyncio.run_coroutine_threadsafe(cancel_all(), self.loop).result(timeout=5)
        except (TimeoutError, concurrent.futures.CancelledError):
            pass
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join(timeout=5)
