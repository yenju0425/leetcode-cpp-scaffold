#!/usr/bin/env python3
"""
LeetCode Problem Fetcher and Code Generator

DISCLAIMER: This tool is for personal study and educational use only.
Please respect LeetCode's Terms of Service and use responsibly.

Usage:
    python fetch.py <problem-slug>

Example:
    python fetch.py two-sum
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, List

import requests
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader


# ============================================================================
# Constants
# ============================================================================

LEETCODE_GRAPHQL = "https://leetcode.com/graphql"
LEETCODE_HOME = "https://leetcode.com/"

SCRIPT_DIR = Path(__file__).parent.resolve()
SRC_DIR = SCRIPT_DIR / "src"
TEMPLATES_DIR = SCRIPT_DIR / "templates"


# ============================================================================
# LeetCode Fetcher
# ============================================================================

def extract_examples_from_html(content_html: str) -> List[Dict[str, str]]:
    """Extract input/output examples from HTML content."""
    soup = BeautifulSoup(content_html, "html.parser")

    results = []
    pres = soup.find_all("pre")
    for p in pres:
        text = p.get_text()
        input_match = re.search(r"Input: (.+)", text)
        output_match = re.search(r"Output: (.+)", text)
        if input_match and output_match:
            results.append({
                "input": input_match.group(1).strip(),
                "output": output_match.group(1).strip(),
            })
    return results


def fetch_leetcode_question(slug: str, timeout: int = 20) -> Dict[str, Any]:
    """Fetch question data from LeetCode GraphQL API."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0",
    })

    session.get(LEETCODE_HOME, timeout=timeout)
    csrftoken = session.cookies.get("csrftoken", "")

    query = """
    query questionData($titleSlug: String!) {
      question(titleSlug: $titleSlug) {
        questionFrontendId
        title
        content
        exampleTestcases
      }
    }
    """

    payload = {
        "query": query,
        "variables": {"titleSlug": slug},
    }

    headers = {
        "Content-Type": "application/json",
        "Referer": f"https://leetcode.com/problems/{slug}/",
        "x-csrftoken": csrftoken,
    }

    resp = session.post(
        LEETCODE_GRAPHQL,
        json=payload,
        headers=headers,
        timeout=timeout,
    )
    resp.raise_for_status()

    data = resp.json()

    if "errors" in data:
        raise RuntimeError(f"LeetCode GraphQL error: {data['errors']}")

    return data


# ============================================================================
# Name Utilities
# ============================================================================

def to_upper_camel_case(title: str) -> str:
    """Convert title to UpperCamelCase (e.g., 'Two Sum' -> 'TwoSum')."""
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", title)
    words = cleaned.split()
    camel = "".join(word.capitalize() for word in words)
    return camel


def create_folder_name(problem_id: str, title: str) -> str:
    """Create folder name: {problem_id}_{TitleInCamelCase}."""
    camel_title = to_upper_camel_case(title)
    return f"{problem_id}_{camel_title}"


# ============================================================================
# Test Case Generation
# ============================================================================

def parse_value(value_str: str) -> Any:
    """Parse value string to Python type."""
    value_str = value_str.strip()

    try:
        return json.loads(value_str)
    except json.JSONDecodeError:
        pass

    # Handle unquoted strings and edge cases
    if value_str.lower() == "true":
        return True
    if value_str.lower() == "false":
        return False
    if value_str.lower() == "null":
        return None

    # Try to parse as int
    try:
        return int(value_str)
    except ValueError:
        pass

    # Try to parse as float
    try:
        return float(value_str)
    except ValueError:
        pass

    # Return as string (remove surrounding quotes if present)
    if (value_str.startswith('"') and value_str.endswith('"')) or \
       (value_str.startswith("'") and value_str.endswith("'")):
        return value_str[1:-1]

    return value_str


def parse_input_string(input_str: str) -> Dict[str, Any]:
    """Parse 'var1 = value1, var2 = value2' format into a dict."""
    result = {}
    i = 0
    while i < len(input_str):
        # Skip whitespace and commas
        while i < len(input_str) and input_str[i] in ' ,':
            i += 1

        if i >= len(input_str):
            break

        # Find the variable name (until '=')
        eq_pos = input_str.find('=', i)
        if eq_pos == -1:
            break

        var_name = input_str[i:eq_pos].strip()
        i = eq_pos + 1

        # Skip whitespace after '='
        while i < len(input_str) and input_str[i] == ' ':
            i += 1

        if i >= len(input_str):
            break

        # Now find the value - need to handle brackets and quotes
        value_start = i
        bracket_depth = 0
        in_string = False
        string_char = None

        while i < len(input_str):
            char = input_str[i]

            if in_string:
                if char == string_char and (i == 0 or input_str[i-1] != '\\'):
                    in_string = False
            else:
                if char in '"\'':
                    in_string = True
                    string_char = char
                elif char in '[{(':
                    bracket_depth += 1
                elif char in ']})':
                    bracket_depth -= 1
                elif char == ',' and bracket_depth == 0:
                    # End of this value
                    break

            i += 1

        value_str = input_str[value_start:i].strip()
        result[var_name] = parse_value(value_str)

    return result


def parse_example_testcases(example_testcases: str, content_html: str) -> List[Dict[str, Any]]:
    """Parse example testcases from HTML and generate test case dicts."""
    examples_from_html = extract_examples_from_html(content_html)

    test_cases = []
    for i, example in enumerate(examples_from_html, start=1):
        parsed_input = parse_input_string(example["input"])
        parsed_output = parse_value(example["output"])

        test_case = {
            "name": f"Example{i}",
            "input": parsed_input,
            "output": parsed_output,
        }
        test_cases.append(test_case)

    return test_cases


def generate_test_cases_json(test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate the test_cases.json structure."""
    return {
        "test_cases": test_cases
    }


# ============================================================================
# Code Generation
# ============================================================================

def generate_code_files(
    problem_dir: Path,
    problem_id: str,
    title: str,
    test_cases: List[Dict[str, Any]]
) -> None:
    """Generate solution.h, test.cpp, and test_cases.json from templates."""
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    camel_title = to_upper_camel_case(title)
    ctx = {
        "problem_id": problem_id,
        "title": title,
        "camel_title": camel_title,
        "test_case_struct_name": f"{camel_title}Case",
        "test_suite_name": f"{camel_title}ParamSuite",
    }

    solution_template = env.get_template("solution.h.jinja2")
    solution_path = problem_dir / "solution.h"
    with open(solution_path, "w") as f:
        f.write(solution_template.render(ctx))
    print(f"Generated: {solution_path}")

    test_template = env.get_template("test.cpp.jinja2")
    test_path = problem_dir / "test.cpp"
    with open(test_path, "w") as f:
        f.write(test_template.render(ctx))
    print(f"Generated: {test_path}")

    test_cases_json = generate_test_cases_json(test_cases)
    test_cases_path = problem_dir / "test_cases.json"
    with open(test_cases_path, "w") as f:
        json.dump(test_cases_json, f, indent=4)
    print(f"Generated: {test_cases_path}")


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Fetch LeetCode problem and generate C++ test boilerplate"
    )
    parser.add_argument(
        "slug",
        help="Problem slug (e.g., 'two-sum')"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without creating files"
    )

    args = parser.parse_args()
    slug = args.slug

    print(f"Fetching problem: {slug}")
    print("-" * 50)

    try:
        data = fetch_leetcode_question(slug)
    except Exception as e:
        print(f"Error fetching problem: {e}", file=sys.stderr)
        sys.exit(1)

    question = data.get("data", {}).get("question")
    if not question:
        print(f"Error: Could not find question data for '{slug}'", file=sys.stderr)
        sys.exit(1)

    problem_id = question.get("questionFrontendId", "0")
    title = question.get("title", slug)
    content = question.get("content", "")
    example_testcases = question.get("exampleTestcases", "")

    print(f"Problem ID: {problem_id}")
    print(f"Title: {title}")

    # Create folder name
    folder_name = create_folder_name(problem_id, title)
    problem_dir = SRC_DIR / folder_name

    print(f"Folder: {folder_name}")
    print("-" * 50)

    # Parse test cases
    test_cases = parse_example_testcases(example_testcases, content)
    print(f"Found {len(test_cases)} example test cases")

    if args.dry_run:
        print("\n[DRY RUN] Would create:")
        print(f"  - {problem_dir}/solution.h")
        print(f"  - {problem_dir}/test.cpp")
        print(f"  - {problem_dir}/test_cases.json")
        print("\nTest cases preview:")
        print(json.dumps(generate_test_cases_json(test_cases), indent=2))
        return

    # Create problem directory
    problem_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created directory: {problem_dir}")

    # Generate code files
    generate_code_files(problem_dir, problem_id, title, test_cases)

    print("-" * 50)
    print("Done!")


if __name__ == "__main__":
    main()
