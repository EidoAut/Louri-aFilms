#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
image=lourinha-films-builder:glibc231
source_commit=$(git rev-parse HEAD)
source_dirty=$(test -z "$(git status --porcelain)" && echo false || echo true)
source_epoch=$(git show -s --format=%ct HEAD)
docker build --platform linux/amd64 -f packaging/Dockerfile.linux -t "$image" .
mkdir -p dist/linux-glibc231
container=$(docker create --platform linux/amd64 --shm-size=512m \
    -e SOURCE_COMMIT="$source_commit" \
    -e SOURCE_DIRTY="$source_dirty" \
    -e SOURCE_DATE_EPOCH="$source_epoch" "$image")
finish() {
    docker logs "$container" > dist/linux-glibc231/build.log 2>&1
    docker rm -f "$container" >/dev/null
}
trap finish EXIT
docker start -a "$container"
test "$(docker inspect -f '{{.State.ExitCode}}' "$container")" = 0
docker cp "$container:/work/dist/packages/." dist/linux-glibc231/
printf '%s\n' 'Paquetes e informes: dist/linux-glibc231/'
