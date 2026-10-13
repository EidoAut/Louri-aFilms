#!/usr/bin/env bash
set -euo pipefail
fail() { printf 'Erro: %s\n' "$*" >&2; exit 1; }
[[ $(uname -m) == x86_64 && $(uname -s) == Linux ]] || fail 'Precísase Linux x86_64.'
glibc=$(getconf GNU_LIBC_VERSION 2>/dev/null) || fail 'Non se detectou GLIBC.'
glibc=${glibc#glibc }
[[ $(printf '%s\n' 2.31 "$glibc" | sort -V | head -n1) == 2.31 ]] || fail 'Precísase GLIBC 2.31 ou posterior. Non substitúas GLIBC manualmente.'
[[ ${HOME:-} == /* && $HOME != / ]] || fail 'HOME non é válido.'
[[ $HOME != *$'\n'* && $HOME != *$'\r'* && $HOME != *$'\t'* ]] || fail 'HOME contén caracteres non admitidos.'
home=$(cd -- "$HOME" && pwd -P)
source_dir=$(cd -- "$(dirname -- "$0")" && pwd -P)
base="$home/.local/opt"
target="$base/lourinha-films"
applications="$home/.local/share/applications"
desktop="$applications/lourinha-films.desktop"
mkdir -p -- "$base" "$applications"
[[ $(realpath "$base") == "$base" && $(realpath "$applications") == "$applications" ]] || fail 'Os directorios de instalación non poden ser ligazóns simbólicas.'
[[ ! -L $target && ! -L $desktop ]] || fail 'O destino é unha ligazón simbólica.'
[[ -x $source_dir/lourihna_films && -d $source_dir/_internal ]] || fail 'Paquete incompleto: falta o executable ou _internal.'
[[ -f $source_dir/_internal/lourihna_films/assets/logo.png && -f $source_dir/BUILD-INFO.json && -f $source_dir/uninstall.sh ]] || fail 'Paquete incompleto: faltan recursos.'
if [[ -e $target ]]; then
    [[ -f $target/.lourinha-managed && $(cat "$target/.lourinha-managed") == 'LourinhaFilms installer v1' ]] || fail 'O destino existente non pertence a este instalador.'
fi
if [[ -e $desktop ]]; then
    grep -qx 'X-LourinhaFilms-Managed=true' "$desktop" || fail 'O acceso directo existente non pertence a este instalador.'
fi
for library in "$source_dir/_internal/libpython3.12.so.1.0" \
    "$source_dir/_internal/PySide6/Qt/lib/libQt6Core.so.6" \
    "$source_dir/_internal/PySide6/Qt/lib/libQt6Gui.so.6" \
    "$source_dir/_internal/PySide6/Qt/lib/libQt6Multimedia.so.6" \
    "$source_dir/_internal/PySide6/Qt/lib/libQt6WebEngineCore.so.6" \
    "$source_dir/_internal/PySide6/Qt/plugins/platforms/libqxcb.so"; do
    [[ -f $library ]] || fail "Falta a biblioteca: $library"
    dependencies=$(LC_ALL=C LD_LIBRARY_PATH="$source_dir/_internal:$source_dir/_internal/PySide6/Qt/lib" ldd "$library" 2>&1) || fail "$dependencies"
    [[ $dependencies != *'not found'* ]] || fail "$dependencies"
done
stage=$(mktemp -d "$base/.lourinha-stage.XXXXXX")
backup=''
cleanup() {
    rm -rf -- "$stage"
    if [[ -n $backup && -d $backup && ! -e $target ]]; then mv -- "$backup" "$target"; fi
}
trap cleanup EXIT
cp -a -- "$source_dir/." "$stage/"
chmod +x "$stage/lourihna_films" "$stage/install.sh" "$stage/uninstall.sh"
printf '%s\n' 'LourinhaFilms installer v1' > "$stage/.lourinha-managed"
if [[ -d $target ]]; then
    backup=$(mktemp -d "$base/.lourinha-backup.XXXXXX")
    rmdir -- "$backup"
    mv -- "$target" "$backup"
fi
mv -- "$stage" "$target"
# Desktop Exec uses its own quoting rules, separate from shell quoting.
exec_path=$(printf '%s' "$target/lourihna_films" | sed 's/\\/\\\\\\\\/g; s/"/\\\\"/g; s/`/\\\\`/g; s/\$/\\\\$/g; s/%/%%/g')
icon_path=$(printf '%s' "$target/_internal/lourihna_films/assets/logo.png" | sed 's/\\/\\\\/g; s/ /\\s/g')
cat > "$desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Louriña Films
Exec="$exec_path"
Icon=$icon_path
Categories=AudioVideo;Video;
Terminal=false
X-LourinhaFilms-Managed=true
EOF
chmod 644 "$desktop"
if command -v update-desktop-database >/dev/null; then update-desktop-database "$applications"; fi
if [[ -n $backup ]]; then rm -rf -- "$backup"; fi
printf '%s\n' 'Louriña Films instalado. Ábreo desde o menú de aplicacións.' "Executable: $target/lourihna_films"
