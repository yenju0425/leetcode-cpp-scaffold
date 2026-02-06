#!/usr/bin/env python3
"""
LeetCode Solution Submitter using Playwright

Automatically submit solutions via browser automation.
Avoids API changes by simulating user interactions.
Includes Cloudflare bypass techniques: stealth JS, humanized delays, mouse simulation.

Usage:
    python submit_to_leetcode.py --problem-id 1 --file solution.cpp --lang cpp17
    python submit_to_leetcode.py --problem-slug two-sum --file solution.py --lang python3
"""

import argparse
import json
import os
import random
import sys
import time
import traceback
from pathlib import Path

from playwright.sync_api import sync_playwright


# ============================================================================
# Configuration
# ============================================================================

LEETCODE_USERNAME = ""
LEETCODE_PASSWORD = ""

SCREENSHOT_DIR = os.environ.get("SCREENSHOT_DIR", "/tmp/leetcode-screenshots")

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
# Humanization Helpers
# ============================================================================

def human_delay(min_sec: float = 0.3, max_sec: float = 1.5):
    """Sleep for a random duration to mimic human behavior."""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)


def human_short_delay():
    """Short random delay (50-300ms) for between keystrokes / micro-actions."""
    time.sleep(random.uniform(0.05, 0.3))


def human_mouse_move(page, target_x: int = None, target_y: int = None):
    """
    Simulate human-like mouse movement with intermediate waypoints.
    If no target given, move to a random viewport position.
    """
    vw = page.viewport_size["width"]
    vh = page.viewport_size["height"]

    if target_x is None:
        target_x = random.randint(100, vw - 100)
    if target_y is None:
        target_y = random.randint(100, vh - 100)

    # Generate 2-4 intermediate waypoints with slight jitter
    steps = random.randint(2, 4)
    current_x, current_y = random.randint(0, vw), random.randint(0, vh)

    for i in range(steps):
        ratio = (i + 1) / steps
        mid_x = int(current_x + (target_x - current_x) * ratio + random.randint(-30, 30))
        mid_y = int(current_y + (target_y - current_y) * ratio + random.randint(-20, 20))
        mid_x = max(0, min(vw, mid_x))
        mid_y = max(0, min(vh, mid_y))
        page.mouse.move(mid_x, mid_y)
        time.sleep(random.uniform(0.02, 0.08))

    page.mouse.move(target_x, target_y)


def human_type(page, text: str, min_delay: int = 30, max_delay: int = 120):
    """Type text with randomized per-character delays to mimic human typing."""
    for char in text:
        page.keyboard.type(char, delay=0)
        time.sleep(random.uniform(min_delay / 1000, max_delay / 1000))


def human_click(page, locator):
    """Click an element with human-like mouse movement beforehand."""
    try:
        box = locator.bounding_box()
        if box:
            # Move to element with jitter, then click
            target_x = int(box["x"] + box["width"] * random.uniform(0.3, 0.7))
            target_y = int(box["y"] + box["height"] * random.uniform(0.3, 0.7))
            human_mouse_move(page, target_x, target_y)
            human_short_delay()
            page.mouse.click(target_x, target_y)
        else:
            locator.click()
    except Exception:
        locator.click()


# ============================================================================
# Stealth / Anti-Detection
# ============================================================================

STEALTH_JS = """
() => {
    // Override navigator.webdriver
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

    // Override navigator.plugins to look like a real browser
    Object.defineProperty(navigator, 'plugins', {
        get: () => [
            { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
            { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
            { name: 'Native Client', filename: 'internal-nacl-plugin' },
        ],
    });

    // Override navigator.languages
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en'],
    });

    // Override navigator.platform
    Object.defineProperty(navigator, 'platform', {
        get: () => 'Linux x86_64',
    });

    // Override navigator.hardwareConcurrency
    Object.defineProperty(navigator, 'hardwareConcurrency', {
        get: () => 8,
    });

    // Override navigator.deviceMemory
    Object.defineProperty(navigator, 'deviceMemory', {
        get: () => 8,
    });

    // Remove automation-related properties
    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;

    // Override permissions query
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications'
            ? Promise.resolve({ state: Notification.permission })
            : originalQuery(parameters)
    );

    // Chrome runtime mock
    window.chrome = {
        runtime: { id: undefined },
        loadTimes: function() {},
        csi: function() {},
        app: { isInstalled: false },
    };

    // WebGL vendor/renderer
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {
        if (parameter === 37445) return 'Intel Inc.';
        if (parameter === 37446) return 'Intel Iris OpenGL Engine';
        return getParameter.call(this, parameter);
    };
}
"""


def apply_stealth(page):
    """Inject stealth JavaScript to avoid bot detection."""
    try:
        page.add_init_script(STEALTH_JS)
    except Exception as e:
        print(f"  Warning: Could not apply stealth script: {e}")


# ============================================================================
# Screenshot Helpers
# ============================================================================

def ensure_screenshot_dir():
    """Create screenshot directory if it doesn't exist."""
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def take_screenshot(page, name: str, full_page: bool = False) -> str:
    """
    Take a screenshot and save it with a descriptive name.
    Returns the file path.
    """
    ensure_screenshot_dir()
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{name}.png"
    filepath = os.path.join(SCREENSHOT_DIR, filename)
    try:
        page.screenshot(path=filepath, full_page=full_page)
        print(f"  📸 Screenshot: {filepath}")
        return filepath
    except Exception as e:
        print(f"  Warning: Screenshot failed ({name}): {e}")
        return ""


def dump_page_info(page, label: str):
    """Dump current page diagnostic info for debugging."""
    try:
        print(f"  [{label}] Title: {page.title()}")
        print(f"  [{label}] URL: {page.url}")
        # Save HTML snapshot for debugging
        ensure_screenshot_dir()
        html_path = os.path.join(
            SCREENSHOT_DIR,
            f"{time.strftime('%Y%m%d_%H%M%S')}_{label}.html"
        )
        html_content = page.content()
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"  [{label}] HTML saved: {html_path}")
    except Exception as e:
        print(f"  [{label}] Could not dump page info: {e}")


# ============================================================================
# Cookie Helpers
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
    except Exception:
        return False


# ============================================================================
# Cloudflare Handling
# ============================================================================

def wait_for_cloudflare(page, label: str = "", max_wait: int = 30) -> bool:
    """
    Wait for Cloudflare challenge to resolve.
    Takes screenshots at each stage for diagnostics.
    Returns True if passed, False if stuck.
    """
    if not label:
        label = "cf"

    for i in range(max_wait):
        page_title = page.title()
        if "Just a moment" not in page_title:
            return True

        if i == 0:
            take_screenshot(page, f"{label}_cloudflare_start")

        if i % 5 == 4:
            print(f"  [{i+1}/{max_wait}] Still on Cloudflare challenge...", flush=True)
            take_screenshot(page, f"{label}_cloudflare_{i+1}")
            # Try some human-like activity: slight mouse movements
            human_mouse_move(page)

        time.sleep(random.uniform(0.8, 1.5))

    # Still stuck
    take_screenshot(page, f"{label}_cloudflare_stuck", full_page=True)
    dump_page_info(page, f"{label}_cloudflare_stuck")
    return False


# ============================================================================
# Core Submission Logic
# ============================================================================

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
    Includes stealth mode and humanized interactions.

    Returns:
        bool: True if Accepted, False otherwise
    """
    with sync_playwright() as p:
        # Launch with comprehensive anti-detection flags
        browser = p.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-site-isolation-trials',
                '--disable-infobars',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--window-size=1920,1080',
                '--start-maximized',
                '--disable-gpu',
                '--lang=en-US,en',
            ]
        )

        # Randomize viewport slightly to avoid fingerprinting
        vw = random.choice([1920, 1900, 1912, 1936])
        vh = random.choice([1080, 1060, 1072, 1048])

        context = browser.new_context(
            viewport={'width': vw, 'height': vh},
            screen={'width': 1920, 'height': 1080},
            user_agent=(
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
            ),
            locale='en-US',
            timezone_id='America/New_York',
            color_scheme='light',
            has_touch=False,
            is_mobile=False,
            java_script_enabled=True,
            ignore_https_errors=True,
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'sec-ch-ua': '"Chromium";v="131", "Not_A Brand";v="24"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Linux"',
            },
        )

        page = context.new_page()

        # Apply stealth scripts before any navigation
        apply_stealth(page)

        # Also inject stealth on every new document
        context.add_init_script(STEALTH_JS)

        try:
            # ── Step 1: Check for saved session ──────────────────────────
            print("[1/5] Checking for saved session...")
            cookies_loaded = load_cookies(context)

            is_logged_in = False
            if cookies_loaded:
                print("  Verifying saved session...")
                page.goto("https://leetcode.com/", wait_until="domcontentloaded")
                human_delay(1.5, 3.0)

                try:
                    page.goto(
                        "https://leetcode.com/profile/",
                        wait_until="domcontentloaded",
                        timeout=10000,
                    )
                    human_delay(1.0, 2.0)
                    if page.url.startswith("https://leetcode.com/u/"):
                        print("  ✅ Logged in with saved cookies!")
                        is_logged_in = True
                        take_screenshot(page, "01_session_restored")
                    else:
                        print("  ⚠ Saved cookies expired, falling back to login")
                except Exception:
                    print("  ⚠ Saved cookies expired, falling back to login")
            else:
                print("  No saved session found, will attempt login")

            # ── Navigate to homepage first (warm up) ─────────────────────
            if not is_logged_in:
                page.goto("https://leetcode.com/", wait_until="domcontentloaded")
                human_delay(2.0, 4.0)

                # Simulate looking around the page
                human_mouse_move(page)
                human_delay(0.5, 1.5)
                human_mouse_move(page)

                # Wait for Cloudflare
                print("  Waiting for Cloudflare check...")
                if not wait_for_cloudflare(page, "homepage"):
                    print("  ❌ Stuck on Cloudflare protection at homepage")
                    take_screenshot(page, "01_cloudflare_blocked", full_page=True)
                    dump_page_info(page, "cloudflare_blocked")
                    return False

                page_title = page.title()
                page_url = page.url
                print(f"  Page loaded: {page_title}")
                print(f"  URL: {page_url}")
                take_screenshot(page, "01_homepage_loaded")

            # ── Step 2: Login ────────────────────────────────────────────
            if not is_logged_in:
                print("[2/5] Logging in...")
                human_delay(1.0, 2.0)

                page.goto(
                    "https://leetcode.com/accounts/login/",
                    wait_until="domcontentloaded",
                )
                human_delay(2.0, 4.0)

                # Wait for Cloudflare on login page
                if not wait_for_cloudflare(page, "login"):
                    print("  ❌ Stuck on Cloudflare protection at login page")
                    take_screenshot(page, "02_login_cloudflare_blocked", full_page=True)
                    dump_page_info(page, "login_cloudflare")
                    return False

                print(f"  Login page: {page.title()}")
                take_screenshot(page, "02_login_page_loaded")

                # Move mouse around to simulate human reading the page
                human_mouse_move(page)
                human_delay(0.5, 1.5)

                # ── Find and fill username ───────────────────────────────
                print("  Looking for username field...")
                username_input = None
                for selector in [
                    "input[type='text']",
                    "input[name='login']",
                    "input#id_login",
                    "input[autocomplete='username']",
                ]:
                    loc = page.locator(selector).first
                    if loc.count() > 0:
                        username_input = loc
                        break

                if username_input is None or username_input.count() == 0:
                    print("  ❌ Error: Could not find username input field")
                    take_screenshot(page, "02_no_username_field", full_page=True)
                    dump_page_info(page, "no_username_field")
                    return False

                print(f"  Filling username: {username[:3]}***")
                human_click(page, username_input)
                human_delay(0.3, 0.8)
                human_type(page, username)
                human_delay(0.3, 0.6)

                # Tab to next field (triggers blur/validation)
                page.keyboard.press("Tab")
                human_delay(0.5, 1.2)

                # ── Find and fill password ───────────────────────────────
                print("  Looking for password field...")
                password_input = None
                for selector in [
                    "input[type='password']",
                    "input[name='password']",
                    "input#id_password",
                ]:
                    loc = page.locator(selector).first
                    if loc.count() > 0:
                        password_input = loc
                        break

                if password_input is None or password_input.count() == 0:
                    print("  ❌ Error: Could not find password input field")
                    take_screenshot(page, "02_no_password_field", full_page=True)
                    dump_page_info(page, "no_password_field")
                    return False

                print("  Filling password: ***")
                human_click(page, password_input)
                human_delay(0.3, 0.8)
                human_type(page, password)
                human_delay(0.3, 0.6)

                # Tab away to trigger validation
                page.keyboard.press("Tab")
                human_delay(0.8, 2.0)

                take_screenshot(page, "02_form_filled")

                # ── Find Sign In button ──────────────────────────────────
                print("  Looking for Sign In button...")
                login_btn = None
                for selector in [
                    "button:has-text('Sign In')",
                    "button[type='submit']",
                    "button:has-text('Log In')",
                    "button#signin_btn",
                ]:
                    loc = page.locator(selector).first
                    if loc.count() > 0:
                        login_btn = loc
                        break

                if login_btn is None or login_btn.count() == 0:
                    print("  ❌ Error: Could not find Sign In button")
                    take_screenshot(page, "02_no_signin_button", full_page=True)
                    dump_page_info(page, "no_signin_button")
                    return False

                # Wait for button to become enabled (Cloudflare Turnstile
                # often keeps it disabled until the invisible challenge passes)
                print("  Waiting for Sign In button to be enabled...")
                button_enabled = False
                max_button_wait = 30  # increased from 10s to 30s
                for i in range(max_button_wait * 2):  # check every 0.5s
                    is_disabled = login_btn.is_disabled()
                    if not is_disabled:
                        print("  ✓ Sign In button is now enabled")
                        button_enabled = True
                        break
                    if i == 0:
                        print(
                            "  Button is disabled — likely waiting for "
                            "Cloudflare Turnstile to complete..."
                        )
                    if i % 10 == 9:
                        elapsed = (i + 1) * 0.5
                        print(f"  Still waiting... ({elapsed:.0f}s elapsed)")
                        take_screenshot(page, f"02_button_disabled_{elapsed:.0f}s")
                        # Move mouse around — Turnstile may need interaction
                        human_mouse_move(page)
                    time.sleep(0.5)

                if not button_enabled:
                    print(
                        f"  ❌ Error: Sign In button still disabled after "
                        f"{max_button_wait} seconds"
                    )
                    print(
                        "  This is almost certainly Cloudflare Turnstile "
                        "blocking the automated browser."
                    )
                    take_screenshot(page, "02_button_still_disabled", full_page=True)
                    dump_page_info(page, "button_disabled_final")

                    # Extra diagnostics: check for Turnstile iframe
                    try:
                        turnstile_frames = page.frames
                        print(f"  Page has {len(turnstile_frames)} frames:")
                        for frame in turnstile_frames:
                            print(f"    - {frame.url}")
                    except Exception:
                        pass
                    return False

                # Click Sign In with human-like behavior
                print("  Clicking Sign In button...")
                human_delay(0.3, 0.8)
                human_click(page, login_btn)
                print("  ✓ Sign In button clicked")
                take_screenshot(page, "02_signin_clicked")

                # Wait for login to complete
                print("  Waiting for login to complete...")
                human_delay(4.0, 7.0)

                # Verify login
                current_url = page.url
                page_title = page.title()
                print(f"  After login URL: {current_url}")
                print(f"  After login title: {page_title}")
                take_screenshot(page, "02_after_login")

                # Check for error messages
                page_content = page.content()
                if "incorrect" in page_content.lower() or "invalid" in page_content.lower():
                    print("  ❌ Error: Invalid username or password")
                    take_screenshot(page, "02_invalid_credentials", full_page=True)
                    return False

                if "captcha" in page_content.lower() or "verification" in page_content.lower():
                    print("  ❌ Error: CAPTCHA or verification required")
                    print("  Please login manually once to solve CAPTCHA")
                    take_screenshot(page, "02_captcha_required", full_page=True)
                    dump_page_info(page, "captcha_required")
                    return False

                if "login" in current_url.lower():
                    print("  ❌ Error: Login failed — still on login page")
                    take_screenshot(page, "02_login_failed", full_page=True)
                    dump_page_info(page, "login_failed")
                    return False

                print("  ✅ Login successful")
                save_cookies(context)

            # ── Step 3: Navigate to problem ──────────────────────────────
            print("[3/5] Navigate to problem...")
            human_delay(1.0, 2.0)

            problem_url = f"https://leetcode.com/problems/{problem_slug}/"
            page.goto(problem_url, wait_until="domcontentloaded")
            human_delay(2.0, 4.0)

            # Wait for Cloudflare
            if not wait_for_cloudflare(page, "problem"):
                print("  ❌ Stuck on Cloudflare at problem page")
                take_screenshot(page, "03_problem_cloudflare", full_page=True)
                return False

            page_title = page.title()
            page_url = page.url
            print(f"  Problem page: {page_title}")
            print(f"  URL: {page_url}")
            take_screenshot(page, "03_problem_loaded")

            # Try to get problem title
            try:
                problem_title_elem = page.locator("a[href*='/problems/']").first
                if problem_title_elem.count() > 0:
                    problem_title = problem_title_elem.inner_text()
                    print(f"  Problem: {problem_title}")
            except Exception:
                pass

            if "404" in page.content() or "not found" in page.content().lower():
                print(f"  ❌ Problem '{problem_slug}' not found")
                take_screenshot(page, "03_problem_404")
                return False

            # ── Step 4: Enter code ───────────────────────────────────────
            print("[4/5] Entering code...")
            human_delay(1.0, 2.0)

            # Select language first
            print(f"  Setting language: {lang}")
            try:
                lang_selector = page.locator(
                    "button[data-testid='lang-select']"
                ).first
                if lang_selector.count() > 0:
                    human_click(page, lang_selector)
                    human_delay(0.5, 1.0)
                    lang_button = page.locator(f"div:has-text('{lang}')").first
                    if lang_button.count() > 0:
                        human_click(page, lang_button)
                        human_delay(0.5, 1.0)
            except Exception:
                pass

            # Click editor
            editor = page.locator(".monaco-editor").first
            if editor.count() > 0:
                human_click(page, editor)
                human_delay(0.3, 0.8)
                print("  Editor found and focused")

            # Clear existing code
            page.keyboard.press("Control+A")
            human_short_delay()
            page.keyboard.press("Delete")
            human_short_delay()

            # Type code with human-like delays
            page.keyboard.type(code, delay=random.randint(3, 8))
            print(f"  Code entered ({len(code)} chars)")
            human_delay(1.0, 2.0)
            take_screenshot(page, "04_code_entered")

            # ── Step 5: Submit ───────────────────────────────────────────
            print("[5/5] Submitting code...")
            human_delay(1.5, 3.0)

            # Primary method: Ctrl+Enter
            print("  Using Ctrl+Enter to submit...")
            try:
                editor = page.locator(".monaco-editor").first
                if editor.count() > 0:
                    human_click(page, editor)
                    human_delay(0.2, 0.5)

                page.keyboard.press("Control+Enter")
                print("  ✓ Ctrl+Enter pressed")
                human_delay(1.5, 3.0)
                take_screenshot(page, "05_submitted")
            except Exception as e:
                print(f"  Ctrl+Enter failed: {e}")

                # Fallback: Try submit button
                print("  Trying submit button...")
                try:
                    submit_btn = page.locator(
                        "button[data-e2e-locator='console-submit-button']"
                    ).first
                    if submit_btn.is_visible(timeout=5000):
                        human_click(page, submit_btn)
                        print("  ✓ Submit button clicked")
                        human_delay(1.5, 3.0)
                    else:
                        raise Exception("Submit button not visible")
                except Exception:
                    print("  ❌ Error: Could not submit solution")
                    take_screenshot(page, "05_submit_failed", full_page=True)
                    return False

            # ── Wait for result ──────────────────────────────────────────
            print("  Waiting for result", end="", flush=True)
            max_wait = 90
            start_time = time.time()
            last_state = None

            while time.time() - start_time < max_wait:
                page_text = page.locator("body").inner_text()

                # Detect state
                current_state = None
                for keyword in [
                    "Accepted",
                    "Wrong Answer",
                    "Runtime Error",
                    "Compile Error",
                    "Time Limit Exceeded",
                    "Memory Limit Exceeded",
                ]:
                    if keyword in page_text:
                        current_state = keyword
                        break
                if current_state is None and (
                    "Judging" in page_text or "Running" in page_text
                ):
                    current_state = "Running"

                if current_state != last_state and current_state:
                    print(f"\n  Status: {current_state}", end="", flush=True)
                    last_state = current_state

                # Terminal states
                if "Accepted" in page_text:
                    print("\n  ✅ Result: Accepted")
                    take_screenshot(page, "05_accepted")
                    return True

                for fail_reason in [
                    "Wrong Answer",
                    "Runtime Error",
                    "Compile Error",
                    "Time Limit Exceeded",
                    "Memory Limit Exceeded",
                ]:
                    if fail_reason in page_text:
                        print(f"\n  ❌ Result: {fail_reason}")
                        take_screenshot(page, f"05_{fail_reason.replace(' ', '_').lower()}")
                        return False

                print(".", end="", flush=True)
                time.sleep(random.uniform(1.5, 2.5))

            print("\n  ❌ Result: Timeout waiting for verdict")
            print(f"  Last page title: {page.title()}")
            take_screenshot(page, "05_timeout", full_page=True)
            return False

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            traceback.print_exc()
            try:
                take_screenshot(page, "error_exception", full_page=True)
                dump_page_info(page, "exception")
            except Exception:
                pass
            return False
        finally:
            browser.close()


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Submit LeetCode solutions using Playwright"
    )
    parser.add_argument(
        "--username",
        default=os.getenv("LEETCODE_USERNAME", ""),
        help="LeetCode username (or set LEETCODE_USERNAME env var)",
    )
    parser.add_argument(
        "--password",
        default=os.getenv("LEETCODE_PASSWORD", ""),
        help="LeetCode password (or set LEETCODE_PASSWORD env var)",
    )
    parser.add_argument(
        "--problem-slug",
        required=True,
        help="Problem slug (e.g.: two-sum)",
    )
    parser.add_argument(
        "--file",
        required=True,
        help="Solution file path",
    )
    parser.add_argument(
        "--lang",
        default="python3",
        help="Programming language",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="Run in headless mode",
    )
    parser.add_argument(
        "--show-browser",
        action="store_true",
        help="Show browser window (for debugging)",
    )
    parser.add_argument(
        "--save-cookies-only",
        action="store_true",
        help="Only login and save cookies, then exit (for initial setup)",
    )
    parser.add_argument(
        "--screenshot-dir",
        default=os.environ.get("SCREENSHOT_DIR", "/tmp/leetcode-screenshots"),
        help="Directory to save screenshots (default: /tmp/leetcode-screenshots)",
    )

    args = parser.parse_args()

    # Set global screenshot dir
    global SCREENSHOT_DIR
    SCREENSHOT_DIR = args.screenshot_dir
    ensure_screenshot_dir()

    # Special mode: Only save cookies
    if args.save_cookies_only:
        print("=== Cookie Setup Mode ===")
        print("This will open a browser for you to login manually.")
        print("After logging in successfully, press Ctrl+C to save cookies.\n")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=(
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
                ),
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
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n\nSaving cookies...")

            try:
                cookies = context.cookies()
                if cookies:
                    cookies_path = get_cookies_path()
                    with open(cookies_path, "w") as f:
                        json.dump(cookies, f, indent=2)
                    print(f"✅ {len(cookies)} cookies saved to {cookies_path}")
                    print(
                        "\n💡 You can now run submissions without "
                        "needing to login each time!"
                    )
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
    if not args.username or not args.password:
        print(
            "Error: Please provide LeetCode username and password",
            file=sys.stderr,
        )
        print("  Method 1: Pass --username and --password", file=sys.stderr)
        print(
            "  Method 2: Set LEETCODE_USERNAME and LEETCODE_PASSWORD env vars",
            file=sys.stderr,
        )
        print(
            "  Method 3 (RECOMMENDED): Use --save-cookies-only to login once",
            file=sys.stderr,
        )
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
