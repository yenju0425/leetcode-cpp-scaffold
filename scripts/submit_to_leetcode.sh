#!/bin/bash
# Submit changed solution files to LeetCode — one file per Python invocation.
# Usage: bash scripts/submit_to_leetcode.sh src/1_TwoSum/solution.h [...]

set -e

[ $# -eq 0 ] && { echo "Usage: $0 <solution.h> [...]"; exit 1; }

if [ ! -f "$HOME/.cache/leetcode-submit/storage_state.json" ]; then
  echo "❌ No saved session. Run: python scripts/submit_to_leetcode.py --save-session"
  exit 1
fi
echo "✅ Saved session found"
[ -n "$GH_USERNAME" ] && [ -n "$GH_PASSWORD" ] && echo "✅ GitHub credentials (fallback)"

derive_slug() {
  basename "$(dirname "$1")" \
    | sed 's/^[0-9]*_//; s/\([a-z0-9]\)\([A-Z]\)/\1-\2/g; s/\([A-Z]\)\([A-Z][a-z]\)/\1-\2/g' \
    | tr '[:upper:]' '[:lower:]'
}

for file in "$@"; do
  [ ! -f "$file" ] && { echo "❌ File not found: $file"; exit 1; }
done

echo -e "\nFiles to submit ($#):"
for file in "$@"; do echo "  - $file"; done

total=$# passed=0 failed=0

for file in "$@"; do
  slug=$(derive_slug "$file")
  echo -e "\n==========================================\n[$slug] $file\n=========================================="

  set +e
  python scripts/submit_to_leetcode.py \
    --problem-slug "$slug" --file "$file" \
    --screenshot-dir "${SCREENSHOT_DIR:-/tmp/leetcode-screenshots}"
  rc=$?
  set -e

  if [ $rc -eq 0 ]; then echo "✅ $slug: ALL ACCEPTED"; passed=$((passed + 1))
  else echo "❌ $slug: FAILED (exit $rc)"; failed=$((failed + 1)); fi
done

echo -e "\n==========================================\nResult: $passed/$total problems passed\n=========================================="
[ $failed -gt 0 ] && { echo "❌ $failed problem(s) failed"; exit 1; }
echo "✅ All problems passed!"
