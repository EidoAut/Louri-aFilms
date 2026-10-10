# ==========================================================================
"""verify_translation.py
Check packaged local translation with installed models and no Python on PATH.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations


def main() -> None:
    """Run this isolated verification command only when explicitly invoked."""
    import json
    import os
    import subprocess
    import sys
    import tempfile
    from pathlib import Path

    executable = Path(sys.argv[1]).resolve()
    models = Path(sys.argv[2]).resolve()
    with tempfile.TemporaryDirectory(
        prefix="lourihna_films-translation-check-"
    ) as directory:
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
        environment["PATH"] = (
            str(Path(environment.get("SYSTEMROOT", "C:/Windows")) / "System32")
            if os.name == "nt"
            else "/usr/bin:/bin"
        )
        for language in ("es", "gl"):
            output = Path(directory) / (language + ".json")
            result = subprocess.run(
                [
                    str(executable),
                    "--smoke-translation",
                    str(models / ("en-" + language)),
                    str(output),
                ],
                env=environment,
                cwd=directory,
                capture_output=True,
                timeout=60,
            )
            data = (
                json.loads(output.read_text(encoding="utf-8"))
                if output.exists()
                else {}
            )
            assert result.returncode == 0 and data.get("translation"), data
            assert (
                data["translation"]
                != "A young woman returns home and discovers a secret."
            )
            print(language + ": " + data["translation"], flush=True)
    print("PASS: packaged Spanish and Galician local translation.")


if __name__ == "__main__":
    main()
