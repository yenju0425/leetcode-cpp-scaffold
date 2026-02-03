#!/usr/bin/env python3
"""
LeetCode Solution Submitter using Playwright

Automatically submit solutions via browser automation.
Avoids API changes by simulating user interactions.

Usage:
    python submit_to_leetcode.py --problem-id 1 --file solution.cpp --lang cpp17
    python submit_to_leetcode.py --problem-slug two-sum --file solution.py --lang python3
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright


# ============================================================================
# Configuration
# ============================================================================

# Load from environment variables: LEETCODE_USERNAME, LEETCODE_PASSWORD
LEETCODE_USERNAME = ""
LEETCODE_PASSWORD = ""

# ============================================================================
# Language Mapping
# ============================================================================

LANG_TO_LEETCODE = {
    "python": "python",
    "python3": "python3",
    "cpp": "cpp",
    "cpp11": "cpp11",
    "cpp14": "cpp14",
    "cpp17": "cpp17",
    "cpp20": "cpp20",
    "c": "c",
    "java": "java",
    "javascript": "javascript",
    "typescript": "typescript",
    "go": "golang",
    "rust": "rust",
    "kotlin": "kotlin",
    "swift": "swift",
    "scala": "scala",
    "php": "php",
    "ruby": "ruby",
}


# ============================================================================
# Helper Functions
# ============================================================================

def wait_for_element(page, selector, timeout=10000):
    """Wait for element to appear."""
    try:
        page.wait_for_selector(selector, timeout=timeout)
        return True
    except:
        return False


def submit_solution(
    username: str,
    password: str,
    problem_slug: str,
    code: str,
    lang: str,
    headless: bool = True,
) -> bool:
    """
    Submit solution to LeetCode using Playwright.
    
    Returns:
        bool: True if Accepted, False otherwise
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()

        try:
            print("[1/5] Visiting LeetCode...")
            page.goto("https://leetcode.com/", wait_until="domcontentloaded")
            time.sleep(2)

            # Check if already logged in
            is_logged_in = False
            try:
                page.goto("https://leetcode.com/profile/",
                          wait_until="domcontentloaded", timeout=5000)
                is_logged_in = page.url.startswith("https://leetcode.com/profile/")
            except:
                pass

            if not is_logged_in:
                print("[2/5] Logging in...")
                page.goto("https://leetcode.com/accounts/login/", wait_until="domcontentloaded")
                time.sleep(2)

                # Fill username
                username_input = page.locator("input[type='text']").first
                username_input.fill(username)
                time.sleep(0.5)

                # Fill password
                password_input = page.locator("input[type='password']").first
                password_input.fill(password)
                time.sleep(0.5)

                # Click sign in
                login_btn = page.locator("button:has-text('Sign In')").first
                if login_btn.count() > 0:
                    login_btn.click()
                else:
                    # Try alternative selector
                    page.click("button[type='submit']")

                time.sleep(5)

                # Verify login
                if not page.url.startswith("https://leetcode.com/"):
                    print("Error: Login failed")
                    return False

            print("[3/5] Navigate to problem...")
            problem_url = f"https://leetcode.com/problems/{problem_slug}/"
            page.goto(problem_url, wait_until="domcontentloaded")
            time.sleep(3)

            # Verify page loaded
            if "404" in page.content() or "not found" in page.content().lower():
                print(f"Error: Problem '{problem_slug}' not found")
                return False

            print("[4/5] Entering code...")
            # Click editor
            editor = page.locator(".monaco-editor").first
            if editor.count() > 0:
                editor.click()
                time.sleep(1)

                # Select all and delete
                page.keyboard.press("Control+A")
                time.sleep(0.3)
                page.keyboard.press("Backspace")
                time.sleep(0.3)

                # Enter code line by line
                for line in code.split("\n"):
                    page.keyboard.type(line + "\n", delay=10)
                    time.sleep(0.1)
            else:
                # Alternative: direct paste
                page.keyboard.press("Control+A")
                time.sleep(0.2)
                page.keyboard.type(code, delay=1)

            time.sleep(2)

            # Select language
            print(f"[4/5] Setting language: {lang}")
            try:
                lang_selector = page.locator("button[data-testid='lang-select']").first
                if lang_selector.count() > 0:
                    lang_selector.click()
                    time.sleep(1)
                    # Find language
                    lang_button = page.locator(f"div:has-text('{lang}')").first
                    if lang_button.count() > 0:
                        lang_button.click()
                        time.sleep(1)
            except:
                # Skip if not found
                pass

            print("[5/5] Submitting code...")
            # Click submit
            submit_btn = page.locator("button:has-text('Submit')").first
            if submit_btn.count() > 0:
                submit_btn.click()
                time.sleep(3)
            else:
                print("Error: Submit button not found")
                return False

            # Wait for result
            print("Waiting for result...")
            max_wait = 120
            start_time = time.time()
            last_check = None

            while time.time() - start_time < max_wait:
                # Check content
                page_text = page.locator("body").inner_text()

                # Check status
                if "Accepted" in page_text:
                    print("\n✓ Result: Accepted")
                    time.sleep(2)
                    return True

                if "Wrong Answer" in page_text:
                    print("\n✗ Result: Wrong Answer")
                    return False

                if "Runtime Error" in page_text:
                    print("\n✗ Result: Runtime Error")
                    return False

                if "Compile Error" in page_text:
                    print("\n✗ Result: Compile Error")
                    return False

                if "Time Limit Exceeded" in page_text:
                    print("\n✗ Result: Time Limit Exceeded")
                    return False

                # Progress
                if page_text != last_check:
                    print(".", end="", flush=True)
                    last_check = page_text

                time.sleep(2)

            print("\n✗ Result: Timeout")
            return False

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return False
        finally:
            browser.close()


# ============================================================================
# Main
# ============================================================================

def main():
    import os

    parser = argparse.ArgumentParser(
        description="Submit LeetCode solutions using Playwright"
    )
    parser.add_argument(
        "--username",
        default=os.getenv("LEETCODE_USERNAME", ""),
        help="LeetCode username (or set LEETCODE_USERNAME env var)"
    )
    parser.add_argument(
        "--password",
        default=os.getenv("LEETCODE_PASSWORD", ""),
        help="LeetCode password (or set LEETCODE_PASSWORD env var)"
    )
    parser.add_argument(
        "--problem-slug",
        required=True,
        help="Problem slug (e.g.: two-sum)"
    )
    parser.add_argument(
        "--file",
        required=True,
        help="Solution file path"
    )
    parser.add_argument(
        "--lang",
        default="python3",
        help="Programming language"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="Run in headless mode"
    )
    parser.add_argument(
        "--show-browser",
        action="store_true",
        help="Show browser window (for debugging)"
    )

    args = parser.parse_args()

    # Verify required parameters
    if not args.username or not args.password:
        print("Error: Please provide LeetCode username and password", file=sys.stderr)
        print("  Method 1: Pass --username and --password", file=sys.stderr)
        print("  Method 2: Set LEETCODE_USERNAME and LEETCODE_PASSWORD env vars", file=sys.stderr)
        sys.exit(1)

    # Read code file
    code_path = Path(args.file)
    if not code_path.exists():
        print(f"Error: File not found '{args.file}'", file=sys.stderr)
        sys.exit(1)

    code = code_path.read_text(encoding="utf-8")

    # Submit
    success = submit_solution(
        username=args.username,
        password=args.password,
        problem_slug=args.problem_slug,
        code=code,
        lang=args.lang,
        headless=not args.show_browser,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
