# Navigation loading

Catalog metadata is delivered independently of image downloads. Existing disk artwork is reused immediately; missing artwork uses asynchronous QML loading while a bounded, deduplicated background queue warms the persistent cache. The cache owns its HTTP client and all background tasks are cancelled and awaited during application shutdown.

TMDB catalog rows and public Explore collections appear as each request completes. Final pagination, provider errors and retry cursors are committed only when the complete discovery request finishes. Progress signals carry a page and request generation so cancelled navigation cannot update another screen. Completed pages retain the existing five-minute navigation cache.

Cold network requests can still take time. A slow or unavailable source no longer prevents already available rows from appearing. This does not guarantee a provider response time or playback availability.

Validation: regression tests hold one provider or image download pending and verify that other content is already accessible; stale page updates are rejected and duplicate artwork work is coalesced.

## Explore stability follow-up

Each public discovery source has a 20-second total deadline, including nested requests. A timeout retains successful collections and exposes the existing explicit retry action; it does not advance past the failed page.

Explore updates its model only when its items change, not on every controller notification. Delegates use their own serialized entry instead of converting the full Python catalog for each card. Model synchronization is deferred and guarded against reentrancy. Pagination is triggered by downward movement, never by content-height or busy-state changes, and the same item count cannot trigger automatic requests repeatedly. A Load more button handles short or duplicate pages without an automatic request loop. Footer geometry stays stable when busy/error controls change.

Regression checks include a stalled provider, a duplicate pagination response and a 2,000-item Explore fixture in the actual QML interface. Fixtures are isolated from the user's database.

The general QML uiState excludes the discovery list. Explore receives a separate JSON snapshot only when discovery items change, avoiding repeated QVariant conversions across every UI binding.
