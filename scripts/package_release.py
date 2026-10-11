# ==========================================================================
"""package_release.py
Export clean source and native portable releases without local profiles or Git data.
Validate file boundaries before writing archives; never publish to a remote service.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import shutil
import subprocess
import tarfile
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "artifacts",
    "build",
    "dist",
}
PRIVATE_SUFFIXES = {
    ".db",
    ".db3",
    ".sqlite",
    ".sqlite3",
    ".log",
    ".bak",
    ".pem",
    ".key",
    ".pyc",
}


def version() -> str:
    """Read the release version from the project metadata."""
    with (ROOT / "pyproject.toml").open("rb") as source:
        return tomllib.load(source)["project"]["version"]


def sensitive(path: Path) -> bool:
    """Recognize data and secret files that must never be distributed."""
    name = path.name.lower()
    return (
        path.suffix.lower() in PRIVATE_SUFFIXES
        or name.endswith((".db-wal", ".db-shm", ".sqlite-wal", ".sqlite-shm"))
        or (name.startswith(".env") and name != ".env.example")
    )


def source_files() -> list[Path]:
    """Select Git-eligible files, rejecting personal data and escaping symlinks."""
    raw = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
    )
    files = []
    for name in sorted(set(raw.decode("utf-8").split("\0")) - {""}):
        relative = Path(name)
        source = ROOT / relative
        if not source.exists():
            continue
        if source.is_symlink() or not source.resolve().is_relative_to(ROOT):
            raise ValueError(f"Source path is not a regular repository file: {name}")
        if set(relative.parts) & PRIVATE_PARTS or sensitive(relative):
            raise ValueError(f"Private/generated file is eligible for Git: {name}")
        files.append(relative)
    return files


def export_source(output: Path) -> Path:
    """Create a source ZIP from the current working tree, including untracked code."""
    files = source_files()
    destination = output / f"lourihna-films-{version()}-source.zip"
    with zipfile.ZipFile(
        destination, "w", zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for relative in files:
            archive.write(ROOT / relative, relative.as_posix())
    print(f"Source export: {len(files)} files; no profile or Git metadata")
    return destination


def package_runtime(runtime: Path, output: Path) -> Path:
    """Package a native PyInstaller runtime and attach rebuild metadata."""
    runtime = runtime.resolve()
    system = platform.system().lower()
    if system not in ("windows", "linux") or platform.machine().lower() not in (
        "amd64",
        "x86_64",
    ):
        raise ValueError(
            "This release supports native Windows/Linux x86_64 builds only"
        )
    executable = runtime / (
        "lourihna_films.exe" if system == "windows" else "lourihna_films"
    )
    if not executable.is_file() or not (runtime / "_internal").is_dir():
        raise ValueError("Expected a complete native PyInstaller runtime")
    for source in runtime.rglob("*"):
        # Certifi's public CA bundle is required for TLS, not a private key.
        if source.relative_to(runtime).as_posix() == "_internal/certifi/cacert.pem":
            if "PRIVATE KEY" in source.read_text(encoding="ascii"):
                raise ValueError("Unexpected private key in the public CA bundle")
            continue
        if source.is_file() and sensitive(source):
            raise ValueError(
                f"Private/generated runtime file: {source.relative_to(runtime)}"
            )
    for name in ("README.md", "LICENSE"):
        shutil.copy2(ROOT / name, runtime / name)
    if system == "linux":
        shutil.copy2(ROOT / "packaging/install-linux.sh", runtime / "install.sh")
        (runtime / "install.sh").chmod(0o755)
    metadata = {
        "version": version(),
        "system": system,
        "architecture": "x86_64",
        "python": platform.python_version(),
        "libc": platform.libc_ver(),
        "dependencies": {
            name: importlib.metadata.version(name)
            for name in (
                "PySide6",
                "httpx",
                "SQLAlchemy",
                "pydantic",
                "ctranslate2",
                "sentencepiece",
                "pyinstaller",
            )
        },
        "profile_included": False,
    }
    (runtime / "BUILD-INFO.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    stem = f"lourihna-films-{version()}-{system}-x86_64"
    if system == "windows":
        destination = output / f"{stem}-portable.zip"
        with zipfile.ZipFile(
            destination, "w", zipfile.ZIP_DEFLATED, compresslevel=6
        ) as archive:
            for source in sorted(runtime.rglob("*")):
                if source.is_file():
                    archive.write(
                        source,
                        "lourihna_films/" + source.relative_to(runtime).as_posix(),
                    )
    else:
        destination = output / f"{stem}.tar.gz"
        with tarfile.open(destination, "w:gz", compresslevel=6) as archive:
            archive.add(runtime, arcname="lourihna_films")
    return destination


def checksums(output: Path) -> None:
    """Write hashes of release archives/installers without including this hash file."""
    lines = []
    for path in sorted(output.iterdir()):
        if path.is_file() and path.name.endswith((".zip", ".tar.gz", ".exe")):
            with path.open("rb") as source:
                digest = hashlib.file_digest(source, "sha256").hexdigest()
            lines.append(f"{digest}  {path.name}")
    (output / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    """Validate and package only the explicitly selected release inputs."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", action="store_true")
    parser.add_argument("--check-source", action="store_true")
    parser.add_argument("--runtime", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "dist/packages")
    args = parser.parse_args()
    if args.check_source:
        print(
            f"PASS: {len(source_files())} Git-eligible files contain no local data files"
        )
    args.output.mkdir(parents=True, exist_ok=True)
    if args.source:
        print(export_source(args.output))
    if args.runtime:
        print(package_runtime(args.runtime, args.output))
    if args.source or args.runtime:
        checksums(args.output)


if __name__ == "__main__":
    main()
