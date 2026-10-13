#!/usr/bin/env bash
set -euo pipefail
package=/input/LourinhaFilms-linux-x86_64-glibc231.tar.gz
cd /input
sha256sum -c "$(basename "$package").sha256"
scratch=$(mktemp -d)
export HOME="$scratch/user home"
mkdir -p "$HOME"
tar -xzf "$package" -C "$scratch"
source_dir="$scratch/lourinha-films"
target="$HOME/.local/opt/lourinha-films"
desktop="$HOME/.local/share/applications/lourinha-films.desktop"
"$source_dir/install.sh"
test -x "$target/lourihna_films"
desktop-file-validate "$desktop"
test -f "$target/_internal/lourihna_films/assets/logo.png"
# Updating must remove obsolete runtime files while preserving user data.
mkdir -p "$HOME/.local/share/lourihna_films"
printf 'preserve me\n' > "$HOME/.local/share/lourihna_films/sentinel"
touch "$target/obsolete-file"
"$source_dir/install.sh"
test ! -e "$target/obsolete-file"
xvfb-run -a python3 /test/verify_executable.py "$target/lourihna_films"
# Launch the real desktop entry in an isolated graphical session.
export XDG_DATA_HOME="$HOME/.local/share"
export LOURIHNA_FILMS_DATA_DIR="$HOME/desktop-profile"
dbus-run-session -- xvfb-run -a bash -c '
    openbox >/dev/null 2>&1 &
    gio launch "$1"
    for attempt in $(seq 1 30); do
        if test -f "$LOURIHNA_FILMS_DATA_DIR/lourihna_films.db" && xwininfo -root -tree | grep -q "Louriña Films"; then
            printf "%s\n" "PASS: desktop entry started a visible application window"
            exit 0
        fi
        sleep 1
    done
    exit 1
' _ "$desktop"
"$target/uninstall.sh"
test ! -e "$target"
test ! -e "$desktop"
test -f "$HOME/.local/share/lourihna_films/sentinel"
printf '%s\n' 'PASS: extraction, checksum, install, update, desktop, runtime and uninstall'
