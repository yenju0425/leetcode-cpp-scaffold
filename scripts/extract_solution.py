#!/usr/bin/env python3
"""
Extract Solution classes from solution.h for LeetCode submission.

Handles:
- Multiple namespaces (baseline, recursive, etc.)
- Removes local includes (#include <util/leetcode.h>)
- Extracts clean Solution class for LeetCode

Usage:
    python scripts/extract_solution.py solution.h              # Extract baseline
    python scripts/extract_solution.py solution.h --all        # List all namespaces
    python scripts/extract_solution.py solution.h --ns bfs     # Extract specific namespace
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Dict, Optional


def extract_namespaces(content: str) -> Dict[str, str]:
    """Extract all namespace blocks from solution.h"""
    namespaces = {}

    # Pattern to match namespace blocks
    # namespace name { ... }
    pattern = r'namespace\s+(\w+)\s*\{(.*?)\}\s*//\s*namespace\s+\1'

    matches = re.findall(pattern, content, re.DOTALL)

    for name, body in matches:
        namespaces[name] = body.strip()

    return namespaces


def extract_solution_class(namespace_body: str) -> Optional[str]:
    """Extract the Solution class from namespace body."""
    # Find class Solution { ... };
    # Need to handle nested braces

    match = re.search(r'class\s+Solution\s*\{', namespace_body)
    if not match:
        return None

    start = match.start()

    # Find matching closing brace
    brace_count = 0
    end = match.end() - 1  # Position of opening brace

    for i in range(match.end() - 1, len(namespace_body)):
        if namespace_body[i] == '{':
            brace_count += 1
        elif namespace_body[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                end = i + 1
                break

    # Include trailing semicolon if present
    if end < len(namespace_body) and namespace_body[end] == ';':
        end += 1

    return namespace_body[start:end]


def clean_for_leetcode(solution_class: str, namespace_body: str) -> str:
    """
    Prepare code for LeetCode submission.
    - Add necessary includes/usings from namespace
    - Remove local includes
    """
    lines = []

    # Check if namespace uses std
    if 'using namespace std;' in namespace_body:
        lines.append('using namespace std;')
        lines.append('')

    # Add the Solution class
    lines.append(solution_class)

    return '\n'.join(lines)


def extract_all_solutions(filepath: str) -> Dict[str, str]:
    """Extract all solutions from a solution.h file."""
    content = Path(filepath).read_text(encoding='utf-8')

    # Remove local includes
    content = re.sub(r'#include\s*<util/[^>]+>', '', content)
    content = re.sub(r'#include\s*"[^"]*util[^"]*"', '', content)

    namespaces = extract_namespaces(content)

    solutions = {}
    for ns_name, ns_body in namespaces.items():
        solution_class = extract_solution_class(ns_body)
        if solution_class:
            clean_code = clean_for_leetcode(solution_class, ns_body)
            solutions[ns_name] = clean_code

    return solutions


def main():
    parser = argparse.ArgumentParser(
        description="Extract Solution classes from solution.h"
    )
    parser.add_argument(
        "filepath",
        help="Path to solution.h"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="List all available namespaces"
    )
    parser.add_argument(
        "--ns",
        type=str,
        default="baseline",
        help="Namespace to extract (default: baseline)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file (default: stdout)"
    )

    args = parser.parse_args()

    if not Path(args.filepath).exists():
        print(f"Error: File not found '{args.filepath}'", file=sys.stderr)
        sys.exit(1)

    solutions = extract_all_solutions(args.filepath)

    if not solutions:
        print("Error: No Solution classes found", file=sys.stderr)
        sys.exit(1)

    if args.all:
        print("Available namespaces:")
        for ns in solutions.keys():
            print(f"  - {ns}")
        sys.exit(0)

    if args.ns not in solutions:
        print(f"Error: Namespace '{args.ns}' not found", file=sys.stderr)
        print(f"Available: {', '.join(solutions.keys())}", file=sys.stderr)
        sys.exit(1)

    code = solutions[args.ns]

    if args.output:
        Path(args.output).write_text(code, encoding='utf-8')
        print(f"Extracted '{args.ns}' to {args.output}")
    else:
        print(code)


if __name__ == "__main__":
    main()
