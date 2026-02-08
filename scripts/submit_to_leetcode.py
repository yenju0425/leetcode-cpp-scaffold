#!/usr/bin/env python3
"""
LeetCode Solution Submitter using Playwright

Automatically submit solutions via browser automation.

=== First-Time Setup (save session) ===

    python scripts/submit_to_leetcode.py --save-session

    A browser window opens. Login via GitHub (or however you prefer),
    then press Enter in the terminal. The session is saved to:
        ~/.cache/leetcode-submit/storage_state.json

=== Submit a Solution ===

    python scripts/submit_to_leetcode.py \
        --problem-slug two-sum --file solution.cpp --lang cpp

=== CI/CD (GitHub Actions) ===

    1. Run --save-session locally
    2. Encode the session:
           base64 -w0 ~/.cache/leetcode-submit/storage_state.json
    3. Add output as GitHub Secret: LEETCODE_STORAGE_STATE
    4. CI decodes it back before running this script

=== Login Strategy ===

    1. Restore saved session and verify it works
    2. If no session or session expired, login via GitHub OAuth
    3. On success, save session for next time
"""

import argparse
import os
import sys
import time
import traceback
from pathlib import Path

from playwright.sync_api import sync_playwright, Page, BrowserContext

# ============================================================================
# Configuration
# ============================================================================

STORAGE_STATE_DIR = os.path.expanduser("~/.cache/leetcode-submit")
STORAGE_STATE_PATH = os.path.join(STORAGE_STATE_DIR, "storage_state.json")
SCREENSHOT_DIR = os.environ.get("SCREENSHOT_DIR", "/tmp/leetcode-screenshots")


# ============================================================================
# Session Helpers
# ============================================================================

def has_saved_session() -> bool:
    return os.path.exists(STORAGE_STATE_PATH)


def save_session(context: BrowserContext) -> None:
    """Save full browser storage state (cookies + localStorage)."""
    os.makedirs(STORAGE_STATE_DIR, exist_ok=True)
    context.storage_state(path=STORAGE_STATE_PATH)
    print(f"  [ok] Session saved to {STORAGE_STATE_PATH}")


# ============================================================================
# Screenshot Helper
# ============================================================================

_screenshot_counter = 0


def screenshot(page: Page, name: str) -> None:
    """Take a debug screenshot with sequential numbering."""
    global _screenshot_counter
    try:
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        _screenshot_counter += 1
        path = os.path.join(
            SCREENSHOT_DIR, f"{_screenshot_counter:03d}_{name}.png")
        page.screenshot(path=path, full_page=True)
        print(f"  [screenshot] {path}")
    except Exception:
        pass


# ============================================================================
# Login Helpers
# ============================================================================

def check_logged_in(page: Page) -> bool:
    """Navigate to profile and check if the session is authenticated."""
    try:
        page.goto("https://leetcode.com/profile/",
                   wait_until="domcontentloaded", timeout=15_000)
        time.sleep(2)  # Wait for redirect
        screenshot(page, "check_login")

        url = page.url
        logged_in = url.startswith("https://leetcode.com/settings/profile")
        print(f"  Login check: URL={url}, logged_in={logged_in}")
        return logged_in
    except Exception as e:
        print(f"  Login check error: {e}")
        return False


def login_via_github(page: Page, context: BrowserContext,
                     gh_username: str, gh_password: str) -> bool:
    """
    Login to LeetCode via GitHub OAuth.

    Flow: LeetCode login page -> click GitHub -> fill GitHub form
          -> OAuth authorize -> redirect back -> verify login.
    """
    # Step 1: Open LeetCode login page
    print("  Step 1: Opening LeetCode login page...")
    page.goto("https://leetcode.com/accounts/login/",
              wait_until="domcontentloaded", timeout=30_000)
    time.sleep(2)  # Wait for page to render
    screenshot(page, "github_login_page")

    # Step 2: Click the GitHub login link
    print("  Step 2: Clicking GitHub login button...")
    github_link = page.locator("a[href*='/accounts/github/login']").first
    if not github_link.is_visible():
        print("  [err] Could not find GitHub login link")
        screenshot(page, "github_no_button")
        return False

    github_link.click()
    page.wait_for_load_state("domcontentloaded", timeout=30_000)
    time.sleep(3)
    screenshot(page, "github_after_click")
    print(f"  Redirected to: {page.url}")

    # Already authorized - redirected straight back to LeetCode
    if (page.url.startswith("https://leetcode.com")
            and "/accounts/login" not in page.url):
        print("  Already authorized via GitHub, verifying...")
        if check_logged_in(page):
            save_session(context)
            return True

    # Not on GitHub - something unexpected happened
    if not page.url.startswith("https://github.com"):
        print(f"  [err] Unexpected URL: {page.url}")
        screenshot(page, "github_unexpected_url")
        return False

    # Check if GitHub shows the OAuth authorize button (already logged in to GH)
    authorize_btn = page.locator("button[name='authorize']").first
    if authorize_btn.is_visible():
        print("  Already logged in to GitHub, authorizing LeetCode...")
        authorize_btn.click()
        page.wait_for_load_state("domcontentloaded", timeout=30_000)
        time.sleep(3)
        if check_logged_in(page):
            save_session(context)
            return True
        return False

    # Step 3: Fill GitHub login form
    print("  Step 3: Filling GitHub login form...")
    login_field = page.locator("#login_field")
    password_field = page.locator("#password")

    if not login_field.is_visible() or not password_field.is_visible():
        print("  [err] GitHub login fields not found")
        screenshot(page, "github_no_fields")
        return False

    login_field.fill(gh_username)
    password_field.fill(gh_password)
    screenshot(page, "github_credentials_filled")

    # Step 4: Click Sign In
    print("  Step 4: Signing in...")
    sign_in_btn = page.locator("input[type='submit'][value='Sign in']").first
    if not sign_in_btn.is_visible():
        sign_in_btn = page.locator("input[type='submit']").first

    if not sign_in_btn.is_visible():
        print("  [err] GitHub Sign In button not found")
        screenshot(page, "github_no_signin_btn")
        return False

    sign_in_btn.click()
    page.wait_for_load_state("domcontentloaded", timeout=30_000)
    time.sleep(3)
    screenshot(page, "github_after_signin")
    print(f"  Post-login URL: {page.url}")

    # Handle 2FA / device verification
    if "two-factor" in page.url or "sessions/two-factor" in page.url:
        print("  [err] GitHub 2FA required - use --save-session instead")
        screenshot(page, "github_2fa")
        return False

    if "verified-device" in page.url or "device-verification" in page.url.lower():
        print("  [err] GitHub device verification required - use --save-session instead")
        screenshot(page, "github_device_verification")
        return False

    # Check for login errors
    error_msg = page.locator(".js-flash-alert, .flash-error").first
    if error_msg.is_visible():
        print(f"  [err] GitHub login error: {error_msg.inner_text()}")
        screenshot(page, "github_login_error")
        return False

    # Step 5: Handle OAuth authorization page (if shown)
    if "authorize" in page.url.lower() or "oauth" in page.url.lower():
        print("  Step 5: Authorizing LeetCode OAuth app...")
        auth_btn = page.locator("button[name='authorize']").first
        if auth_btn.is_visible():
            auth_btn.click()
            page.wait_for_load_state("domcontentloaded", timeout=30_000)
            time.sleep(3)
            screenshot(page, "github_after_authorize")

    # Step 6: Verify login on LeetCode
    time.sleep(2)
    if check_logged_in(page):
        print("  [ok] Logged in via GitHub OAuth!")
        save_session(context)
        return True

    print("  [err] GitHub OAuth did not result in LeetCode login")
    print(f"  Final URL: {page.url}")
    screenshot(page, "github_login_failed")
    return False


def ensure_logged_in(page: Page, context: BrowserContext,
                     gh_username: str = "", gh_password: str = "") -> bool:
    """
    Ensure we are logged in to LeetCode.

    Strategy:
      1. If a saved session exists, restore it and verify - skip GitHub if OK.
      2. Otherwise (or if session expired), try GitHub OAuth.
    """
    # Try saved session first (it should be valid; we only save on success)
    if has_saved_session():
        print("  Checking saved session...")
        if check_logged_in(page):
            print("  [ok] Saved session is valid")
            return True
        print("  [warn] Saved session expired, falling back to GitHub OAuth...")

    # GitHub OAuth
    if not gh_username or not gh_password:
        print("  [err] No GitHub credentials provided and no valid session")
        return False

    print("  Logging in via GitHub OAuth...")
    return login_via_github(page, context, gh_username, gh_password)


# ============================================================================
# Core: Submit Solution
# ============================================================================

def submit_solution(
    problem_slug: str,
    code: str,
    lang: str = "cpp",
    headless: bool = True,
    slow_mo: int = 0,
    gh_username: str = "",
    gh_password: str = "",
) -> bool:
    """
    Submit a solution to LeetCode.

    1. Login (saved session -> GitHub OAuth)
    2. Navigate to problem
    3. Paste code via clipboard
    4. Submit and wait for verdict

    Returns True if Accepted.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            slow_mo=slow_mo,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )

        context_opts = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
        }

        # Restore saved session into browser context
        if has_saved_session():
            try:
                context = browser.new_context(
                    storage_state=STORAGE_STATE_PATH, **context_opts)
            except Exception:
                context = browser.new_context(**context_opts)
        else:
            context = browser.new_context(**context_opts)

        # Grant clipboard permissions for code pasting
        context.grant_permissions(["clipboard-read", "clipboard-write"])
        page = context.new_page()

        try:
            # -- Login -------------------------------------------------
            print("[1/4] Logging in...")
            if not ensure_logged_in(page, context,
                                    gh_username=gh_username,
                                    gh_password=gh_password):
                print("[FAIL] Login failed")
                print("Hint: Run  python scripts/submit_to_leetcode.py --save-session")
                screenshot(page, "login_failed")
                return False

            # -- Navigate to problem -----------------------------------
            print(f"\n[2/4] Opening problem: {problem_slug}")
            problem_url = f"https://leetcode.com/problems/{problem_slug}/"
            page.goto(problem_url, wait_until="domcontentloaded", timeout=30_000)
            time.sleep(2)  # Wait for page to render
            screenshot(page, "problem_page_loaded")

            if problem_slug not in page.url:
                print(f"  [err] Problem '{problem_slug}' not found (URL: {page.url})")
                screenshot(page, "problem_not_found")
                return False
            print(f"  [ok] {page.title()}")

            # -- Enter code --------------------------------------------
            print(f"\n[3/4] Entering code ({len(code)} chars, lang={lang})")

            # Wait for Monaco editor to be ready
            editor = page.locator(".monaco-editor").first
            editor.wait_for(state="visible", timeout=15_000)
            editor.click()
            time.sleep(0.5)

            # Select all existing code and delete it
            modifier = "Meta" if sys.platform == "darwin" else "Control"
            page.keyboard.press(f"{modifier}+A")
            time.sleep(0.2)
            page.keyboard.press("Delete")
            time.sleep(0.2)

            # Paste code via clipboard (preserves formatting, unlike fill())
            page.evaluate("text => navigator.clipboard.writeText(text)", code)
            time.sleep(0.2)
            page.keyboard.press(f"{modifier}+V")
            time.sleep(1)
            print("  [ok] Code pasted via clipboard")
            screenshot(page, "code_entered")

            # -- Submit ------------------------------------------------
            print("\n[4/4] Submitting...")
            editor.click()
            time.sleep(0.3)
            page.keyboard.press(f"{modifier}+Enter")
            print("  [ok] Ctrl+Enter pressed")
            time.sleep(5)
            screenshot(page, "submitted")

            # -- Wait for verdict --------------------------------------
            print("  Waiting for verdict", end="", flush=True)
            max_wait = 120
            start = time.time()
            last_state = None

            TERMINAL_STATES = [
                "Accepted", "Wrong Answer", "Runtime Error",
                "Compile Error", "Time Limit Exceeded",
                "Memory Limit Exceeded",
            ]

            while time.time() - start < max_wait:
                try:
                    body = page.locator("body").inner_text()
                except Exception:
                    time.sleep(2)
                    continue

                state = None
                for kw in TERMINAL_STATES:
                    if kw in body:
                        state = kw
                        break
                if state is None and ("Judging" in body or "Running" in body):
                    state = "Running"

                if state and state != last_state:
                    print(f"\n  Status: {state}", end="", flush=True)
                    last_state = state

                if state == "Accepted":
                    print("\n  [PASS] Accepted!")
                    screenshot(page, "accepted")
                    return True

                if state in TERMINAL_STATES:
                    print(f"\n  [FAIL] {state}")
                    screenshot(page, state.lower().replace(" ", "_"))
                    return False

                print(".", end="", flush=True)
                time.sleep(2)

            print("\n  [FAIL] Timeout waiting for verdict")
            screenshot(page, "timeout")
            return False

        except Exception as e:
            print(f"\n[FAIL] Error: {e}", file=sys.stderr)
            traceback.print_exc()
            screenshot(page, "exception")
            return False
        finally:
            browser.close()


# ============================================================================
# Save Session Mode
# ============================================================================

def save_session_interactive():
    """Open browser for manual login, then save session on Enter."""
    print("=== Save Session Mode ===\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
        )
        page = context.new_page()

        page.goto("https://leetcode.com/accounts/login/")
        time.sleep(2)

        print("A browser window has opened.\n")
        print("   1. Login to LeetCode (via GitHub, Google, or credentials)")
        print("   2. Make sure you can see the LeetCode homepage (logged in)")
        print("   3. Come back here and press Enter\n")

        input("Press Enter when you're logged in... ")

        print("\nSaving session...")
        os.makedirs(STORAGE_STATE_DIR, exist_ok=True)
        try:
            context.storage_state(path=STORAGE_STATE_PATH)
            print(f"[ok] Session saved to {STORAGE_STATE_PATH}")
            print(f"\nFor CI, base64-encode and store as GitHub Secret:")
            print(f"   base64 -w0 {STORAGE_STATE_PATH}")
        except Exception as e:
            print(f"[err] Failed to save: {e}")
            sys.exit(1)
        finally:
            try:
                browser.close()
            except Exception:
                pass


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Submit LeetCode solutions via Playwright",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # First-time setup (opens browser for manual login):
  %(prog)s --save-session

  # Submit using saved session:
  %(prog)s --problem-slug two-sum --file solution.cpp --lang cpp

  # Submit using GitHub OAuth (auto login):
  %(prog)s --problem-slug two-sum --file solution.cpp --lang cpp \\
           --gh-username USER --gh-password PASS
""",
    )

    parser.add_argument("--save-session", action="store_true",
                        help="Open browser to login manually and save session")
    parser.add_argument("--problem-slug",
                        help="Problem slug (e.g. two-sum)")
    parser.add_argument("--file",
                        help="Solution file path")
    parser.add_argument("--code",
                        help="Inline solution code (alternative to --file)")
    parser.add_argument("--lang", default="cpp",
                        help="Language (default: cpp)")
    parser.add_argument("--show-browser", action="store_true",
                        help="Show browser window")
    parser.add_argument("--slow-mo", type=int, default=0,
                        help="Slow down actions by N ms")
    parser.add_argument("--screenshot-dir",
                        default=os.environ.get(
                            "SCREENSHOT_DIR", "/tmp/leetcode-screenshots"),
                        help="Screenshot output directory")
    parser.add_argument("--gh-username",
                        default=os.getenv("GH_USERNAME", ""),
                        help="GitHub username (or GH_USERNAME env)")
    parser.add_argument("--gh-password",
                        default=os.getenv("GH_PASSWORD", ""),
                        help="GitHub password (or GH_PASSWORD env)")

    args = parser.parse_args()

    global SCREENSHOT_DIR
    SCREENSHOT_DIR = args.screenshot_dir

    # Mode: save session
    if args.save_session:
        save_session_interactive()
        return

    # Mode: submit - validate required args
    if not args.problem_slug:
        parser.error("--problem-slug is required for submission")
    if not args.file and not args.code:
        parser.error("--file or --code is required for submission")

    if args.code:
        code = args.code
    else:
        code_path = Path(args.file)
        if not code_path.exists():
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        code = code_path.read_text(encoding="utf-8")

    # Need at least one login method
    if not has_saved_session() and not args.gh_username:
        print("Error: No login method available.\n", file=sys.stderr)
        print("Option A: Provide GitHub credentials:", file=sys.stderr)
        print("  --gh-username USER --gh-password PASS\n", file=sys.stderr)
        print("Option B: Save session first:", file=sys.stderr)
        print("  python scripts/submit_to_leetcode.py --save-session",
              file=sys.stderr)
        sys.exit(1)

    success = submit_solution(
        problem_slug=args.problem_slug,
        code=code,
        lang=args.lang,
        headless=not args.show_browser,
        slow_mo=args.slow_mo if args.show_browser else 0,
        gh_username=args.gh_username,
        gh_password=args.gh_password,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
