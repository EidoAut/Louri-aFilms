#!/usr/bin/env bash
set -euo pipefail
export XDG_RUNTIME_DIR
XDG_RUNTIME_DIR=$(mktemp -d)
chmod 700 "$XDG_RUNTIME_DIR"
pulseaudio --start --exit-idle-time=-1
pactl load-module module-null-sink sink_name=lourinha_test >/dev/null
openbox >/dev/null 2>&1 &
window_manager=$!
trap 'kill "$window_manager"; pulseaudio --kill' EXIT
python3.12 scripts/verify_linux_audio.py
python3.12 scripts/verify_controls.py
mkdir -p artifacts
python3.12 scripts/verify_ui.py --compact --stress-explore --native-qt-logging 2>&1 | tee artifacts/linux-ui.log
if grep -E 'Error:|Unexpected token|is not a type|Cannot assign|failed to load component|Unable to assign|not assigned a valid texture|Cannot open:|Binding loop detected' artifacts/linux-ui.log; then
    echo 'QML diagnostics failed' >&2
    exit 1
fi
