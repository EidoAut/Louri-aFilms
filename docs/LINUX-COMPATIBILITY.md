# Linux GLIBC 2.31 build audit

The previous workflow built directly on Ubuntu 24.04 using setup-python and
unbounded dependency ranges. Python, Qt and other native libraries therefore
inherited a newer ABI floor. The reported failure is libpython3.12's imported
GLIBC_2.38 symbol version, which Ubuntu 20.04 (GLIBC 2.31) cannot satisfy.
The local 0.5.0 Linux archive was inspected with readelf: libpython3.12.so.1.0
requires GLIBC 2.38, and libQt6Core.so.6 and libQt6WebEngineCore.so.6 require
GLIBC 2.34. Replacing Python alone would therefore not fix Ubuntu 20.04.

## Build decisions

- Preserve application/provider/QML contracts and existing `lourihna_films`
  executable and profile identity. The new installation/archive directory is
  `lourinha-films`, as requested, with no automatic removal of legacy installs.
- Compile CPython 3.12.15 from a SHA-256 checked source archive on Ubuntu 20.04.
  Python 3.10 would require changing the declared >=3.12 contract and packaging
  APIs (tomllib, hashlib.file_digest); retaining 3.12 avoids unrelated migration.
- Use Ubuntu 20.04 by immutable digest and APT snapshot 20261001T000000Z.
  Initial CA-certificate bootstrap uses official Focal repositories; its actual
  version is recorded. This is a repeatable build environment, not a claim of
  bit-identical output: BUILD-INFO records the actual build time.
- Pin Linux wheels and hashes separately from the pre-existing Windows lock.
  PySide6/Shiboken/Essentials/Addons 6.8.3 use manylinux_2_28 x86_64 wheels.
  CTranslate2 4.8.2 uses manylinux_2_27/_2_28 and has no mandatory cuDNN import.
  The initially evaluated 4.6.0 wheel failed this check. NumPy 2.2.6 uses
  manylinux_2_17; SentencePiece 0.2.1
  supports manylinux_2_28. PyInstaller 6.16.0 preserves onedir and Qt hooks.
- Audit every packaged ELF using file, readelf and ldd. Imported version needs
  (not exported version definitions) determine the maximum required GLIBC.
  Private/unknown GLIBC ABI requirements, external symlinks, missing libraries,
  wrong architectures and bundled GLIBC cause failure. Reports include hashes
  and dependency resolution per file. Wheel tags alone are not acceptance.
- The spec retains QML/assets/Inter/logo, WebEngine resources/helper, Qt
  Multimedia and translation binaries. No GLIBC replacement is shipped.
- Qt 6.8 requires OpenSSL 3 for HTTPS, while Focal supplies OpenSSL 1.1.1.
  OpenSSL 3.5.9 LTS is source-built on Focal with a verified upstream SHA-256,
  and its two shared libraries and license are explicitly collected. Python
  retains its Focal-built SSL extension. Both source and frozen smoke checks
  require an available Qt TLS backend; GLIBC auditing includes OpenSSL too.
- Rename the private QML loader id `native` to `bufferedLoader`: Qt 6.8 parses
  the former as a reserved JavaScript keyword. Slots, signals, object names,
  artwork and layout remain unchanged.

## Validation boundaries

`build-linux.sh` performs lint, formatting, pytest, PyInstaller, a full ELF audit,
packaged video/startup/restart checks under Xvfb, packaging and SHA-256 generation.
GitHub Actions tests that same artifact in separate 20.04, 22.04 and 24.04 runtime
containers. Test users are unprivileged; Chromium sandbox remains enabled.
Linux UI tests collect native Qt stderr instead of a Python Qt message callback:
Qt 6.8's asynchronous QML loading can deadlock that callback while a Python
property update owns the GIL. Diagnostics are still checked for QML errors.
Tests include installation in a HOME with spaces, updates removing obsolete
runtime files, desktop-file validation and actual gio desktop launch, and
uninstallation retaining personal data. The runtime containers have no project
Python dependencies; system Python is used only by the external test harness.

The existing playback smoke uses a silent AVI. It verifies video decoding, not
audible audio. Source UI/control checks, audio fixtures and live provider checks
are reported separately. Xvfb cannot establish hardware GPU/HDMI/speaker support.
TMDB needs a user-supplied credential; never embed one in a build or CI.

Build artifacts are candidates, not automatic stable Releases. Publish stable
only after reviewing the three runtime jobs and live integration/audio evidence.
If any acceptance checks remain incomplete, publish verified source and CI
artifacts and clearly label any GitHub Release as a prerelease.

## References

- [PyInstaller Linux portability](https://pyinstaller.org/en/stable/usage.html#making-gnu-linux-apps-forward-compatible)
- [Qt 6.8 supported platforms](https://doc.qt.io/qt-6.8/supported-platforms.html)
- [CPython 3.12.15](https://www.python.org/downloads/release/python-31215/)
- [Ubuntu snapshot service](https://snapshot.ubuntu.com/)

Actual run results are recorded in the release notes and attached audit reports;
the target matrix above is not itself evidence of a successful run.
