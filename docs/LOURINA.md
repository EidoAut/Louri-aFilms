# Louriña Films — presentation refresh

## Scope

The existing PySide6/QML application keeps its technical identity (`teleputin`, `TelePutin.exe`, database and data paths). Visible branding is Louriña Films. A before/after SHA-256 comparison confirmed that controller, service, provider, database and core Python files were unchanged. `main.py` only sets the new application display name; the application and organization identifiers remain intact.

## Visual system

Theme.qml centralizes the charcoal Atlantic palette, green primary actions, blue selection, warm text, Inter font, spacing, radii and control sizes. Existing red/gold token names remain compatible aliases for green actions and blue focus. Buttons, navigation, cards, image fallback, forms, popups, loading and playback controls share this system. Hover no longer enlarges cards. Following the updated visual preference, the hero fills the available width with the existing TMDB backdrop, falling back to a poster or public thumbnail even when enlargement is necessary. Failed image loads advance to the next available source. Hero and card spacing are more compact. No image lookup provider was added.

The bundled font is [Inter](https://github.com/google/fonts/tree/main/ofl/inter), distributed with its SIL Open Font License. No runtime font download is required. Original line SVG icons replace mixed Unicode player/window symbols. All previous handlers and shortcuts remain in place.

## Assets

See `teleputin/assets/brand/README.md` for originals, display variants, icon sizes and restoration limitations. The original supplied PNG is retained byte-for-byte. The display logo and symbol are raster cleanup variants on a dark background; they are not a clean vector master or pixel-identical restoration. Transparent edits retained artifacts and were not installed.

## Running

Use the renamed **Abrir Louriña Films** shortcut in the project directory. The existing portable executable location remains `Aplicacion/TelePutin.exe`. From source, use the existing launch scripts or run `python main.py` with the project environment.

## Validation

151 tests passed. Real QML screens were checked at compact and wide sizes, maximized, and with Qt scale factors 1.0, 1.25 and 1.5. Source UI checks exercise favorites and scrolling. Native playback checks cover pause/resume, seek, volume, mute, quality change and fullscreen restoration. The native volume control exists and remains available. The portable executable passed startup, native playback, browser lifecycle, SQLite integrity, shutdown and a second launch retaining the stored interface-language preference.

Screenshots under `docs/screenshots/lourina` are actual application captures. The public-catalog captures use real results from the existing Archive provider in an isolated temporary database; they do not seed or modify the user's library. Player test screenshots use a generated local test video, not a claimed available film.

## Limitations

Windows 11 was tested. Linux, Windows 10 and moving between physical displays with different scaling were not tested. Qt scale-factor runs simulate 125% and 150%; they do not certify every monitor configuration. Source image quality and availability remain provider-dependent. Embedded third-party player controls are owned by the provider and cannot be restyled by this QML theme. No authentication, playback, discovery or persistence changes were made to address existing provider limitations.
