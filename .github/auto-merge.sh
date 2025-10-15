#!/usr/bin/env bash

set -u

PR_NUMBER_FROM_ARG="${1:-}"
PR_NUMBER_ENV="${PR_NUMBER:-}"

if [[ -n "$PR_NUMBER_FROM_ARG" ]]; then
  PR_NUMBER_VALUE="$PR_NUMBER_FROM_ARG"
else
  PR_NUMBER_VALUE="${PR_NUMBER_ENV:-}"
fi

if [[ -z "$PR_NUMBER_VALUE" ]]; then
  echo "No pull request number provided to auto-merge script." >&2
  exit 0
fi

if ! command -v gh >/dev/null 2>&1; then
  yay -Syu --noconfirm github-cli
fi

REPO_NAME_WITH_OWNER="${GITHUB_REPOSITORY:-}"
if [[ -z "$REPO_NAME_WITH_OWNER" ]]; then
  REPO_NAME_WITH_OWNER="$(gh repo view --json nameWithOwner --jq '.nameWithOwner')"
fi

MAX_POLL_ATTEMPTS=10
REACTION_DETECTED=0
RECENT_COMMENT_WINDOW_SECONDS=43200
RECENT_COMMENT_WINDOW_HOURS=$(( RECENT_COMMENT_WINDOW_SECONDS / 3600 ))

for (( attempt=1; attempt<=MAX_POLL_ATTEMPTS; attempt++ )); do
  remaining=$(( MAX_POLL_ATTEMPTS - attempt ))
  echo "[auto-merge] Attempt ${attempt}/${MAX_POLL_ATTEMPTS} - checking for approvals (remaining: ${remaining})."

  if ! pr_metadata_json="$(gh pr view "$PR_NUMBER_VALUE" --json comments)"; then
    echo "[auto-merge] Failed to fetch pull request metadata; aborting." >&2
    exit 1
  fi

  recent_comment_count="$(jq --argjson window "$RECENT_COMMENT_WINDOW_SECONDS" '[.comments[]? | select(.updatedAt != null or .createdAt != null) | ( .updatedAt // .createdAt ) as $timestamp | select((now - ($timestamp | fromdateiso8601)) <= $window)] | length' <<<"$pr_metadata_json")"
  if [[ -z "$recent_comment_count" || "$recent_comment_count" == "null" ]]; then
    recent_comment_count=0
  fi
  echo "[auto-merge] Detected ${recent_comment_count} recent comment(s) within the last ${RECENT_COMMENT_WINDOW_HOURS} hour(s)."
  if (( recent_comment_count > 0 )); then
    echo "[auto-merge] Detected recent comment activity; aborting auto-merge until reviewed." >&2
    exit 0
  fi

  plus_one_reactions="$(gh api \
    -H 'Accept: application/vnd.github.squirrel-girl-preview+json' \
    --jq 'map(select(.content == "+1")) | length' \
    "/repos/${REPO_NAME_WITH_OWNER}/issues/${PR_NUMBER_VALUE}/reactions")"

  echo "[auto-merge] Found ${plus_one_reactions} 👍 reaction(s)."

  if [[ "$plus_one_reactions" -gt 0 ]]; then
    REACTION_DETECTED=1
    break
  fi

  if (( attempt < MAX_POLL_ATTEMPTS )); then
    echo "[auto-merge] No 👍 reaction yet; sleeping 30 seconds before next check."
    sleep 30
  fi
done

if (( ! REACTION_DETECTED )); then
  echo "[auto-merge] No 👍 reaction detected after ${MAX_POLL_ATTEMPTS} checks; exiting without enabling auto-merge." >&2
  exit 0
fi

MAX_RETRIES=5
SUCCESS=0
for (( attempt=1; attempt<=MAX_RETRIES; attempt++ )); do
  if gh pr merge --merge --auto "$PR_NUMBER_VALUE"; then
    SUCCESS=1
    break
  fi
  echo "Attempt ${attempt} to enable auto-merge failed." >&2
  if (( attempt < MAX_RETRIES )); then
    sleep 15
  fi
done

if (( SUCCESS )); then
  echo "Successfully enabled auto-merge for PR #${PR_NUMBER_VALUE}."
else
  echo "Failed to enable auto-merge for PR #${PR_NUMBER_VALUE} after ${MAX_RETRIES} attempts." >&2
fi

exit 0
