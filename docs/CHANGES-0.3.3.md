# TelePutin 0.3.3

- Fixed long filename-style titles overflowing into adjacent cards: bounded text rectangle, wrapping and ellipsis. Thumbnail decoding is limited to the displayed width at the current pixel density.
- Catalog sections retain completed results in memory for five minutes. Reopening a section no longer empties/reloads an unchanged catalog. Explicit Refresh and configuration changes invalidate this cache. Repeated selection of an already loading section does not cancel/restart its request.
- Page creation uses the asynchronous QML loader. The fade from black was removed. Loading now identifies the current catalog, synopsis/details or video search instead of an unexplained spinner.
- Verification: 149 tests passed, compact QML capture without errors, long unbroken title shown beside a second card without overlap. Native playback, quality switching, pause, resume and fullscreen controls passed after the loader change.

First visits and explicit refresh still depend on the source response time. This change reduces redundant work; it does not claim a measured frame-rate improvement on every machine. Screenshot: [title regression check](screenshots/title-overflow-fixed.png).

- My List now exposes explicit Add/Remove actions on cards, details and the hero, plus a search shortcut from the list. Removing a favorite preserves the library and watch history.
