#!/usr/bin/env bash
set -euo pipefail
# Resolve versions from the authenticated snapshot indices, then fetch the
# exact same bytes from Ubuntu's faster pool when they are still available.
# The snapshot remains the fallback for versions retired from the live pool.
manifest=$(mktemp)
trap 'rm -f -- "$manifest"' EXIT
apt-get -o Acquire::ForceHash=sha256 --print-uris --yes --download-only \
    --no-install-recommends install "$@" > "$manifest"
while read -r uri filename size digest; do
    [[ $uri == \'http* ]] || continue
    uri=${uri#\'}
    uri=${uri%\'}
    [[ $filename != */* && $filename == *.deb && $digest == SHA256:* ]] || exit 1
    hash=${digest#SHA256:}
    [[ $hash =~ ^[0-9a-f]{64}$ ]] || exit 1
    target="/var/cache/apt/archives/$filename"
    mirror=${uri/http:\/\/snapshot.ubuntu.com\/ubuntu\/20261001T000000Z/https:\/\/archive.ubuntu.com\/ubuntu}
    mirror=${mirror/https:\/\/snapshot.ubuntu.com\/ubuntu\/20261001T000000Z/https:\/\/archive.ubuntu.com\/ubuntu}
    verified=false
    for location in "$mirror" "$uri"; do
        if curl --fail --silent --show-error --location --retry 2 \
            --connect-timeout 15 --max-time 120 -o "$target" "$location" \
            && printf '%s  %s\n' "$hash" "$target" | sha256sum --check --status; then
            verified=true
            break
        fi
    done
    "$verified" || { printf 'Cannot verify %s\n' "$filename" >&2; exit 1; }
done < "$manifest"
apt-get install -y --no-install-recommends "$@"
