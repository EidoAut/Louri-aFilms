# Preparing a release

Build on the target operating system. Windows executables are not Linux binaries.
The Linux workflow uses Ubuntu 24.04 x86_64; keep that baseline when producing
portable archives. Record a different baseline explicitly if it changes.

1. Update `pyproject.toml`, `main.py`, the Settings version label and the default
   version in `packaging/windows.iss` together. Write release notes in Galician.
2. Run Ruff, pytest, actual QML checks and native playback controls in an isolated
   profile. Use no provider credentials or private profile data in CI.
3. Run `python scripts/package_release.py --check-source`. Review `git diff` and
   `git status`; a successful file-name check does not replace reviewing content
   for credentials. `.env.example` must contain no actual values.
4. Build with `python -m PyInstaller --noconfirm lourihna_films.spec` and run
   `python scripts/verify_executable.py <native-executable>`. On headless Linux,
   use Xvfb and the library list in `.github/workflows/build.yml`.
5. Run `python scripts/package_release.py --runtime dist/lourihna_films` on each
   native platform. This writes a portable archive, build metadata and hashes.
   For Windows installers, run Inno Setup on `packaging/windows.iss` first.
   `/DAppSource=<absolute-runtime-directory>` selects a non-default build.
6. Export the reviewed working tree with `python scripts/package_release.py
   --source`. This includes untracked, non-ignored source files; review and commit
   those files before tagging. It excludes Git metadata and rejects eligible
   database, log and secret files.
7. Combine the native archives, optional installer and source ZIP in one release
   directory. Recompute `SHA256SUMS.txt` for that directory, and verify each hash.
8. Review the exact release notes and artifacts before publishing. Do not claim
   an installer exists if only a portable archive was built. Distinguish headless
   Linux validation from testing desktop audio or a physical HDMI television.

The build workflow has read-only repository permissions and uploads workflow
artifacts. It does not push code, create tags or publish GitHub Releases. Publishing
is a separate explicit step. Runtime profiles and older local backups are never
part of the source export or portable packages.

The history-management interface is unrelated to release cleanup. A fresh release
creates its own database at startup. Existing installations keep their data unless
the user explicitly resets their local profile.
