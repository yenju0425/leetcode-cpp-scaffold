#!/bin/bash
# Submit solutions to LeetCode

set -e

LEETCODE_USERNAME="${LEETCODE_USERNAME}"
LEETCODE_PASSWORD="${LEETCODE_PASSWORD}"

# Check if we have saved session (storage state or cookies)
HAS_SESSION=false
if [ -f "$HOME/.cache/leetcode-submit/storage_state.json" ] || [ -f "$HOME/.cache/leetcode-submit/cookies.json" ]; then
  HAS_SESSION=true
  echo "✅ Saved session found, credentials are optional"
fi

# Verify credentials only if no saved session
if [ "$HAS_SESSION" = false ]; then
  if [ -z "$LEETCODE_USERNAME" ] || [ -z "$LEETCODE_PASSWORD" ]; then
    echo "❌ No saved session and no LEETCODE_USERNAME/LEETCODE_PASSWORD set!"
    echo "   Run: python scripts/submit_to_leetcode.py --save-session"
    exit 1
  fi
fi

submission_count=0
success_count=0

# Process all changed solution.h files
for file in $(cat /tmp/changed_files.txt | grep 'solution.h' || true); do
  problem_dir=$(dirname "$file")
  problem_name=$(basename "$problem_dir")
  problem_id=$(echo "$problem_name" | grep -oE '^[0-9]+' || echo "")
  
  [ -z "$problem_id" ] && { echo "❌ Cannot extract problem ID from: $problem_name"; exit 1; }
  
  problem_slug=$(echo "$problem_name" | sed 's/^[0-9]*_//' | sed 's/\([A-Z]\)/-\L\1/g' | sed 's/^-//')
  
  echo ""
  echo "=========================================="
  echo "[$problem_id] $problem_slug"
  echo "=========================================="
  
  solution_file="$problem_dir/solution.h"
  [ ! -f "$solution_file" ] && { echo "❌ Solution file not found"; exit 1; }
  
  namespaces=$(python scripts/extract_solution.py "$solution_file" --all 2>/dev/null | grep "^\s*-" | sed 's/.*- //' || true)
  [ -z "$namespaces" ] && { echo "❌ No namespaces found"; exit 1; }
  
  echo "Namespaces: $namespaces"
  
  for ns in $namespaces; do
    echo ""
    echo "--- Namespace: $ns ---"
    submission_count=$((submission_count + 1))
    
    tmp_file="/tmp/solution_${problem_id}_${ns}.cpp"
    python scripts/extract_solution.py "$solution_file" --ns "$ns" --output "$tmp_file" || { echo "❌ Extraction failed"; exit 1; }
    [ ! -f "$tmp_file" ] && { echo "❌ File not created"; exit 1; }
    
    # Build submit command (credentials are optional if session exists)
    SUBMIT_CMD="python scripts/submit_to_leetcode.py --problem-slug \"$problem_slug\" --file \"$tmp_file\" --lang \"cpp\" --screenshot-dir \"${SCREENSHOT_DIR:-/tmp/leetcode-screenshots}\""
    if [ -n "$LEETCODE_USERNAME" ] && [ -n "$LEETCODE_PASSWORD" ]; then
      SUBMIT_CMD="$SUBMIT_CMD --username \"$LEETCODE_USERNAME\" --password \"$LEETCODE_PASSWORD\""
    fi

    if eval $SUBMIT_CMD; then
      echo "✅ ACCEPTED"
      success_count=$((success_count + 1))
    else
      echo "❌ FAILED"
      exit 1
    fi
    
    sleep 3
  done
done

echo ""
echo "=========================================="
echo "Result: $success_count/$submission_count passed"
echo "=========================================="

[ "$submission_count" -eq 0 ] && { echo "❌ No solutions submitted"; exit 1; }
[ "$success_count" -ne "$submission_count" ] && { echo "❌ Some submissions failed"; exit 1; }

echo "✅ All submissions passed!"
