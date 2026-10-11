# Cinema interface redesign — 2026-10-11

The existing PySide6/QML application now uses a compact navigation header,
a responsive panoramic feature, horizontal catalog rows, a single hover preview,
and a modal detail sheet. The original logo, Inter font and corporate colors are
retained: background `#0B1012`, accent `#27B99A`, selection `#287CC1`, text
`#F3F0E8`. Shared geometry and interaction timing live in `ui/Theme.qml`.

## Components and behavior

- `CatalogArtwork.qml` loads images asynchronously with bounded decode sizes,
  tries available fallbacks, preserves portrait proportions and renders rounded
  corners on both software and GPU backends. `HeroArtwork.qml` reuses it.
- `FeaturedBanner.qml`, `ContentCarousel.qml` and `VideoCard.qml` share the same
  artwork and typography. Vertical wheel events remain available to the page;
  horizontal wheel input or Shift-wheel moves a row.
- `HoverPreview.qml` owns one delayed preview above the clipping containers.
  Leaving a card cancels a pending opening. A short dismissal cooldown prevents
  immediate reopening after Escape. Space or Down opens the same controls from
  a focused card; Enter opens details and Left/Right reveal adjacent cards.
  Favorites retain their existing database
  action.
- `Main.qml` keeps the underlying catalog loader alive during detail and player
  navigation. Closing the detail popup restores focus and both scroll positions.
  Narrow navigation moves secondary sections into the menu without removing them.
- `DetailsPage.qml` uses a scrollable two-column layout which stacks on narrow
  windows. Progress comes from saved history. Available season/episode metadata
  supplies titles, thumbnails, runtimes and descriptions.

The default interface language for a new profile is Galician. Existing saved
language preferences remain intact. The earlier audit fixes remain included.

## Data boundaries

No recommendation engine, age rating, quality badge, trailer or playback source
has been invented. Rows retain their actual provider categories. Catalog-only
entries offer source discovery; video entries offer playback or resumption.
Previews are static because no verified trailer is currently supplied by the
model. Text and artwork availability depend on the providers; synopsis language
continues to follow the configured metadata/translation settings.

## Verification

`scripts/verify_cinema_ui.py --catalog <public-catalog-snapshot.json> --size
1280x720` runs real QML with an isolated SQLite database and substituted network
responses. The snapshot contains public catalog metadata and cached public
artwork, never credentials or personal history. Repeat with `1920x1080` and
`720x900`. Outputs are in `artifacts/redesign/<size>/`.

The interactive checks cover delayed-hover cancellation, preview window bounds,
favorite persistence, keyboard access and focus restoration, modal dismissal,
catalog lifetime and scroll retention, real series metadata, search state and
missing artwork. The normal UI verification also exercises progressive loading
with 2,000 catalog entries, native playback and navigation. Playback controls and
resumption are additionally covered by `scripts/verify_controls.py`.

The local Windows build is under `dist/cinema-redesign/lourihna_films/`; existing
release archives and installers are not republished by this local redesign.

## Responsiveness follow-up — 2026-10-11

The updated local build is `dist/fluid-ui/lourihna_films/`.
QML now consumes a stable `viewState` property map with notifications per field.
Changing loading, playback or favorite state no longer converts the complete
catalog for every binding. The existing `state` and `uiState` snapshot APIs remain
available, and no-op updates no longer emit redundant notifications.

Artwork decode sizes use shared buckets so a card and its hover panel can reuse
the image cache. Rounded corners use four small textures instead of an
image-sized transparent Canvas. Normal hover dismissal no longer imposes a
global cooldown; explicit dismissal and keyboard Escape still prevent accidental
reopening. Section navigation cancels pending previews.

In the same 1280x720 isolated catalog scenario, the worst loading-state update
dropped from 83.4 ms to below 1 ms (0.2–0.7 ms across follow-up runs). This measures
GUI update dispatch and event processing, not network latency or frame rate.
The verification script also checks native Windows interaction, retained card
objects, and cached section dispatch. A regression test checks that loading and
playback notifications do not re-evaluate the catalog binding.

## HDMI audio routing — 2026-10-11

The native player now binds its AudioOutput to MediaDevices.defaultAudioOutput,
following system output changes while playback remains active. Its Audio menu
also allows selecting any currently reported output for the current player
session. If that device disconnects, routing falls back to the system default.
Volume, mute and playback position are independent of this selection. Embedded
web playback continues to use Chromium/Windows audio routing.

The existing `dist/fluid-ui` runtime includes the updated QML. Control checks
exercise automatic routing, each available output, return to automatic mode,
the output menu, and pause/volume/position preservation. The available hardware
reported one Realtek speaker output; physical HDMI playback and hot-plug behavior
still require a connected television. No Windows default-device settings were
changed. The binding follows the
[Qt MediaDevices guidance](https://doc.qt.io/qt-6/qml-qtmultimedia-mediadevices.html).

## History controls — 2026-10-11

The navigation menu now exposes a shared history dialog. Search and My List
also provide shortcuts with the appropriate history preselected. Users can
delete search history, viewing history, or both; Escape/Cancel leaves data
untouched. Viewing-history deletion includes saved progress and continue-watching
entries. Favorites, library records and preferences remain intact.

The repository deletes the selected tables in one transaction and validates the
scope before deleting anything. Controller snapshots update immediately; search
deletion also clears the current query/results. Deletion is disabled during
pending operations. The existing no-argument clearHistory API still clears both.

Verification covers all three scopes and invalid scopes in isolated databases,
and real QML confirmation/cancellation and selective deletion. No personal
history is deleted during installation or verification. The new local runtime
is `dist/history-controls/lourihna_films/` and includes the earlier UI and HDMI
audio changes.

## Release consolidation — 0.5.0

The current Windows runtime is `dist/release-0.5.0/lourihna_films/`.
Earlier runtime paths above document intermediate builds. The release includes
the redesign, granular state updates, audio routing and history controls.
See `RELEASE-0.5.0.md` for Windows and native Linux validation results.
