#!/bin/bash
# Submit solutions to LeetCode

set -e

LEETCODE_USERNAME="${LEETCODE_USERNAME}"
LEETCODE_PASSWORD="${LEETCODE_PASSWORD}"

# Verify credentials
if [ -z "$LEETCODE_USERNAME" ] || [ -z "$LEETCODE_PASSWORD" ]; then
  echo "❌ LEETCODE_USERNAME or LEETCODE_PASSWORD not set!"
  exit 1
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
    
    if python scripts/submit_to_leetcode.py --problem-slug "$problem_slug" --file "$tmp_file" --lang "cpp" --screenshot-dir "${SCREENSHOT_DIR:-/tmp/leetcode-screenshots}"; then
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
