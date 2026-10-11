# ==========================================================================
"""verify_executable.py
Smoke-test a native portable build without Python on PATH or personal data.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations


def main() -> None:
    """Run this isolated verification command only when explicitly invoked."""
    import os
    import sqlite3
    import subprocess
    import sys
    import tempfile
    from contextlib import closing
    from pathlib import Path

    from video_fixture import write_video_fixture

    executable = (
        Path(sys.argv[1]).resolve()
        if len(sys.argv) > 1
        else Path(__file__).resolve().parents[2] / "Aplicacion" / "lourihna_films.exe"
    )
    with tempfile.TemporaryDirectory(
        prefix="lourihna_films-portable-check-"
    ) as directory:
        fixture = Path(directory) / "fixture.avi"
        write_video_fixture(fixture)
        environment = os.environ.copy()
        for name in (
            "PYTHONPATH",
            "PYTHONHOME",
            "VIRTUAL_ENV",
            "TMDB_TOKEN",
            "TMDB_API_KEY",
            "BRAVE_SEARCH_API_KEY",
        ):
            environment.pop(name, None)
        if os.name == "nt":
            windows = environment.get("SYSTEMROOT", r"C:\Windows")
            environment["PATH"] = str(Path(windows) / "System32") + ";" + windows
        else:
            environment["PATH"] = "/usr/bin:/bin"
        environment["LOURIHNA_FILMS_DATA_DIR"] = directory
        startup = None
        if os.name == "nt":
            startup = subprocess.STARTUPINFO()
            startup.dwFlags = subprocess.STARTF_USESHOWWINDOW
            startup.wShowWindow = 0
        result = subprocess.run(
            [str(executable), "--smoke-test", "--smoke-media", str(fixture)],
            cwd=directory,
            env=environment,
            capture_output=True,
            timeout=60,
            startupinfo=startup,
        )
        assert result.returncode == 0, result.stderr.decode(errors="replace")
        timings = [
            int(line.split("=", 1)[1])
            for line in result.stdout.decode(errors="replace").splitlines()
            if line.startswith("SPLASH_READY_MS=")
        ]
        assert timings and timings[0] >= 3000, (
            "Packaged welcome ended before three seconds"
        )
        database = Path(directory) / "lourihna_films.db"
        assert database.is_file(), "Application did not create its isolated database"
        with closing(sqlite3.connect(database)) as connection:
            assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        log = (Path(directory) / "lourihna_films.log").read_text(encoding="utf-8")
        assert not log.strip(), log
        with closing(sqlite3.connect(database)) as connection:
            connection.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("ui_language", "gl"),
            )
            connection.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("tmdb_token", "dpapi:a"),
            )
            connection.commit()
        restarted = subprocess.run(
            [str(executable), "--smoke-test"],
            cwd=directory,
            env=environment,
            capture_output=True,
            timeout=60,
            startupinfo=startup,
        )
        assert restarted.returncode == 0, restarted.stderr.decode(errors="replace")
        with closing(sqlite3.connect(database)) as connection:
            assert (
                connection.execute(
                    "SELECT value FROM settings WHERE key = 'ui_language'"
                ).fetchone()[0]
                == "gl"
            )
        assert (
            not (Path(directory) / "lourihna_films.log")
            .read_text(encoding="utf-8")
            .strip()
        )
        print(
            "PASS: preferences survived packaged restart with a malformed credential."
        )
        print(
            "PASS: packaged startup, native buffered playback, browser lifecycle, SQLite integrity and clean shutdown."
        )


if __name__ == "__main__":
    main()
