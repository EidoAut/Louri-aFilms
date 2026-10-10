#!/bin/sh
set -eu
source_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
target="$HOME/.local/opt/lourihna-films"
mkdir -p "$target" "$HOME/.local/share/applications"
cp -a "$source_dir/." "$target/"
chmod +x "$target/lourihna_films"
cat > "$HOME/.local/share/applications/lourihna-films.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Louriña Films
Exec="$target/lourihna_films"
Icon=$target/_internal/lourihna_films/assets/logo.png
Categories=AudioVideo;Video;
Terminal=false
EOF
printf '%s\n' 'Louriña Films instalado para o usuario actual.'
