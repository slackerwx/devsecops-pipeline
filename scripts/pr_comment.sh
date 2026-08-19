#!/usr/bin/env bash
# Create or update the sticky PR comment identified by MARKER. Needs GH_TOKEN with pull-requests: write.
set -euo pipefail
FILE="$1"; MARKER="$2"
: "${GITHUB_REPOSITORY:?}" "${PR_NUMBER:?}"
existing="$(gh api "repos/${GITHUB_REPOSITORY}/issues/${PR_NUMBER}/comments" --paginate \
  --jq ".[] | select(.body | contains(\"${MARKER}\")) | .id" 2>/dev/null | head -n1 || true)"
if [ -n "$existing" ]; then
  if gh api -X PATCH "repos/${GITHUB_REPOSITORY}/issues/comments/${existing}" -F body=@"$FILE" >/dev/null; then
    echo "pr comment updated (#$existing)"
  else
    echo "::notice::could not update the PR comment (token lacks pull-requests: write?)"
  fi
elif gh api -X POST "repos/${GITHUB_REPOSITORY}/issues/${PR_NUMBER}/comments" -F body=@"$FILE" >/dev/null; then
  echo "pr comment created"
else
  echo "::notice::could not create the PR comment (token lacks pull-requests: write?)"
fi
