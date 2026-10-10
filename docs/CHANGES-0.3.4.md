# LourihnaFilms 0.3.4

Explore now uses a virtualized vertical video grid. Scrolling near the end fetches the next public discovery page asynchronously. Results are deduplicated by provider and video ID, and exhausted sources are excluded from subsequent requests. Each Archive collection owns its pagination state. Page caches include the page number.

Failed or partial requests stop automatic loading and expose Retry. Retrying keeps the same page, with cached successful collections reused. Navigation cancellation rejects obsolete responses. Search results also request the next page on downward scrolling; the existing manual action remains available.

This uses the existing public discovery queries and supported provider pagination. It does not provide unlimited results when a provider reports no next page. Favorites and history are preserved.

Validation: 151 unit/integration tests passed. Compact QML verification confirmed one request near the bottom, append from 40 to 60 items without changing scroll position, and no QML errors. A live Archive check returned 20 videos on each of pages 1 and 2 with no overlapping identifiers.
