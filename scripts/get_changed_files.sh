#!/bin/bash
# Get changed solution files for submission

set -e

EVENT_NAME="${1:-$GITHUB_EVENT_NAME}"
BASE_REF="${2:-$GITHUB_BASE_REF}"

echo "Finding changed files..."

if [ "$EVENT_NAME" = "pull_request" ]; then
  git fetch origin "$BASE_REF" || true
  git diff "origin/$BASE_REF...HEAD" --name-only > /tmp/changed_files.txt 2>/dev/null || find src -name "solution.h" > /tmp/changed_files.txt
else
  if git rev-parse HEAD~1 >/dev/null 2>&1; then
    git diff HEAD~1 HEAD --name-only > /tmp/changed_files.txt 2>/dev/null || find src -name "solution.h" > /tmp/changed_files.txt
  else
    find src -name "solution.h" > /tmp/changed_files.txt
  fi
fi

echo "Changed files:"
cat /tmp/changed_files.txt
