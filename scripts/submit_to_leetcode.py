#!/usr/bin/env python3
"""
LeetCode Solution Submitter — one file per invocation.

Usage:
  python scripts/submit_to_leetcode.py --save-session
  python scripts/submit_to_leetcode.py --problem-slug two-sum --file src/1_TwoSum/solution.h
"""

import argparse
import base64
import os
import re
import sys
import time
import traceback
from pathlib import Path

from playwright.sync_api import sync_playwright, Page, BrowserContext

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

STORAGE_DIR = os.path.expanduser("~/.cache/leetcode-submit")
STORAGE_PATH = os.path.join(STORAGE_DIR, "storage_state.json")
SCREENSHOT_DIR = os.environ.get("SCREENSHOT_DIR", "/tmp/leetcode-screenshots")

EXIT_OK, EXIT_FAIL, EXIT_CLOUDFLARE = 0, 1, 2

TIMEOUT_PAGE = 30_000
TIMEOUT_EDITOR = 45_000
TIMEOUT_VERDICT = 150  # seconds

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_screenshot_seq = 0


def screenshot(page: Page, name: str) -> None:
    global _screenshot_seq
    try:
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        _screenshot_seq += 1
        path = os.path.join(SCREENSHOT_DIR, f"{_screenshot_seq:03d}_{name}.png")
        page.screenshot(path=path, full_page=True)
    except Exception:
        pass


class CloudflareBlockedError(Exception):
    pass


def is_cloudflare(page: Page) -> bool:
    try:
        t = page.title().lower()
    except Exception:
        return False
    return "just a moment" in t or "verify you are human" in t


def wait_for_cloudflare(page: Page, label: str = "", timeout: float = 30) -> None:
    if not is_cloudflare(page):
        return
    print(f"  [{label}] Cloudflare detected, waiting", end="", flush=True)
    start = time.time()
    while time.time() - start < timeout:
        time.sleep(2)
        print(".", end="", flush=True)
        if not is_cloudflare(page):
            print(f" resolved ({time.time()-start:.0f}s)")
            return
    print(f" BLOCKED ({timeout:.0f}s)")
    raise CloudflareBlockedError(f"Cloudflare blocked ({label})")


def goto(page: Page, url: str, label: str = "", timeout: int = TIMEOUT_PAGE) -> None:
    page.goto(url, wait_until="domcontentloaded", timeout=timeout)
    time.sleep(3)
    wait_for_cloudflare(page, label)
    screenshot(page, label or "page")


# ---------------------------------------------------------------------------
# Solution Extraction
# ---------------------------------------------------------------------------

def extract_all_solutions(filepath: str) -> dict[str, str]:
    content = Path(filepath).read_text(encoding="utf-8")
    content = re.sub(r'#include\s*[<"][^>"]*util[^>"]*[>"]', '', content)
    content = re.sub(r'^\s*//.*$', '', content, flags=re.MULTILINE)

    solutions = {}
    for name, body in re.findall(
        r'namespace\s+(\w+)\s*\{(.*?)\}\s*//\s*namespace\s+\1', content, re.DOTALL
    ):
        cls = _extract_class(body)
        if not cls:
            continue
        prefix = "using namespace std;\n\n" if "using namespace std;" in body else ""
        solutions[name] = prefix + cls
    return solutions


def _extract_class(body: str) -> str | None:
    m = re.search(r'class\s+Solution\s*\{', body)
    if not m:
        return None
    depth, end = 0, m.end() - 1
    for i in range(m.end() - 1, len(body)):
        if body[i] == '{': depth += 1
        elif body[i] == '}':
            depth -= 1
            if depth == 0: end = i + 1; break
    if end < len(body) and body[end] == ';':
        end += 1
    return body[m.start():end]


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def check_logged_in(page: Page) -> bool:
    goto(page, "https://leetcode.com/settings/profile", "check_login", 15_000)
    for _ in range(15):
        if "/accounts/login" in page.url:
            return False
        try:
            if len(page.locator("body").inner_text().strip()) > 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return page.url.startswith("https://leetcode.com/settings/profile")


def login_via_github(page: Page, username: str, password: str) -> bool:
    goto(page, "https://leetcode.com/accounts/login/", "login_page")

    gh_link = page.locator("a[href*='/accounts/github/login']").first
    if not gh_link.is_visible():
        print("  [err] GitHub login button not found"); return False
    gh_link.click()
    page.wait_for_load_state("domcontentloaded", timeout=TIMEOUT_PAGE)
    time.sleep(3)
    screenshot(page, "github_redirect")

    if page.url.startswith("https://leetcode.com") and "/accounts/login" not in page.url:
        if check_logged_in(page):
            return True

    if not page.url.startswith("https://github.com"):
        print(f"  [err] Unexpected redirect: {page.url}"); return False

    auth_btn = page.locator("button[name='authorize']").first
    if auth_btn.is_visible():
        auth_btn.click()
        page.wait_for_load_state("domcontentloaded", timeout=TIMEOUT_PAGE)
        time.sleep(3)
        return check_logged_in(page)

    login_f, pass_f = page.locator("#login_field"), page.locator("#password")
    if not (login_f.is_visible() and pass_f.is_visible()):
        print("  [err] GitHub login form not found"); return False
    login_f.fill(username)
    pass_f.fill(password)

    submit_btn = page.locator("input[type='submit'][value='Sign in']").first
    if not submit_btn.is_visible():
        submit_btn = page.locator("input[type='submit']").first
    if not submit_btn.is_visible():
        print("  [err] Sign in button not found"); return False

    submit_btn.click()
    page.wait_for_load_state("domcontentloaded", timeout=TIMEOUT_PAGE)
    time.sleep(3)
    screenshot(page, "github_post_signin")

    url_lower = page.url.lower()
    if any(kw in url_lower for kw in ["two-factor", "verified-device", "device-verification"]):
        print("  [err] 2FA/device verification required — use --save-session"); return False

    err = page.locator(".js-flash-alert, .flash-error").first
    if err.is_visible():
        print(f"  [err] GitHub: {err.inner_text()}"); return False

    if "authorize" in url_lower or "oauth" in url_lower:
        ab = page.locator("button[name='authorize']").first
        if ab.is_visible():
            ab.click()
            page.wait_for_load_state("domcontentloaded", timeout=TIMEOUT_PAGE)
            time.sleep(3)

    if check_logged_in(page):
        print("  [ok] Logged in via GitHub OAuth")
        return True
    print("  [err] OAuth did not result in login"); return False


# ---------------------------------------------------------------------------
# Submit
# ---------------------------------------------------------------------------

def submit_code(page: Page, slug: str, code: str, ns: str = "") -> str:
    """Submit one snippet. Returns verdict string. Raises CloudflareBlockedError."""
    label = f"{slug}/{ns}" if ns else slug
    print(f"\n  --- {label} ---")

    goto(page, f"https://leetcode.com/problems/{slug}/", "problem")
    editor = page.locator(".monaco-editor").first
    try:
        editor.wait_for(state="visible", timeout=TIMEOUT_EDITOR)
    except Exception:
        return "Editor not found"
    if slug not in page.url:
        return "Problem not found"

    mod = "Meta" if sys.platform == "darwin" else "Control"
    editor.click(); time.sleep(0.5)
    page.keyboard.press(f"{mod}+A"); time.sleep(0.3)
    page.keyboard.press("Delete"); time.sleep(0.3)
    page.evaluate("text => navigator.clipboard.writeText(text)", code)
    time.sleep(0.3)
    page.keyboard.press(f"{mod}+V"); time.sleep(1.5)
    screenshot(page, "code_entered")

    editor.click(); time.sleep(0.5)
    page.keyboard.press(f"{mod}+Enter"); time.sleep(7)
    screenshot(page, "submitted")

    print("  Waiting for verdict", end="", flush=True)
    start, last = time.time(), None
    verdicts = ["Accepted", "Wrong Answer", "Runtime Error",
                "Compile Error", "Time Limit Exceeded", "Memory Limit Exceeded"]

    while time.time() - start < TIMEOUT_VERDICT:
        try:
            body = page.locator("body").inner_text()
        except Exception:
            time.sleep(3); continue

        state = next((v for v in verdicts if v in body), None)
        if not state and ("Judging" in body or "Running" in body):
            state = "Running"

        if state and state != last:
            print(f"\n  → {state}", end="", flush=True)
            last = state

        if state == "Accepted":
            perf = _extract_perf(body)
            print(f"\n  [PASS] Accepted{perf}")
            screenshot(page, "accepted")
            return "Accepted"
        if state in verdicts:
            print(f"\n  [FAIL] {state}")
            screenshot(page, state.lower().replace(" ", "_"))
            return state

        print(".", end="", flush=True)
        time.sleep(3)

    print("\n  [FAIL] Timeout")
    return "Timeout"


def _extract_perf(body: str) -> str:
    parts = []
    rt = re.search(r'(\d+)\s*ms', body)
    mem = re.search(r'([\d.]+)\s*MB', body)
    beats = re.findall(r'Beats\s+([\d.]+)\s*%', body)
    if rt:
        s = f"{rt.group(1)} ms"
        if beats: s += f" (Beats {beats[0]}%)"
        parts.append(s)
    if mem:
        s = f"{mem.group(1)} MB"
        if len(beats) >= 2: s += f" (Beats {beats[1]}%)"
        parts.append(s)
    return f" — {', '.join(parts)}" if parts else ""


# ---------------------------------------------------------------------------
# Save Session
# ---------------------------------------------------------------------------

def save_session_interactive() -> None:
    print("=== Save Session Mode ===\n")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = ctx.new_page()
        page.goto("https://leetcode.com/accounts/login/")
        time.sleep(2)

        print("Browser opened. Login to LeetCode, then press Enter here.\n")
        input("Press Enter when logged in... ")

        os.makedirs(STORAGE_DIR, exist_ok=True)
        try:
            ctx.storage_state(path=STORAGE_PATH)
            print(f"\n[ok] Session saved to {STORAGE_PATH}")
            _print_session_base64()
        except Exception as e:
            print(f"[err] Failed: {e}"); sys.exit(1)
        finally:
            browser.close()


def _print_session_base64() -> None:
    try:
        encoded = base64.b64encode(Path(STORAGE_PATH).read_bytes()).decode()
        print(f"\n{'='*60}")
        print("BASE64 SESSION (copy to GitHub Secret LEETCODE_STORAGE_STATE):")
        print(f"{'='*60}")
        print(encoded)
        print(f"{'='*60}")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Browser Context
# ---------------------------------------------------------------------------

def _make_context(p, args) -> BrowserContext:
    browser = p.chromium.launch(
        headless=not args.show_browser,
        slow_mo=args.slow_mo if args.show_browser else 0,
        args=["--no-sandbox", "--disable-dev-shm-usage"],
    )
    try:
        ctx = browser.new_context(
            storage_state=STORAGE_PATH,
            viewport={"width": 1920, "height": 1080},
            user_agent=USER_AGENT,
        )
    except Exception:
        ctx = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=USER_AGENT,
        )
    ctx.grant_permissions(["clipboard-read", "clipboard-write"])
    return ctx


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Submit one LeetCode solution file")
    parser.add_argument("--save-session", action="store_true")
    parser.add_argument("--problem-slug", help="e.g. two-sum")
    parser.add_argument("--file", help="Path to solution.h")
    parser.add_argument("--code", help="Inline code (requires --problem-slug)")
    parser.add_argument("--ns", help="Submit only this namespace")
    parser.add_argument("--lang", default="cpp")
    parser.add_argument("--show-browser", action="store_true")
    parser.add_argument("--slow-mo", type=int, default=0)
    parser.add_argument("--screenshot-dir",
                        default=os.environ.get("SCREENSHOT_DIR", "/tmp/leetcode-screenshots"))
    parser.add_argument("--gh-username", default=os.getenv("GH_USERNAME", ""))
    parser.add_argument("--gh-password", default=os.getenv("GH_PASSWORD", ""))
    parser.add_argument("--max-retries", type=int, default=5)
    args = parser.parse_args()

    global SCREENSHOT_DIR
    SCREENSHOT_DIR = args.screenshot_dir

    if args.save_session:
        save_session_interactive()
        return

    if not args.problem_slug:
        parser.error("--problem-slug is required")
    if not args.file and not args.code:
        parser.error("--file or --code is required")
    if not os.path.exists(STORAGE_PATH):
        print("Error: No saved session. Run --save-session first.", file=sys.stderr)
        sys.exit(EXIT_FAIL)

    print(f"Problem: {args.problem_slug}")

    # ── Step 1: Login (retry on Cloudflare, fresh browser each attempt) ──
    for attempt in range(1, args.max_retries + 1):
        if attempt > 1:
            print(f"\n🔄 Retry {attempt}/{args.max_retries}...")
            time.sleep(5)
        try:
            pw, ctx, page = _open_browser(args)

            print("\n[login] Verifying session...")
            logged_in = check_logged_in(page)

            if not logged_in and args.gh_username and args.gh_password:
                print("[login] Session expired, trying GitHub OAuth...")
                logged_in = login_via_github(page, args.gh_username, args.gh_password)
                if logged_in:
                    os.makedirs(STORAGE_DIR, exist_ok=True)
                    ctx.storage_state(path=STORAGE_PATH)
                    print("[login] Session updated locally")
                    _print_session_base64()

            if not logged_in:
                print("[FAIL] Not logged in")
                ctx.browser.close()
                pw.stop()
                sys.exit(EXIT_FAIL)

            print("[login] ✅ Ready\n")
            break  # login succeeded, keep browser open

        except CloudflareBlockedError:
            print(f"  [blocked] Cloudflare (attempt {attempt}/{args.max_retries})")
            ctx.browser.close()
            pw.stop()
        except Exception as e:
            print(f"  [err] {e}", file=sys.stderr)
            traceback.print_exc()
            try: ctx.browser.close(); pw.stop()
            except Exception: pass
    else:
        print(f"\n[FAIL] All {args.max_retries} attempts failed")
        sys.exit(EXIT_CLOUDFLARE)

    # ── Step 2: Extract solutions ──
    if args.code:
        solutions = {"inline": args.code}
    else:
        solutions = extract_all_solutions(args.file)
        if not solutions:
            print(f"Error: No Solution classes found in {args.file}", file=sys.stderr)
            ctx.browser.close(); pw.stop()
            sys.exit(EXIT_FAIL)
        if args.ns:
            if args.ns not in solutions:
                print(f"Error: Namespace '{args.ns}' not found. "
                      f"Available: {', '.join(solutions)}", file=sys.stderr)
                ctx.browser.close(); pw.stop()
                sys.exit(EXIT_FAIL)
            solutions = {args.ns: solutions[args.ns]}

    print(f"Namespaces: {', '.join(solutions)}")

    # ── Step 3: Submit ──
    try:
        rc = _submit_all(page, args.problem_slug, solutions)
    except CloudflareBlockedError:
        print("  [blocked] Cloudflare during submission")
        rc = EXIT_CLOUDFLARE
    except Exception as e:
        print(f"  [err] {e}", file=sys.stderr)
        traceback.print_exc()
        rc = EXIT_FAIL
    finally:
        ctx.browser.close()
        pw.stop()
    sys.exit(rc)


def _open_browser(args):
    """Start Playwright + browser, return (playwright, context, page)."""
    pw = sync_playwright().start()
    ctx = _make_context(pw, args)
    page = ctx.new_page()
    return pw, ctx, page


def _submit_all(page: Page, slug: str, solutions: dict[str, str]) -> int:
    """Submit all namespaces. Assumes already logged in."""
    passed, total = 0, len(solutions)
    for i, (ns, code) in enumerate(solutions.items(), 1):
        print(f"[{i}/{total}] {ns}")
        verdict = submit_code(page, slug, code, ns=ns)

        if verdict == "Accepted":
            passed += 1
        elif verdict in ("Editor not found", "Problem not found"):
            print(f"  [err] {verdict} — aborting")
            break

        if i < total:
            time.sleep(3)

    print(f"\nResult: {passed}/{total} accepted")
    return EXIT_OK if passed == total else EXIT_FAIL


if __name__ == "__main__":
    main()
