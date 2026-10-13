# ==========================================================================
"""verify_linux_elf.py
Audit every shipped ELF and its resolved dependencies before Linux packaging.
Write evidence and reject unsupported or unresolved binaries.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

LIMIT = (2, 31)
GLIBC_FILES = re.compile(r"^(lib(c|m|pthread|dl|rt|resolv|util)\.so|ld-linux)")


def required_glibc(version_info: str) -> tuple[int, ...]:
    """Read imported GLIBC versions, excluding symbols defined by the library."""
    needs = version_info.partition("Version needs section")[2]
    versions = [
        tuple(map(int, value.split(".")))
        for value in re.findall(r"Name: GLIBC_([0-9.]+)", needs)
    ]
    if "GLIBC_PRIVATE" in needs or "GLIBC_ABI_" in needs:
        raise ValueError("Unsupported private or ABI-level GLIBC dependency")
    return max(versions, default=(0, 0))


def audit(runtime: Path) -> dict:
    """Inspect trusted build outputs only; ldd must not run on untrusted binaries."""
    runtime = runtime.resolve(strict=True)
    binaries = []
    for path in sorted(runtime.rglob("*")):
        if path.is_symlink() and not path.resolve().is_relative_to(runtime):
            raise ValueError(f"Runtime symlink escapes package: {path}")
        if path.is_file() and not path.is_symlink():
            with path.open("rb") as source:
                if source.read(4) == b"\x7fELF":
                    binaries.append(path)
    if not binaries or not (runtime / "lourihna_films").is_file():
        raise ValueError("No complete Linux runtime found")
    environment = {**os.environ, "LC_ALL": "C"}
    environment["LD_LIBRARY_PATH"] = ":".join(
        [str(runtime / "_internal")] + sorted({str(path.parent) for path in binaries})
    )
    records, errors = [], []
    for path in binaries:
        name = path.relative_to(runtime).as_posix()
        description = subprocess.check_output(
            ["file", "-b", str(path)], text=True, env=environment
        ).strip()
        header = subprocess.check_output(
            ["readelf", "-h", str(path)], text=True, env=environment
        )
        if "ELF64" not in header or "Advanced Micro Devices X86-64" not in header:
            errors.append(f"{name}: wrong architecture")
        if GLIBC_FILES.match(path.name):
            errors.append(f"{name}: bundled GLIBC is forbidden")
        versions = subprocess.check_output(
            ["readelf", "--version-info", "--wide", str(path)],
            text=True,
            env=environment,
        )
        try:
            required = required_glibc(versions)
        except ValueError as exc:
            errors.append(f"{name}: {exc}")
            required = (999, 0)
        if required > LIMIT:
            errors.append(f"{name}: requires GLIBC {'.'.join(map(str, required))}")
        linked = subprocess.run(
            ["ldd", str(path)], text=True, capture_output=True, env=environment
        )
        dependencies = linked.stdout + linked.stderr
        if "not found" in dependencies or (
            linked.returncode and "statically linked" not in dependencies
        ):
            errors.append(f"{name}: unresolved dependencies: {dependencies.strip()}")
        records.append(
            {
                "path": name,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "file": description,
                "glibc_required": ".".join(map(str, required)),
                "ldd": dependencies.strip().splitlines(),
            }
        )
    maximum = max(
        tuple(map(int, item["glibc_required"].split("."))) for item in records
    )
    return {
        "passed": not errors,
        "architecture": "x86_64",
        "glibc_limit": "2.31",
        "glibc_max_required": ".".join(map(str, maximum)),
        "elf_count": len(records),
        "errors": errors,
        "files": records,
    }


def main() -> None:
    """Fail on unsupported shipped ELF, retaining the audit report."""
    parser = argparse.ArgumentParser()
    parser.add_argument("runtime", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = audit(args.runtime)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        f"ELF audit: {report['elf_count']} files; GLIBC {report['glibc_max_required']}"
    )
    for error in report["errors"]:
        print(error)
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
