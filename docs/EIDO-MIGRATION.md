# EIDO adaptation and identity migration — 0.4.0

The existing Python/PySide6/QML application was retained. The original source snapshot is preserved in Git and a local backup. No user database is committed or distributed.

## Scope

- Owned modules carry a 76-character banner, filename, responsibility and the exact EIDO signature. Ruff provides consistent formatting and import checks. Public application contracts have type annotations and English docstrings; JSON/Qt and third-party keyword boundaries retain `Any` where their schema is intentionally dynamic.
- Qt overrides, QML slots/properties and existing JSON keys keep their contracted names. Tests use pytest fixture injection; local CLI callbacks remain implementation details rather than new public APIs.
- The controller remains a cohesive Qt facade despite exceeding the guide's module-size warning threshold: splitting playback/navigation in this identity-only task would increase behavior risk. No speculative abstractions were introduced.
- CLI verification scripts now run only under a main guard. Third-party license texts and the supplied style guide are unchanged.

## Renames

The Python package, executable, spec file, database filename and log prefix are `lourihna_films`. Distribution files use `lourihna-films`. Brand environment variables use `LOURIHNA_FILMS`; visible UI uses Louriña Films. The GitHub URL is deliberately unchanged. The outer local workspace and archived backups are retained to avoid breaking existing local references; they are not the published project identity.

## Compatibility exception

Only `lourihna_films/core/compatibility.py` contains literal previous-brand identifiers. Its three constants locate the legacy directory, database filename and optional legacy data-directory override. It copies a consistent SQLite snapshot after integrity validation, preserves originals, and never overwrites an existing destination. Compatible DPAPI blobs retain their original user protection; their description is not decryption entropy. No old-brand environment aliases are used for new writes.

## Welcome lifecycle

`core/startup.py`, `ui/Splash.qml` and the entry point share a two-condition gate. A QElapsedTimer starts on the first splash frame. A GUI-thread QTimer checks both the minimum 3,000 ms and successful main-page readiness. Database recovery and migration run in an owned worker; QML creation stays on the GUI thread. Errors leave a closable message. Closing cancels callbacks and disposes a completed database instead of revealing the main window.

## Verification and distribution

See the release notes for commands and results actually completed. Windows is packaged with PyInstaller plus Inno Setup. Linux uses the same onedir layout in a tar.gz with a user installer, avoiding an additional FUSE dependency. The workflow smoke-tests native playback, WebEngine lifecycle and SQLite before uploading artifacts. Linux desktop variation and signed Windows installer trust remain outside the CI smoke test.

The existing session-only credential map remains owned by the secrets module; replacing this internal lifetime mechanism was intentionally deferred to preserve authentication behavior. CLI and pytest callbacks are not exposed as application APIs. The obsolete unused root logo was archived locally and replaced with a byte-for-byte copy of the current logo.
