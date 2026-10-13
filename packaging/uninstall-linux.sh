#!/usr/bin/env bash
set -euo pipefail
fail() { printf 'Erro: %s\n' "$*" >&2; exit 1; }
[[ ${HOME:-} == /* && $HOME != / ]] || fail 'HOME non é válido.'
home=$(cd -- "$HOME" && pwd -P)
target="$home/.local/opt/lourinha-films"
desktop="$home/.local/share/applications/lourinha-films.desktop"
if [[ -e $target || -L $target ]]; then
    [[ ! -L $target && $(realpath "$target") == "$target" ]] || fail 'Destino non seguro.'
    [[ -f $target/.lourinha-managed && $(cat "$target/.lourinha-managed") == 'LourinhaFilms installer v1' ]] || fail 'O destino non pertence a este instalador.'
    rm -rf -- "$target"
fi
if [[ -e $desktop || -L $desktop ]]; then
    [[ ! -L $desktop && $(realpath "$desktop") == "$desktop" ]] || fail 'Acceso directo non seguro.'
    grep -qx 'X-LourinhaFilms-Managed=true' "$desktop" || fail 'Acceso directo alleo á aplicación.'
    rm -- "$desktop"
fi
printf '%s\n' 'Louriña Films desinstalado. Conserváronse a biblioteca e os axustes persoais.'
