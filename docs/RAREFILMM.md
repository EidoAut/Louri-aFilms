# Public video integration architecture

## Scope and source

Reviewed the actual [default.py](https://github.com/Nigel1992/rarefilmm-kodi-addon/blob/c112685db52251c4198dbd83d76353c376d55b85/default.py) at commit `c112685db52251c4198dbd83d76353c376d55b85` by Nigel Hagen. The project is MIT licensed; its notice remains in `docs/licenses/rarefilmm-MIT.txt` and the portable distribution. This is an independent adaptation of architectural ideas, not an import of Kodi code, catalog, features or UI. No new dependency is required.

LourihnaFilms searches public OK.ru videos by title. It does not query RareFilmm, download its index or assume that addon implements global OK.ru search. The earlier catalog integration has been removed. Saved user data is retained; an older catalog favorite opens without contacting its former source and can be searched by title using the current OK.ru pipeline.

## Actual upstream implementation

Upstream is predominantly a single procedural `default.py`, rather than provider classes:

| Concern | Actual implementation | Consequence for adaptation |
| --- | --- | --- |
| HTTP | `http_get()` constructs `urllib.request.Request`, applies timeout and headers, reads the response, handles gzip and decodes the declared charset with UTF-8 fallback. Although a persistent `_opener` is declared, this function actually calls `urllib.request.urlopen()`. | Use an explicitly owned `httpx.AsyncClient` and a shared bounded reader; do not assume upstream's opener provides pooling. |
| Discovery | `parse_index()` matches dated RareFilmm post anchors; `get_index_entries()` fetches and deduplicates them. `search_movies()` performs a case-insensitive substring search on those titles. | Reuse the staged fetch/parse/normalize pattern, not the index or its search algorithm as a global OK.ru service. |
| HTML and identity | Regular expressions and `strip_tags()` normalize HTML/entities. `find_direct_links()` collects source tags, download anchors and media URLs; it also loads iframes and scans script payloads. | Separate pure HTML parsing from strict OK.ru numeric identity validation. No arbitrary nested iframe requests. |
| OK.ru and playback | The addon does not expose a dedicated global OK.ru search provider or strict OK.ru identity class. It scans embedded payloads, including `hlsManifestUrl`, and passes resolved media to Kodi in `play_movie()`. | Do not adopt media/manifest extraction. Resolve only an official `/videoembed/<id>` navigation URL and let OK.ru enforce access and embedding restrictions. |
| Metadata | `fetch_movie_metadata()` reads Open Graph image and description tags, supports property/name variants, and HTML-unescapes descriptions. | Retain public Open Graph/JSON-LD metadata extraction as a separate stage. TMDB remains responsible for cinematic movie metadata and artwork. |
| Concurrency | `get_index_entries()` schedules up to 100 guessed pages through a 32-worker `ThreadPoolExecutor`; `fetch_multiple_metadata()` uses a thread pool and batches cache writes. Imported `ProcessPoolExecutor` is not used in these paths. This is threaded blocking I/O, not asyncio. | Keep LourihnaFilms's cancellable asyncio worker. Batch and cache metadata, but serialize public OK.ru requests through a shared pacing lock instead of copying aggressive concurrency. |
| Cache | Timestamped JSON index cache has configurable TTL. Metadata is kept in an in-memory dictionary and a JSON file, with no equivalent TTL in `fetch_movie_metadata()`. | Retain SQLite and explicit positive/negative TTLs; use stale metadata with a clear notice when refresh fails. |
| Pagination | `_fetch_page()` constructs RareFilmm index page URLs. `list_movies()` slices the cached index using `PAGE_SIZE` (50). | Do not invent OK.ru pagination. The observed anonymous HTML search and public HTML fallback support only their first result page; Brave's supported pagination remains unchanged. |
| Errors | HTTP errors are logged and raised; page fetch failures become empty results. Metadata exceptions return empty image/description values. Missing direct links fall back to the page URL. | Distinguish an individual missing video from access denial; preserve discovered titles and show source failures rather than inventing results or treating page URLs as media. |

## LourihnaFilms components and adopted patterns

1. `core/public_http.py`: centralized public transport with host boundary, response byte limits, charset decoding, robots rules (including query paths), shared rate pacing, challenge detection and explicit error reasons. Discovery and metadata reuse the same reader within a worker operation. Redirects, access denial and server failures stop further requests in that batch; a 404/410 for one video does not block other videos.
2. `providers/direct_search.py`: pure `PublicVideoCards` HTML parser plus public-search orchestration and external fallback. It no longer calls a private method on the metadata extractor or owns duplicate robots/pacing logic. No endpoints were added.
3. `models/okru_identity.py`: strict host/path/port validation and canonical public/embed URLs. `providers/okru.py` remains the existing provider adapter and re-exports prior helpers for compatibility.
4. `providers/result_normalization.py`: safely normalizes heterogeneous provider rows, skips malformed rows, and merges useful metadata from duplicate canonical IDs instead of discarding richer later rows. It never sets embedding permission from URL syntax.
5. `providers/public_metadata.py`: public HTML/JSON-LD parsing and identity matching; no scripts or private player state are resolved. Fetching delegates to the shared reader. Missing metadata for one page no longer stops the whole batch.
6. `services/metadata_service.py`: cached batch enrichment, independent of library persistence. Positive metadata lives for 24 hours, empty results for five minutes; stale successful metadata survives temporary failures with an explicit notice. Only fetched IDs get negative cache entries when a batch is blocked. Existing search titles and durations are preserved if enrichment fails.
7. `services/candidate_service.py`: bounded title/year/director variants, deduplication and relevance ranking remain. Candidates are enriched before saving, avoiding the previous import-placeholder overwrite. No movie catalog is consulted. `services/library_service.py` reuses the same enrichment service but owns explicit link import and persistence.
8. `services/playback_service.py`: validates the chosen video, respects an explicit embedding denial and reconstructs only the official OK.ru embed URL. Persisted or search-provided stream/embed URLs are never trusted as playback targets.
9. `services/search_service.py` keeps provider routing and SQLite result caching, with a normalization cache namespace version so old serialized results do not silently bypass the new boundary. `ApplicationController` owns the HTTP client and injected metadata service, keeps cancellation/generation guards and dispatches playback through the resolver. QML's RareFilmm controls were removed; the Netflix layout, colors, logo and TMDB browsing were preserved.

The former `providers/rarefilmm.py`, `providers/catalog.py` and `services/catalog_service.py` are removed. No replacement generic plugin framework or duplicate cache database was introduced. The existing Internet Archive feature remains independent and unchanged.

## Validation and comparison

Live public checks on 2026-10-10, before (15:51 UTC) and after (15:57 UTC) the adaptation:

| Check | Before | After |
| --- | --- | --- |
| `Metropolis 1927` | 14 public candidates, 14 with durations | Same 14 IDs and durations present |
| `Night of the Living Dead 1968` | 20 public candidates, 20 with durations | Same 20 IDs and durations present |
| `https://ok.ru/video/2116476930726` | Title, description, thumbnail and duration 5,581 seconds | Same public metadata fields and duration |

These are observations, not coverage guarantees or a benchmark. Live reports are in local `artifacts/okru-before.json` and `artifacts/okru-after.json`; `scripts/verify_okru_live.py` repeats the current-path check on demand. It also checks a URL returned by title search and records its canonical official embed address. No playback or embedding permission is inferred from those checks. TMDB integration is regression-tested with mocked authenticated responses; no user TMDB credential is included in test fixtures or packages.

The final automated run passed 97 tests; the 11-step QML lifecycle check reported zero QML errors.

Tests cover provider routing, shared transport and pacing, denial/redirect/challenge/size boundaries, missing-video continuation, malformed results, richer duplicate merging, metadata cache reuse/stale fallback, placeholder-overwrite regression, playback URL validation, retained user data and absence of the removed catalog dependency. The existing full test suite and QML lifecycle checks remain in use.

## Remaining limitations

Public OK.ru HTML is a best-effort interface, not an official global search API. Markup, ranking, visibility and restrictions can change. Unknown search markup triggers the existing external fallback. No guessed pagination, login automation, CAPTCHA solving, private endpoint, HLS/MP4 extraction or DRM circumvention is implemented. Public-page metadata is not proof that a video is playable, complete, correctly matched or licensed for a particular use. The official player may impose login, geographic or embedding restrictions. Cached metadata can be outdated and is labeled when served stale. The MIT license covers the reference software, not video distribution rights.

## Player diagnosis: 2026-10-10

A user-reported black screen exposed a limitation not covered by the original browser-lifecycle smoke test. The public embed page loaded successfully, but the installed Qt WebEngine returned empty `canPlayType` results for H.264 and AAC, while VP9 returned `probably`. Loading HTML is not evidence of playable media. Qt documents the build requirement at https://doc.qt.io/qt-6/qtwebengine-features.html#audio-and-video-codecs.

`PlayerPage.qml` now runs a local capability probe before navigating to an OK.ru embed. Missing capabilities produce an explicit system-browser fallback, preserving the official player and existing URL validation. New-window requests do not set a fatal playback error. The UI verification script checks completion of the capability probe and the fallback panel. `scripts/diagnose_player.py [public-embed-url]` reports codec support and visible page errors without extracting stream addresses. Embedded H.264/AAC playback remains unavailable in this Qt build; full support requires a compatible browser engine/build.
