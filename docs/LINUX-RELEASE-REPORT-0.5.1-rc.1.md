# Linux 0.5.1-rc.1 compatibility report

Build date: 2026-10-13. Final verification: 2026-10-15. Branch: `main`. Repository: https://github.com/EidoAut/Louri-aFilms.

## Original failure and repair

The previous 0.5.0 Linux archive was built with a newer native ABI. Direct `readelf` inspection found imported GLIBC 2.38 symbols in `libpython3.12.so.1.0`, and GLIBC 2.34 requirements in Qt Core and WebEngine. Ubuntu 20.04 supplies GLIBC 2.31. Updating the installer alone, or replacing only Python, could not repair the complete dependency chain.

The new build compiles CPython and OpenSSL inside digest-pinned Ubuntu 20.04, uses an APT snapshot and hash-pinned Python wheels, and runs PyInstaller there. It never borrows native libraries from the host runner. A recursive ELF audit verifies architecture, imported symbol versions, links and dependency resolution. No replacement GLIBC is bundled.

Qt 6.8.3 uses compatible manylinux 2.28 wheels. OpenSSL 3.5.9 is built on Focal because Qt needs an OpenSSL 3 TLS backend while Focal's system Python SSL uses OpenSSL 1.1. Both needed ABI versions are retained. Qt, Python, FFmpeg and translation dependencies remain bundled. Host libstdc++, libgcc, GBM/DRM and graphics-driver libraries must match the host Mesa/LLVM stack; bundling Focal's copies caused a real Jammy/Noble failure that was reproduced and corrected.

The only application QML change is the internal loader identifier `native` Ã¢â€ â€™ `bufferedLoader`, because Qt 6.8 treats `native` as reserved. Public slots, properties, signals, layout, artwork and provider contracts remain unchanged. Version labels advance to 0.5.1; the distribution is explicitly labelled as a prerelease.

## Build environment and dependencies

| Component | Linux build |
| --- | --- |
| Base OS | Ubuntu 20.04 x86_64, immutable image digest |
| Build GLIBC | 2.31 |
| CPython | 3.12.15, compiled from SHA-256 verified source |
| PyInstaller | 6.16.0, onedir, UPX disabled |
| PySide6 / Shiboken / Qt | 6.8.3 |
| Qt multimedia FFmpeg | 7.1, LGPL 2.1 or later |
| OpenSSL for Qt | 3.5.9, compiled on Focal |
| CTranslate2 | 4.8.2, manylinux 2.27/2.28 |
| SentencePiece | 0.2.1 |
| NumPy | 2.2.6 |
| SQLAlchemy | 2.0.43 |
| Pydantic | 2.11.7 |
| HTTPX | 0.28.1 |
| Ruff | 0.14.0 |

The complete Linux dependency closure and wheel hashes are in `packaging/requirements-linux.lock`; the package records the installed versions in `PYTHON-REQUIREMENTS.txt` and native package versions in `SYSTEM-PACKAGES.txt`. Python 3.12 is retained because it is the existing project contract and the packaging code uses APIs newer than 3.10.

The APT snapshot is `20261001T000000Z`. Certificate/curl bootstrap uses official Focal repositories, and actual versions are recorded. For subsequent packages, authenticated snapshot metadata selects versions and SHA-256 values. Identical archives can be fetched from Ubuntu's live pool, with hash verification and fallback to the snapshot. This avoids observed snapshot latency and transient HTTP 503 failures without selecting newer versions.

`bash scripts/build-linux.sh` is the supported entry point. Build provenance includes the source commit and dirty flag. Tar ownership, ordering and source epoch are normalized, but actual timestamps and diagnostic reports prevent a claim of bit-identical output.

## Installer and user data

The archive root is `lourinha-films/`; its executable keeps the established internal name `lourihna_films`. Installation checks Linux/x86_64, GLIBC >=2.31, core runtime dependencies and destination ownership. It stages an update and removes stale runtime files.

Installation: `$HOME/.local/opt/lourinha-films`.
Desktop entry: `$HOME/.local/share/applications/lourinha-films.desktop`.
The entry uses the visible name LouriÃƒÂ±a Films and absolute executable/icon paths. No sudo is needed. The uninstaller checks exact managed destinations and keeps the personal profile. A historical `lourihna-films` directory is not silently removed.

## Verification scope

Local source checks passed on Focal: Ruff, formatting, 189 pytest cases with one Windows-only skip, real QML loading/stress with 2,020 catalog items, playback controls, decoded PCM audio, volume and mute against a virtual PulseAudio sink. Windows local pytest passed 188 cases with two Linux-only skips. The prior successful Windows CI build also packaged and smoke-tested the executable and generated the Inno Setup installer.

The corrected local candidate passed independent runtime containers on Ubuntu 20.04, 22.04 and 24.04. Each checked SHA-256, extraction, installation as an unprivileged user in a HOME containing spaces, update/stale-file removal, desktop validation and icon path, frozen startup and restart, malformed credential recovery, SQLite integrity, WebEngine lifecycle, local video frames, an MPEG4/AAC fixture, actual GTK desktop entry launch and visible window, and uninstall/data retention.

Desktop title detection uses UTF-8. The initial ASCII locale prevented `xwininfo` from decoding the ÃƒÂ± although the application window and database existed. This was fixed in the test harness.

Separate live source checks on Focal obtained 14 OK.ru search results for Metropolis and 20 for Night of the Living Dead; playback decoded three video frames and 31 audio buffers with no media error. Public catalog checks populated 11 rows. Spanish and Galician Argos models downloaded through the application and produced non-empty translations from the frozen executable. Models and provider URLs/tokens are excluded from distribution.

The initial bundled Focal libstdc++ incompatibility was resolved before the successful three-OS matrix. The first Windows CI playback smoke failed; rerunning the same commit passed. The original failure was not reproduced and its cause was not established. This is recorded rather than treated as evidence of universal hardware coverage. No deterministic application regression was found within the exercised scope.

## Limitations and release decision

- TMDB live validation requires a real user credential. No credential was available or embedded. Existing automated provider tests remain in the suite.
- The graphics tests use Xvfb and software Mesa. Physical GPUs, Wayland sessions, HDMI and physical audio devices were not certified.
- Audio decoding and virtual output were exercised; human-audible speaker playback was not assessed.
- Chromium sandbox stays enabled. The build/test containers use a documented Moby seccomp profile allowing its namespace calls. Desktop namespace/AppArmor policy may require administrator configuration; no host policy was modified.
- The system still needs the documented Linux desktop, sound, TLS trust and graphics libraries. A Python installation is unnecessary for end users.
- No other Linux distribution is declared verified.

These remaining acceptance boundaries require a prerelease rather than a stable release. User-visible instructions and release notes are in Galician.

## Changed files

Build and delivery: `.dockerignore`, `.github/workflows/build.yml`, `packaging/Dockerfile.linux`, `packaging/Dockerfile.linux-test`, `packaging/requirements-linux.lock`, `packaging/chromium-seccomp.json`, `lourihna_films.spec`, `scripts/build-linux.sh`, `scripts/build-linux-container.sh`, `scripts/install-linux-build-deps.sh`, `scripts/package_release.py`, `scripts/collect_linux_licenses.py`, `scripts/verify_linux_elf.py`.

Installation: `packaging/install-linux.sh`, `packaging/uninstall-linux.sh`.

Verification: `scripts/test-linux-package.sh`, `scripts/verify-linux-ui.sh`, `scripts/verify_linux_audio.py`, `scripts/verify_controls.py`, `scripts/verify_ui.py`, `tests/test_linux_packaging.py`.

Application compatibility/version: `main.py`, `lourihna_films/ui/pages/PlayerPage.qml`, `lourihna_films/ui/pages/SettingsPage.qml`, `pyproject.toml`, `packaging/windows.iss`.

Documentation and licenses: `README.md`, `docs/LINUX-COMPATIBILITY.md`, `docs/RELEASING.md`, `docs/licenses/THIRD-PARTY.md`, `docs/licenses/Moby-Profiles-APACHE-2.0.txt`, this report and the release notes. The EIDO Python style guide remains byte-for-byte unchanged.

## Provenance and publication

- Implementation commit: `d401abb243c2c2f0dc5b01a610824e1b0678c864` (`fix(linux): support Ubuntu 20.04+ and improve packaging`). Follow-up commits fix sandboxed verification, decoder settling, APT resilience, host graphics ABI and UTF-8 title inspection.
- Final binary source: `b7c13295e1e49bf5cab9454e59aa62f3466b0f2d`, branch `main`, clean tree. The tag points to this tested build commit; subsequent documentation commits do not change the binary.
- Canonical build: GitHub Actions run [38456598501](https://github.com/EidoAut/Louri-aFilms/actions/runs/38456598501), Linux artifact ID `11844243634`.
- Build time: `2026-10-13T19:54:03.318098+00:00`.
- Recursive ELF result: **548 files; maximum imported GLIBC 2.30**; all audit gates passed. Target minimum OS GLIBC remains 2.31.
- Archive: `LourinhaFilms-linux-x86_64-glibc231.tar.gz`, **315,806,985 bytes**.
- SHA-256: `9fab1b04f12535d3a4e34c2beaddd12e274b5d1474fd5d312da7e54e7abc6af3`.
- Local canonical CI artifact: `Codigo/dist/release-0.5.1-rc.1/`.
- User-facing copy: `Paquetes/Lourihna-0.5.1-rc.1/` beside `Codigo`.
- Published release: [v0.5.1-rc.1](https://github.com/EidoAut/Louri-aFilms/releases/tag/v0.5.1-rc.1), explicitly a prerelease. Publication checks source identity, clean provenance, SHA-256 and required CI jobs before upload.

| Verification | Result |
| --- | --- |
| Clean Focal build, Ruff, formatting | Passed |
| Linux pytest | 189 passed, 1 Windows-only skip |
| Source QML, controls and PCM audio | Passed |
| All packaged ELF dependencies | Passed; 548 ELF; GLIBC max 2.30 |
| Canonical CI package on Ubuntu 20.04 | Passed |
| Canonical CI package on Ubuntu 22.04 | Passed |
| Canonical CI package on Ubuntu 24.04 | Passed |
| Canonical CI package Spanish/Galician translation | Passed, 2026-10-15 |
| SHA-256 after downloading CI archive | Matches generated checksum |
| Windows CI rerun: lint, tests, packaged smoke and installer | Passed |
| Mirror helper accepts correct bytes and rejects altered bytes | Passed |
| EIDO style guide byte preservation | Verified |

The invalid-artwork messages in the UI test are deliberate corrupt-image fixtures; the resulting UI error list was empty. The exact CI artifact, rather than an earlier locally generated candidate, is selected for release. Earlier archives are superseded.


## Completion state

Implemented: build, ABI audit, installer, uninstaller, CI matrix and documentation.
Compiled: clean Ubuntu 20.04 candidate and Windows CI distribution.
Tested: the exact Linux candidate passed all three Ubuntu CI runtime jobs; its local translation check also passed.
Verified: clean source provenance, 548 ELF files, GLIBC maximum 2.30 and archive checksum.
Published: `v0.5.1-rc.1` on 2026-10-15 as a GitHub prerelease with the Linux archive, its `.sha256`, `SHA256SUMS.txt`, `BUILD-INFO.json` and `ELF-AUDIT.json`. Windows distribution files remain CI artifacts for this Linux-focused release. No stable release was created.

The public release download was streamed in full after publication: 315,806,985 bytes and SHA-256 matched the canonical CI archive. The copy in the user-facing Paquetes directory was independently hashed and also matched.
