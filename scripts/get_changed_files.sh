#!/bin/bash
# Get changed solution.h files from git diff.
# Outputs one file path per line to stdout (no temp files).
#
# Usage:
#   # In CI (auto-detects PR vs push):
#   bash scripts/get_changed_files.sh
#
#   # Explicit mode:
#   bash scripts/get_changed_files.sh pull_request main
#
#   # Pipe to submit script:
#   bash scripts/get_changed_files.sh | xargs bash scripts/submit_to_leetcode.sh

set -e

EVENT_NAME="${1:-$GITHUB_EVENT_NAME}"
BASE_REF="${2:-$GITHUB_BASE_REF}"

changed_files=""

if [ "$EVENT_NAME" = "pull_request" ]; then
  git fetch origin "$BASE_REF" 2>/dev/null || true
  changed_files=$(git diff "origin/$BASE_REF...HEAD" --name-only 2>/dev/null || find src -name "solution.h")
else
  if git rev-parse HEAD~1 >/dev/null 2>&1; then
    changed_files=$(git diff HEAD~1 HEAD --name-only 2>/dev/null || find src -name "solution.h")
  else
    changed_files=$(find src -name "solution.h")
  fi
fi

# Filter to only solution.h files and output to stdout
echo "$changed_files" | grep 'solution\.h$' || true
