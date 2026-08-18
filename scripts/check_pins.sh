#!/usr/bin/env bash
# Fails when config/versions.env has an unresolved image (no digest) or a placeholder.
set -euo pipefail
FILE="${1:-config/versions.env}"
rc=0
if grep -nE '<[a-z]+>' "$FILE"; then echo "placeholders left in $FILE" >&2; rc=1; fi
while IFS= read -r line; do
  [[ "$line" =~ ^[A-Z_]+_IMAGE= ]] || continue
  if ! [[ "$line" =~ ^[A-Z_]+_IMAGE=[a-z0-9./-]+:[A-Za-z0-9._-]+@sha256:[a-f0-9]{64}$ ]]; then
    echo "not pinned by digest: $line" >&2; rc=1
  fi
done < "$FILE"
exit $rc
