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

=== Login Strategy (configurable via LOGIN_METHODS) ===

    Default order: saved session -> GitHub OAuth
    Change LOGIN_METHODS list below to reorder or add methods.
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

# Login methods in priority order.
# Swap or remove entries to change login behavior.
LOGIN_METHODS = ["session", "github"]


# ============================================================================
# Session Helpers
# ============================================================================

def has_saved_session() -> bool:
    return os.path.exists(STORAGE_STATE_PATH)


def save_session(context: BrowserContext) -> bool:
    """Save full browser storage state (cookies + localStorage)."""
    try:
        os.makedirs(STORAGE_STATE_DIR, exist_ok=True)
        context.storage_state(path=STORAGE_STATE_PATH)
        print(f"  [ok] Session saved to {STORAGE_STATE_PATH}")
        return True
    except Exception as e:
        print(f"  [err] Failed to save session: {e}")
        return False


# ============================================================================
# Screenshot Helper
# ============================================================================

def screenshot(page: Page, name: str) -> None:
    """Take a debug screenshot."""
    try:
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        ts = time.strftime("%H%M%S")
        path = os.path.join(SCREENSHOT_DIR, f"{ts}_{name}.png")
        page.screenshot(path=path)
        print(f"  [screenshot] {path}")
    except Exception:
        pass


# ============================================================================
# Login Strategies
# ============================================================================

def check_logged_in(page: Page) -> bool:
    """Check if the current browser session is logged in to LeetCode."""
    try:
        page.goto("https://leetcode.com/profile/",
                   wait_until="domcontentloaded", timeout=15000)
        time.sleep(2)
        # LeetCode redirects /profile/ to /u/<username>/ when logged in
        return page.url.startswith("https://leetcode.com/u/")
    except Exception:
        return False


def login_via_session(page: Page, context: BrowserContext, **_) -> bool:
    """Try to login using saved session (cookies + localStorage)."""
    if not has_saved_session():
        print("  No saved session found")
        return False

    print("  Verifying saved session...")
    if check_logged_in(page):
        print("  [ok] Logged in via saved session")
        save_session(context)  # Refresh expiry
        return True

    print("  [warn] Session expired")
    return False


def login_via_github(page: Page, context: BrowserContext,
                     gh_username: str = "", gh_password: str = "",
                     **_) -> bool:
    """
    Login to LeetCode via GitHub OAuth.

    Navigates to https://leetcode.com/accounts/github/login/ which redirects
    to GitHub's login page (no Cloudflare Turnstile). After GitHub login,
    it redirects back to LeetCode.

    Requires gh_username and gh_password (CLI args or env vars).
    """
    if not gh_username or not gh_password:
        print("  No GitHub credentials provided")
        return False

    print("  Navigating to LeetCode -> GitHub OAuth...")
    page.goto("https://leetcode.com/accounts/github/login/",
              wait_until="domcontentloaded")
    time.sleep(3)

    current_url = page.url

    # Case 1: Already authorized -- GitHub redirects straight back to LeetCode
    if "leetcode.com" in current_url:
        if check_logged_in(page):
            print("  [ok] GitHub OAuth: already authorized, logged in!")
            save_session(context)
            return True

    # Case 2: GitHub login page
    if "github.com" not in current_url:
        print(f"  [warn] Unexpected URL: {current_url}")
        screenshot(page, "github_unexpected")
        return False

    print(f"  GitHub login page: {page.title()}")

    # Check if GitHub asks for OAuth authorization (already logged in to GitHub)
    authorize_btn = page.locator("button[name='authorize']").first
    if authorize_btn.is_visible():
        print("  Already logged in to GitHub, authorizing LeetCode...")
        authorize_btn.click()
        time.sleep(5)
        if check_logged_in(page):
            print("  [ok] Logged in via GitHub OAuth (authorized)")
            save_session(context)
            return True

    # Fill GitHub login form
    login_field = page.locator("input[name='login']").first
    password_field = page.locator("input[name='password']").first

    if not login_field.is_visible() or not password_field.is_visible():
        print("  [err] Could not find GitHub login fields")
        screenshot(page, "github_no_fields")
        return False

    print(f"  Filling GitHub credentials ({gh_username[:3]}***)")
    login_field.fill(gh_username)
    time.sleep(0.3)
    password_field.fill(gh_password)
    time.sleep(0.3)

    # Click sign in
    sign_in_btn = page.locator(
        "input[type='submit'][value='Sign in']").first
    if not sign_in_btn.is_visible():
        sign_in_btn = page.locator("input[type='submit']").first

    if not sign_in_btn.is_visible():
        print("  [err] Could not find GitHub Sign In button")
        screenshot(page, "github_no_signin")
        return False

    sign_in_btn.click()
    print("  Waiting for GitHub login...")
    time.sleep(5)

    # Handle 2FA if needed
    current_url = page.url
    if "two-factor" in current_url or "sessions/two-factor" in current_url:
        print("  [warn] GitHub 2FA is required")
        print("  Hint: use --save-session to login manually instead")
        screenshot(page, "github_2fa")
        return False

    # Check if we need to authorize the OAuth app
    if "authorize" in page.url.lower():
        print("  Authorizing LeetCode OAuth app...")
        auth_btn = page.locator("button[name='authorize']").first
        if auth_btn.is_visible():
            auth_btn.click()
            time.sleep(5)

    # Verify we're back on LeetCode and logged in
    time.sleep(3)
    if check_logged_in(page):
        print("  [ok] Logged in via GitHub OAuth")
        save_session(context)
        return True

    print(f"  [err] GitHub login failed (URL: {page.url})")
    screenshot(page, "github_login_failed")
    return False


# Registry: method name -> function
LOGIN_REGISTRY = {
    "session": login_via_session,
    "github": login_via_github,
}


def attempt_login(page: Page, context: BrowserContext, **kwargs) -> bool:
    """Try each login method in LOGIN_METHODS order."""
    for method in LOGIN_METHODS:
        handler = LOGIN_REGISTRY.get(method)
        if handler is None:
            print(f"  [warn] Unknown login method: {method}")
            continue
        print(f"[Login] Trying: {method}")
        if handler(page, context, **kwargs):
            return True
    return False


# ============================================================================
# Core: Submit Solution
# ============================================================================

def submit_solution(
    problem_slug: str,
    code: str,
    lang: str = "cpp",
    headless: bool = True,
    **login_kwargs,
) -> bool:
    """
    Submit a solution to LeetCode.

    1. Login (via configured methods)
    2. Navigate to problem
    3. Enter code
    4. Submit and wait for verdict

    Returns True if Accepted.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )

        # Load saved session into context if available
        context_opts = {"viewport": {"width": 1920, "height": 1080}}
        if has_saved_session():
            try:
                context = browser.new_context(
                    storage_state=STORAGE_STATE_PATH, **context_opts)
            except Exception:
                context = browser.new_context(**context_opts)
        else:
            context = browser.new_context(**context_opts)

        page = context.new_page()

        try:
            # -- Login -------------------------------------------------
            print("[1/4] Logging in...")
            if not attempt_login(page, context, **login_kwargs):
                print("[FAIL] All login methods failed")
                print("Hint: Run  python scripts/submit_to_leetcode.py --save-session")
                screenshot(page, "login_failed")
                return False

            # -- Navigate to problem -----------------------------------
            print(f"[2/4] Opening problem: {problem_slug}")
            problem_url = f"https://leetcode.com/problems/{problem_slug}/"
            page.goto(problem_url, wait_until="domcontentloaded")
            time.sleep(3)

            print(f"  Page: {page.title()}")
            print(f"  URL:  {page.url}")

            if "404" in page.title() or problem_slug not in page.url:
                print(f"  [err] Problem '{problem_slug}' not found")
                screenshot(page, "problem_not_found")
                return False

            # -- Enter code --------------------------------------------
            print(f"[3/4] Entering code ({len(code)} chars, lang={lang})")

            # Select language
            try:
                lang_btn = page.locator(
                    "button[data-testid='lang-select']").first
                if lang_btn.is_visible():
                    lang_btn.click()
                    time.sleep(1)
                    lang_option = page.locator(
                        f"div:has-text('{lang}')").first
                    if lang_option.is_visible():
                        lang_option.click()
                        time.sleep(1)
            except Exception:
                pass

            # Focus editor, clear, type code
            editor = page.locator(".monaco-editor").first
            if editor.is_visible():
                editor.click()
                time.sleep(0.3)

            page.keyboard.press("Control+A")
            time.sleep(0.2)
            page.keyboard.press("Delete")
            time.sleep(0.2)
            page.keyboard.type(code, delay=5)
            time.sleep(1)
            print("  [ok] Code entered")

            # -- Submit ------------------------------------------------
            print("[4/4] Submitting...")
            time.sleep(1)

            # Click editor to ensure focus, then Ctrl+Enter
            if editor.is_visible():
                editor.click()
                time.sleep(0.3)

            page.keyboard.press("Control+Enter")
            print("  [ok] Ctrl+Enter pressed")
            time.sleep(3)
            screenshot(page, "submitted")

            # -- Wait for verdict --------------------------------------
            print("  Waiting for verdict", end="", flush=True)
            max_wait = 90
            start = time.time()
            last_state = None

            TERMINAL_STATES = [
                "Accepted", "Wrong Answer", "Runtime Error",
                "Compile Error", "Time Limit Exceeded",
                "Memory Limit Exceeded",
            ]

            while time.time() - start < max_wait:
                body = page.locator("body").inner_text()

                # Detect current state
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
                    print("\n  [PASS] Accepted")
                    screenshot(page, "accepted")
                    return True

                if state in TERMINAL_STATES and state != "Accepted":
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

    # Modes
    parser.add_argument("--save-session", action="store_true",
                        help="Open browser to login manually and save session")

    # Submission args
    parser.add_argument("--problem-slug",
                        help="Problem slug (e.g. two-sum)")
    parser.add_argument("--file",
                        help="Solution file path")
    parser.add_argument("--lang", default="cpp",
                        help="Language (default: cpp)")
    parser.add_argument("--show-browser", action="store_true",
                        help="Show browser window")
    parser.add_argument("--screenshot-dir",
                        default=os.environ.get(
                            "SCREENSHOT_DIR", "/tmp/leetcode-screenshots"),
                        help="Screenshot output directory")

    # GitHub OAuth credentials
    parser.add_argument("--gh-username",
                        default=os.getenv("GITHUB_USERNAME", ""),
                        help="GitHub username (or GITHUB_USERNAME env)")
    parser.add_argument("--gh-password",
                        default=os.getenv("GITHUB_PASSWORD", ""),
                        help="GitHub password (or GITHUB_PASSWORD env)")

    args = parser.parse_args()

    global SCREENSHOT_DIR
    SCREENSHOT_DIR = args.screenshot_dir

    # Mode: save session
    if args.save_session:
        save_session_interactive()
        return

    # Mode: submit -- validate required args
    if not args.problem_slug or not args.file:
        parser.error("--problem-slug and --file are required for submission")

    code_path = Path(args.file)
    if not code_path.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    # Check if we have any login method available
    if not has_saved_session() and not args.gh_username:
        print("Error: No login method available.\n", file=sys.stderr)
        print("Option A (recommended): Save session first:", file=sys.stderr)
        print("  python scripts/submit_to_leetcode.py --save-session\n",
              file=sys.stderr)
        print("Option B: Provide GitHub credentials:", file=sys.stderr)
        print("  --gh-username USER --gh-password PASS", file=sys.stderr)
        print("  or set GITHUB_USERNAME / GITHUB_PASSWORD env vars",
              file=sys.stderr)
        sys.exit(1)

    code = code_path.read_text(encoding="utf-8")

    success = submit_solution(
        problem_slug=args.problem_slug,
        code=code,
        lang=args.lang,
        headless=not args.show_browser,
        gh_username=args.gh_username,
        gh_password=args.gh_password,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
