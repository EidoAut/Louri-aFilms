#!/usr/bin/env bash
set -euo pipefail
export PYTHONHASHSEED=0
python3.12 -m ruff check .
python3.12 -m ruff format --check .
QT_QPA_PLATFORM=offscreen python3.12 -m pytest -q
timeout 180s xvfb-run -a bash scripts/verify-linux-ui.sh
python3.12 scripts/collect_linux_licenses.py
python3.12 -m PyInstaller --clean --noconfirm lourihna_films.spec
python3.12 scripts/collect_linux_licenses.py dist/lourihna_films
mkdir -p dist/packages
python3.12 scripts/verify_linux_elf.py dist/lourihna_films --output dist/packages/ELF-AUDIT.json
xvfb-run -a python3.12 scripts/verify_executable.py dist/lourihna_films/lourihna_films
python3.12 -m scripts.package_release --runtime dist/lourihna_films
