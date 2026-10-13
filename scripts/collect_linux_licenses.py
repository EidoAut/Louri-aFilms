# ==========================================================================
"""collect_linux_licenses.py
Retain license notices from the exact Linux wheel environment used for builds.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

import importlib.metadata
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> None:
    """Copy installed distribution notices without replacing historical notices."""
    if len(sys.argv) == 2:
        collect_system_notices(Path(sys.argv[1]))
        return
    target = Path("docs/licenses/linux-wheels")
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2("/opt/openssl/LICENSE.txt", target / "OpenSSL-3.5.9-LICENSE.txt")
    for distribution in importlib.metadata.distributions():
        for relative in distribution.files or []:
            if any(
                word in relative.name.lower()
                for word in ("license", "copying", "copyright", "authors", "notice")
            ):
                source = Path(distribution.locate_file(relative))
                if not source.is_file() or source.suffix in (".py", ".pyc", ".so"):
                    continue
                name = (
                    distribution.metadata["Name"]
                    + "-"
                    + str(relative).replace("/", "_")
                )
                shutil.copy2(source, target / name)


def collect_system_notices(runtime: Path) -> None:
    """Retain Ubuntu copyright notices for native libraries copied into runtime."""
    target = runtime / "_internal/licenses/linux-system"
    target.mkdir(parents=True, exist_ok=True)
    packages = set()
    for name in sorted({path.name for path in runtime.rglob("*.so*")}):
        result = subprocess.run(
            ["dpkg-query", "-S", "*/" + name], capture_output=True, text=True
        )
        for line in result.stdout.splitlines():
            package = line.split(": ", 1)[0].split(":", 1)[0]
            if package not in packages:
                source = Path("/usr/share/doc") / package / "copyright"
                if source.is_file():
                    shutil.copy2(source, target / (package + "-copyright"))
                    packages.add(package)


if __name__ == "__main__":
    main()
