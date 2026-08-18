#!/usr/bin/env bash
# Installs pinact (version from config/versions.env) into the given bin dir, verifying the release checksum.
set -euo pipefail
DEST="${1:-.venv/bin}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=/dev/null
set -a; . "$ROOT/config/versions.env"; set +a
os="$(uname -s | tr '[:upper:]' '[:lower:]')"
arch="$(uname -m)"; case "$arch" in x86_64) arch=amd64 ;; aarch64|arm64) arch=arm64 ;; esac
base="https://github.com/suzuki-shunsuke/pinact/releases/download/v${PINACT_VERSION}"
tarball="pinact_${os}_${arch}.tar.gz"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
curl -fsSL -o "$tmp/$tarball" "$base/$tarball"
curl -fsSL -o "$tmp/checksums.txt" "$base/pinact_${PINACT_VERSION}_checksums.txt"
(cd "$tmp" && grep " $tarball\$" checksums.txt | sha256sum -c -)
tar -xzf "$tmp/$tarball" -C "$tmp" pinact
mkdir -p "$DEST" && install -m 0755 "$tmp/pinact" "$DEST/pinact"
"$DEST/pinact" version
