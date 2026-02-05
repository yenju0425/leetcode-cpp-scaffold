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
import os
import sys
import time
from pathlib import Path

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

def get_cookies_path():
    """Get the path to store cookies."""
    cache_dir = os.path.expanduser("~/.cache/leetcode-submit")
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, "cookies.json")


def save_cookies(context):
    """Save browser cookies to file."""
    try:
        cookies = context.cookies()
        cookies_path = get_cookies_path()
        with open(cookies_path, 'w') as f:
            json.dump(cookies, f, indent=2)
        print(f"  ✓ Cookies saved to {cookies_path}")
        return True
    except Exception as e:
        print(f"  Warning: Failed to save cookies: {e}")
        return False


def load_cookies(context):
    """Load cookies from file into browser context."""
    try:
        cookies_path = get_cookies_path()
        if not os.path.exists(cookies_path):
            return False

        with open(cookies_path, 'r') as f:
            cookies = json.load(f)

        context.add_cookies(cookies)
        print(f"  ✓ Loaded {len(cookies)} cookies")
        return True
    except Exception as e:
        print(f"  Warning: Failed to load cookies: {e}")
        return False


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
        # Launch with more realistic browser settings
        browser = p.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
            ]
        )
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = context.new_page()

        try:
            # Try to load existing cookies first
            print("[1/5] Checking for saved session...")
            cookies_loaded = load_cookies(context)

            is_logged_in = False
            if cookies_loaded:
                print("  Verifying saved session...")
                page.goto("https://leetcode.com/", wait_until="domcontentloaded")
                time.sleep(1)

                # Check if logged in with cookies
                try:
                    page.goto("https://leetcode.com/profile/",
                              wait_until="domcontentloaded", timeout=5000)
                    if page.url.startswith("https://leetcode.com/u/"):
                        print("  ✅ Logged in with saved cookies! (bypassed Cloudflare)")
                        is_logged_in = True
                    else:
                        print("  ⚠ Saved cookies expired, falling back to login")
                        is_logged_in = False
                except:
                    print("  ⚠ Saved cookies expired, falling back to login")
                    is_logged_in = False
            else:
                print("  No saved session found, will attempt login")
                page.goto("https://leetcode.com/", wait_until="domcontentloaded")
                time.sleep(2)

                # Wait for Cloudflare check
                print("  Waiting for Cloudflare check...")
                max_cloudflare_wait = 15
                for i in range(max_cloudflare_wait):
                    page_title = page.title()
                    if "Just a moment" not in page_title:
                        break
                    print(f"  [{i+1}/{max_cloudflare_wait}] Still on Cloudflare check...", flush=True)
                    time.sleep(1)

                page_title = page.title()
                page_url = page.url
                print(f"  Page loaded: {page_title}")
                print(f"  URL: {page_url}")

                if "Just a moment" in page_title:
                    print("  ❌ Stuck on Cloudflare protection")
                    return False

            if not is_logged_in:
                print("[2/5] Logging in...")
                page.goto("https://leetcode.com/accounts/login/", wait_until="domcontentloaded")
                time.sleep(2)

                # Wait for Cloudflare again
                for i in range(10):
                    if "Just a moment" not in page.title():
                        break
                    time.sleep(1)

                print(f"  Login page: {page.title()}")

                # Find username input
                print("  Looking for username field...")
                username_input = page.locator("input[type='text']").first
                if username_input.count() == 0:
                    username_input = page.locator("input[name='login']").first
                if username_input.count() == 0:
                    username_input = page.locator("input#id_login").first

                if username_input.count() == 0:
                    print("  ❌ Error: Could not find username input field")
                    # Save screenshot for debugging
                    try:
                        page.screenshot(path="/tmp/leetcode_login_page.png")
                        print("  Screenshot saved: /tmp/leetcode_login_page.png")
                    except:
                        pass
                    return False

                print(f"  Filling username: {username[:3]}***")
                # Click to focus, then type to trigger events
                username_input.click()
                time.sleep(0.2)
                username_input.fill(username)
                # Trigger blur event
                username_input.press("Tab")
                time.sleep(0.5)

                # Find password input
                print("  Looking for password field...")
                password_input = page.locator("input[type='password']").first
                if password_input.count() == 0:
                    password_input = page.locator("input[name='password']").first
                if password_input.count() == 0:
                    password_input = page.locator("input#id_password").first

                if password_input.count() == 0:
                    print("  ❌ Error: Could not find password input field")
                    try:
                        page.screenshot(path="/tmp/leetcode_login_page.png")
                        print("  Screenshot saved: /tmp/leetcode_login_page.png")
                    except:
                        pass
                    return False

                print("  Filling password: ***")
                # Click to focus, then type to trigger events
                password_input.click()
                time.sleep(0.2)
                password_input.fill(password)
                # Trigger blur event
                password_input.press("Tab")
                time.sleep(0.5)

                # Find sign in button
                print("  Looking for Sign In button...")
                login_btn = page.locator("button:has-text('Sign In')").first
                if login_btn.count() == 0:
                    login_btn = page.locator("button[type='submit']").first
                if login_btn.count() == 0:
                    login_btn = page.locator("button:has-text('Log In')").first
                if login_btn.count() == 0:
                    login_btn = page.locator("button#signin_btn").first

                if login_btn.count() == 0:
                    print("  ❌ Error: Could not find Sign In button")
                    try:
                        page.screenshot(path="/tmp/leetcode_login_page.png")
                        print("  Screenshot saved: /tmp/leetcode_login_page.png")
                    except:
                        pass
                    return False

                # Check if button is disabled
                print("  Waiting for Sign In button to be enabled...")
                try:
                    # Wait for button to become enabled (max 10 seconds)
                    for i in range(20):
                        is_disabled = login_btn.is_disabled()
                        if not is_disabled:
                            print("  ✓ Sign In button is now enabled")
                            break
                        if i == 0:
                            print("  Button is disabled, waiting for form validation...")
                        time.sleep(0.5)

                    # Final check
                    if login_btn.is_disabled():
                        print("  ❌ Error: Sign In button is still disabled after 10 seconds")
                        print("  This may indicate form validation issues")
                        try:
                            page.screenshot(path="/tmp/leetcode_login_disabled.png")
                            print("  Screenshot saved: /tmp/leetcode_login_disabled.png")
                        except:
                            pass
                        return False
                except Exception as e:
                    print(f"  Warning: Could not check button state: {e}")

                print("  Clicking Sign In button...")
                try:
                    login_btn.click(timeout=5000)
                    print("  ✓ Sign In button clicked")
                except Exception as e:
                    print(f"  ❌ Error clicking Sign In button: {e}")
                    try:
                        page.screenshot(path="/tmp/leetcode_login_error.png")
                        print("  Screenshot saved: /tmp/leetcode_login_error.png")
                    except:
                        pass
                    return False

                print("  Waiting for login to complete...")
                time.sleep(5)  # Wait longer for login

                # Verify login
                current_url = page.url
                page_title = page.title()
                print(f"  After login URL: {current_url}")
                print(f"  After login title: {page_title}")

                # Check for error messages
                page_content = page.content()
                if "incorrect" in page_content.lower() or "invalid" in page_content.lower():
                    print("  ❌ Error: Invalid username or password")
                    return False

                if "captcha" in page_content.lower() or "verification" in page_content.lower():
                    print("  ❌ Error: CAPTCHA or verification required")
                    print("  Please login manually once in a browser to solve CAPTCHA")
                    return False

                if "login" in current_url.lower():
                    print("  ❌ Error: Login failed - still on login page")
                    try:
                        page.screenshot(path="/tmp/leetcode_after_login.png")
                        print("  Screenshot saved: /tmp/leetcode_after_login.png")
                    except:
                        pass
                    return False

                print("  ✅ Login successful")

                # Save cookies for future use
                save_cookies(context)

            print("[3/5] Navigate to problem...")
            problem_url = f"https://leetcode.com/problems/{problem_slug}/"
            page.goto(problem_url, wait_until="domcontentloaded")
            time.sleep(2)

            # Wait for Cloudflare again
            for i in range(10):
                if "Just a moment" not in page.title():
                    break
                time.sleep(1)

            # Verify page loaded
            page_title = page.title()
            page_url = page.url
            print(f"  Problem page: {page_title}")
            print(f"  URL: {page_url}")

            # Try to get problem title from page
            try:
                problem_title_elem = page.locator("a[href*='/problems/']").first
                if problem_title_elem.count() > 0:
                    problem_title = problem_title_elem.inner_text()
                    print(f"  Problem: {problem_title}")
            except:
                pass

            if "404" in page.content() or "not found" in page.content().lower():
                print(f"  ❌ Problem '{problem_slug}' not found")
                return False

            if "Just a moment" in page_title:
                print("  ❌ Still on Cloudflare protection")
                return False

            print("[4/5] Entering code...")
            # Click editor
            editor = page.locator(".monaco-editor").first
            if editor.count() > 0:
                editor.click()
                time.sleep(0.5)
                print("  Editor found and focused")

            # Clear and paste code
            page.keyboard.press("Control+A")
            time.sleep(0.2)
            page.keyboard.press("Delete")
            time.sleep(0.2)

            # Type code faster
            page.keyboard.type(code, delay=5)
            print(f"  Code entered ({len(code)} chars)")
            time.sleep(1)

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
            time.sleep(2)

            # Primary method: Ctrl+Enter keyboard shortcut
            print("  Using Ctrl+Enter to submit...")
            try:
                editor = page.locator(".monaco-editor").first
                if editor.count() > 0:
                    editor.click()
                    time.sleep(0.3)

                page.keyboard.press("Control+Enter")
                print("  ✓ Ctrl+Enter pressed")
                time.sleep(2)
            except Exception as e:
                print(f"  Ctrl+Enter failed: {e}")

                # Fallback: Try submit button
                print("  Trying submit button...")
                try:
                    submit_btn = page.locator(
                        "button[data-e2e-locator='console-submit-button']").first
                    if submit_btn.is_visible(timeout=5000):
                        submit_btn.click()
                        print("  ✓ Submit button clicked")
                        time.sleep(2)
                    else:
                        raise Exception("Submit button not visible")
                except:
                    print("  Error: Could not submit solution")
                    return False

            # Wait for result
            print("  Waiting for result", end="", flush=True)
            max_wait = 90
            start_time = time.time()
            check_interval = 2
            last_state = None

            while time.time() - start_time < max_wait:
                page_text = page.locator("body").inner_text()

                # Log state changes
                current_state = None
                if "Accepted" in page_text:
                    current_state = "Accepted"
                elif "Wrong Answer" in page_text:
                    current_state = "Wrong Answer"
                elif "Runtime Error" in page_text:
                    current_state = "Runtime Error"
                elif "Compile Error" in page_text:
                    current_state = "Compile Error"
                elif "Time Limit Exceeded" in page_text:
                    current_state = "Time Limit Exceeded"
                elif "Judging" in page_text or "Running" in page_text:
                    current_state = "Running"

                if current_state != last_state and current_state:
                    print(f"\n  Status: {current_state}", end="", flush=True)
                    last_state = current_state

                # Check status
                if "Accepted" in page_text:
                    print("\n  ✅ Result: Accepted")
                    return True
                if "Wrong Answer" in page_text:
                    print("\n  ❌ Result: Wrong Answer")
                    return False
                if "Runtime Error" in page_text:
                    print("\n  ❌ Result: Runtime Error")
                    return False
                if "Compile Error" in page_text:
                    print("\n  ❌ Result: Compile Error")
                    return False
                if "Time Limit Exceeded" in page_text:
                    print("\n  ❌ Result: Time Limit Exceeded")
                    return False

                print(".", end="", flush=True)
                time.sleep(check_interval)

            print("\n  ❌ Result: Timeout waiting for verdict")
            print(f"  Last page title: {page.title()}")
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
    parser.add_argument(
        "--save-cookies-only",
        action="store_true",
        help="Only login and save cookies, then exit (for initial setup)"
    )

    args = parser.parse_args()

    # Special mode: Only save cookies
    if args.save_cookies_only:
        print("=== Cookie Setup Mode ===")
        print("This will open a browser for you to login manually.")
        print("After logging in successfully, press Ctrl+C to save cookies.\n")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)  # Always show browser
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()

            print("Opening LeetCode...")
            page.goto("https://leetcode.com/")
            time.sleep(2)

            print("\n📌 Instructions:")
            print("  1. Login manually in the browser window")
            print("  2. Solve Cloudflare Turnstile CAPTCHA if prompted")
            print("  3. Wait until you see LeetCode homepage")
            print("  4. Press Ctrl+C in this terminal to save cookies")
            print("\nWaiting for you to login...")

            try:
                # Wait for user to press Ctrl+C
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n\nSaving cookies...")

            # Save cookies before closing
            try:
                cookies = context.cookies()
                if cookies:
                    cookies_path = get_cookies_path()
                    with open(cookies_path, 'w') as f:
                        json.dump(cookies, f, indent=2)
                    print(f"✅ {len(cookies)} cookies saved to {cookies_path}")
                    print("\n💡 You can now run submissions without needing to login each time!")
                    print(
                        "   Example: python scripts/submit_to_leetcode.py --problem-slug two-sum --file src/1_TwoSum/solution.h --lang cpp")
                    sys.exit(0)
                else:
                    print("⚠ No cookies found. Did you login?")
                    sys.exit(1)
            except Exception as e:
                print(f"❌ Error saving cookies: {e}")
                sys.exit(1)
            finally:
                browser.close()

    # Normal mode: Submit solution
    # Verify required parameters
    if not args.username or not args.password:
        print("Error: Please provide LeetCode username and password", file=sys.stderr)
        print("  Method 1: Pass --username and --password", file=sys.stderr)
        print("  Method 2: Set LEETCODE_USERNAME and LEETCODE_PASSWORD env vars", file=sys.stderr)
        print("  Method 3 (RECOMMENDED): Use --save-cookies-only to login once and save cookies", file=sys.stderr)
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
