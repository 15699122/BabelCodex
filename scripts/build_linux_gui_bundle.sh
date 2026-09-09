#!/usr/bin/env bash
set -euo pipefail

# Build the Linux desktop bundle only after the target-triple sidecar is present.
# The binary itself is supplied by the caller (default prefers the controlled
# `scripts/babelcodex-service.spec` build output, falling back to the venv
# console script) so this script never downloads, executes, or discovers an
# arbitrary executable.

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
if [[ -f "$repo_root/dist/babelcodex-service" ]]; then
  sidecar_source="${1:-$repo_root/dist/babelcodex-service}"
else
  sidecar_source="${1:-$repo_root/.venv/bin/babelcodex-service}"
fi
sidecar_target="$repo_root/gui/src-tauri/binaries/babelcodex-service-x86_64-unknown-linux-gnu"

if [[ ! -f "$sidecar_source" ]]; then
  echo "missing Linux sidecar: $sidecar_source" >&2
  exit 2
fi

mkdir -p "$(dirname "$sidecar_target")"
install -m 0755 "$sidecar_source" "$sidecar_target"
cleanup() { rm -f "$sidecar_target"; }
trap cleanup EXIT

cd "$repo_root/gui"
npm ci
npm test -- --run
npm run build
npm run tauri -- build --bundles deb,appimage

echo "Linux GUI bundle build completed."