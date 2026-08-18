#!/usr/bin/env bash
# Appends @sha256:<digest> to every *_IMAGE entry of config/versions.env that lacks one.
# Uses docker buildx (present with Docker Desktop / CI); falls back to crane.
set -euo pipefail
FILE="${1:-config/versions.env}"
digest_of() {
  local ref="$1"
  if command -v docker >/dev/null 2>&1; then
    docker buildx imagetools inspect "$ref" --format '{{.Manifest.Digest}}'
  elif command -v crane >/dev/null 2>&1; then
    crane digest "$ref"
  else
    echo "need docker or crane to resolve $ref" >&2; exit 1
  fi
}
tmp="$(mktemp)"
while IFS= read -r line; do
  if [[ "$line" =~ ^([A-Z_]+_IMAGE)=([^@[:space:]]+)$ ]]; then
    ref="${BASH_REMATCH[2]}"
    d="$(digest_of "$ref")"
    echo "${BASH_REMATCH[1]}=${ref}@${d}"
  else
    echo "$line"
  fi
done < "$FILE" > "$tmp"
mv "$tmp" "$FILE"
grep -E '^[A-Z_]+_IMAGE=' "$FILE"
