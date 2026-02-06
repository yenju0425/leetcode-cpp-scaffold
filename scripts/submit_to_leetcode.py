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
# Storage State Helpers (cookies + localStorage + IndexedDB)
# ============================================================================

def get_storage_state_dir():
    """Get the cache directory for storage state."""
    cache_dir = os.path.expanduser("~/.cache/leetcode-submit")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def get_storage_state_path():
    """Get the path to store Playwright storage state."""
    return os.path.join(get_storage_state_dir(), "storage_state.json")


def get_cookies_path():
    """Legacy cookies path (for backward compat)."""
    return os.path.join(get_storage_state_dir(), "cookies.json")


def has_saved_state():
    """Check if a saved storage state or cookies file exists."""
    return (
        os.path.exists(get_storage_state_path())
        or os.path.exists(get_cookies_path())
    )


def save_storage_state(context):
    """
    Save full browser storage state (cookies + localStorage).
    This is far more reliable than saving cookies alone.
    """
    try:
        state_path = get_storage_state_path()
        context.storage_state(path=state_path)
        print(f"  ✓ Storage state saved to {state_path}")
        # Also save cookies separately for backward compat
        try:
            cookies = context.cookies()
            cookies_path = get_cookies_path()
            with open(cookies_path, 'w') as f:
                json.dump(cookies, f, indent=2)
        except Exception:
            pass
        return True
    except Exception as e:
        print(f"  Warning: Failed to save storage state: {e}")
        # Fallback: save cookies only
        try:
            cookies = context.cookies()
            cookies_path = get_cookies_path()
            with open(cookies_path, 'w') as f:
                json.dump(cookies, f, indent=2)
            print(f"  ✓ Fallback: cookies saved to {cookies_path}")
            return True
        except Exception as e2:
            print(f"  Warning: Failed to save cookies: {e2}")
            return False


def load_storage_state_into_context(browser, base_context_options: dict):
    """
    Try to create a new browser context with saved storage state.
    Returns (context, True) if loaded, or (context, False) if no state found.

    Priority:
      1. storage_state.json (cookies + localStorage)
      2. cookies.json (legacy, cookies only)
      3. Fresh context (no saved state)
    """
    state_path = get_storage_state_path()
    cookies_path = get_cookies_path()

    # Try full storage state first
    if os.path.exists(state_path):
        try:
            context = browser.new_context(
                storage_state=state_path,
                **base_context_options,
            )
            print(f"  ✓ Loaded storage state from {state_path}")
            return context, True
        except Exception as e:
            print(f"  ⚠ Failed to load storage state: {e}")

    # Fallback: try legacy cookies
    if os.path.exists(cookies_path):
        try:
            context = browser.new_context(**base_context_options)
            with open(cookies_path, 'r') as f:
                cookies = json.load(f)
            context.add_cookies(cookies)
            print(f"  ✓ Loaded {len(cookies)} cookies from {cookies_path}")
            return context, True
        except Exception as e:
            print(f"  ⚠ Failed to load cookies: {e}")

    # No saved state
    context = browser.new_context(**base_context_options)
    return context, False


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
# Cloudflare Turnstile Checkbox Solver
# ============================================================================

def solve_turnstile(page, max_attempts: int = 3) -> bool:
    """
    Attempt to find and click the Cloudflare Turnstile "Verify you are human"
    checkbox.

    KEY INSIGHT: Turnstile renders its iframe inside a **closed shadow DOM**:
        <div>
          <template shadowrootmode="closed">
            <iframe src="https://challenges.cloudflare.com/..." />
          </template>
          <input type="hidden" name="cf-turnstile-response" />
        </div>

    Because the shadow root is CLOSED, normal DOM queries like
    page.locator("iframe[src*='challenges.cloudflare.com']")
    will NOT find it. However, Playwright's page.frames still lists
    all frames regardless of shadow DOM. We use that + frame_element()
    to get the bounding box and click it.

    Returns True if Turnstile appears solved, False otherwise.
    """
    print("  ── Attempting to solve Cloudflare Turnstile ──")

    for attempt in range(1, max_attempts + 1):
        print(f"  Attempt {attempt}/{max_attempts}")

        # ── Step A: Find Turnstile frame via page.frames ─────────────
        # (bypasses closed shadow DOM limitation)
        turnstile_frame = None
        turnstile_element = None
        box = None

        print("    Scanning page.frames for Turnstile...")
        all_frames = page.frames
        print(f"    Page has {len(all_frames)} frame(s):")
        for frame in all_frames:
            url = frame.url or "(about:blank)"
            print(f"      - {url[:120]}")
            if "challenges.cloudflare.com" in url or "turnstile" in url:
                turnstile_frame = frame
                print(f"    ✓ Found Turnstile frame: {url[:120]}")

        if turnstile_frame is not None:
            # Get the iframe's element handle to find its position on page
            try:
                turnstile_element = turnstile_frame.frame_element()
                box = turnstile_element.bounding_box()
            except Exception as e:
                print(f"    ⚠ Could not get frame element/bbox: {e}")

        # Fallback: also try locator-based search (in case shadow DOM is open)
        if box is None:
            print("    Trying locator-based fallback...")
            for selector in [
                "iframe[src*='challenges.cloudflare.com']",
                "iframe[title*='Cloudflare']",
                "iframe[title*='Widget containing']",
                "iframe[src*='turnstile']",
                "div.cf-turnstile iframe",
                "div.cf-turnstile",
                "div[class*='turnstile']",
            ]:
                try:
                    loc = page.locator(selector).first
                    if loc.count() > 0:
                        box = loc.bounding_box()
                        if box:
                            print(f"    ✓ Found via locator: {selector}")
                            break
                except Exception:
                    continue

        # Last resort: find the hidden input and estimate position
        if box is None:
            print("    Trying hidden input sibling method...")
            try:
                hidden = page.locator(
                    "input[name='cf-turnstile-response']"
                ).first
                if hidden.count() > 0:
                    # The Turnstile widget is the parent div of this input.
                    # Use JS to find the parent's bounding rect.
                    parent_box = hidden.evaluate(
                        """el => {
                            const parent = el.parentElement;
                            if (!parent) return null;
                            const rect = parent.getBoundingClientRect();
                            return {
                                x: rect.x, y: rect.y,
                                width: rect.width, height: rect.height
                            };
                        }"""
                    )
                    if parent_box and parent_box.get("width", 0) > 0:
                        box = parent_box
                        print(f"    ✓ Found via hidden input parent")
            except Exception as e:
                print(f"    Could not use hidden input method: {e}")

        if box is None:
            print("    ❌ Could not locate Turnstile widget at all")
            take_screenshot(page, f"turnstile_not_found_attempt{attempt}")
            if attempt < max_attempts:
                human_delay(2.0, 4.0)
                continue
            return False

        print(f"    Turnstile bbox: x={box['x']:.0f} y={box['y']:.0f} "
              f"w={box['width']:.0f} h={box['height']:.0f}")

        # ── Step B: Calculate checkbox click target ───────────────────
        # Turnstile widget is 300x65. Checkbox is on the left, ~28px in.
        checkbox_x = int(box["x"] + 28 + random.randint(-3, 3))
        checkbox_y = int(box["y"] + box["height"] / 2 + random.randint(-3, 3))

        print(f"    Clicking checkbox at ({checkbox_x}, {checkbox_y})")

        # ── Step C: Human-like approach and click ─────────────────────
        # Move mouse randomly first, then approach the checkbox
        human_mouse_move(page)
        human_delay(0.4, 1.0)

        # Natural path toward checkbox
        human_mouse_move(page, checkbox_x, checkbox_y)
        human_delay(0.15, 0.4)

        # Click!
        page.mouse.click(checkbox_x, checkbox_y)
        print("    ✓ Clicked Turnstile checkbox")
        take_screenshot(page, f"turnstile_clicked_attempt{attempt}")

        # ── Step D: Wait and verify ──────────────────────────────────
        print("    Waiting for Turnstile to verify...", end="", flush=True)
        for wait_i in range(40):  # up to 20 seconds
            time.sleep(0.5)
            print(".", end="", flush=True)

            # Check if Sign In button is now enabled
            try:
                sign_in = page.locator("button:has-text('Sign In')").first
                if sign_in.count() > 0 and not sign_in.is_disabled():
                    print(f"\n    ✅ Turnstile solved! (took ~{(wait_i+1)*0.5:.1f}s)")
                    take_screenshot(page, "turnstile_solved")
                    return True
            except Exception:
                pass

            # Also check the hidden response field — if it has a long value,
            # the challenge may have been completed
            try:
                resp = page.locator(
                    "input[name='cf-turnstile-response']"
                ).first
                if resp.count() > 0:
                    val = resp.get_attribute("value") or ""
                    if len(val) > 100:
                        # Response token populated — challenge likely passed
                        # Give it a moment for the button to enable
                        human_delay(0.5, 1.0)
                        try:
                            sign_in = page.locator(
                                "button:has-text('Sign In')"
                            ).first
                            if sign_in.count() > 0 and not sign_in.is_disabled():
                                print(f"\n    ✅ Turnstile solved via token! "
                                      f"(took ~{(wait_i+1)*0.5:.1f}s)")
                                take_screenshot(page, "turnstile_solved")
                                return True
                        except Exception:
                            pass
            except Exception:
                pass

        print("\n    ⚠ Turnstile did not resolve in 20s")
        take_screenshot(page, f"turnstile_timeout_attempt{attempt}")

        if attempt < max_attempts:
            print("    Retrying...")
            human_delay(2.0, 4.0)
            human_mouse_move(page)
            human_delay(1.0, 2.0)

    print("  ❌ All Turnstile solve attempts failed")
    take_screenshot(page, "turnstile_all_failed", full_page=True)
    dump_page_info(page, "turnstile_failed")
    return False


# ============================================================================
# Core Submission Logic
# ============================================================================

def submit_solution(
    username: str = "",
    password: str = "",
    problem_slug: str = "",
    code: str = "",
    lang: str = "cpp",
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

        base_context_options = dict(
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

        # Load saved storage state (cookies + localStorage) if available
        context, state_loaded = load_storage_state_into_context(
            browser, base_context_options
        )

        page = context.new_page()

        # Apply stealth scripts before any navigation
        apply_stealth(page)

        # Also inject stealth on every new document
        context.add_init_script(STEALTH_JS)

        try:
            # ── Step 1: Check for saved session ──────────────────────────
            print("[1/5] Checking for saved session...")

            is_logged_in = False
            if state_loaded:
                print("  Verifying saved session...")
                page.goto("https://leetcode.com/", wait_until="domcontentloaded")
                human_delay(1.5, 3.0)

                # Handle Cloudflare on initial load
                if not wait_for_cloudflare(page, "session_check", max_wait=15):
                    print("  ⚠ Cloudflare blocked session check")

                try:
                    page.goto(
                        "https://leetcode.com/profile/",
                        wait_until="domcontentloaded",
                        timeout=15000,
                    )
                    human_delay(1.0, 2.0)
                    wait_for_cloudflare(page, "profile_check", max_wait=10)
                    human_delay(0.5, 1.0)

                    if page.url.startswith("https://leetcode.com/u/"):
                        print("  ✅ Logged in with saved session!")
                        is_logged_in = True
                        take_screenshot(page, "01_session_restored")
                        # Re-save to refresh cookie expiry
                        save_storage_state(context)
                    else:
                        print(f"  ⚠ Session expired (redirected to {page.url})")
                        print("  Falling back to login...")
                except Exception as e:
                    print(f"  ⚠ Session check failed: {e}")
                    print("  Falling back to login...")
            else:
                print("  No saved session found, will attempt login")

            # ── Navigate to homepage first (warm up) ─────────────────────
            if not is_logged_in:
                # Check if we can even attempt login
                if not username or not password:
                    print("  ❌ No valid session and no credentials provided")
                    print("  💡 Run: python scripts/submit_to_leetcode.py --save-session")
                    return False

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

                # ── Solve Cloudflare Turnstile checkbox ──────────────────
                # Check if Sign In is already enabled (no Turnstile)
                login_btn_check = page.locator("button:has-text('Sign In')").first
                if login_btn_check.count() > 0 and login_btn_check.is_disabled():
                    print("  Sign In button is disabled — Turnstile detected")
                    turnstile_ok = solve_turnstile(page, max_attempts=3)
                    if not turnstile_ok:
                        print("  ❌ Could not solve Cloudflare Turnstile")
                        print("  💡 Tip: Run with --save-cookies-only to login")
                        print("     manually and save cookies for CI use.")
                        return False
                else:
                    print("  ✓ No Turnstile challenge (or already solved)")

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

                # Final safety check: wait a bit more for button to enable
                print("  Verifying Sign In button is enabled...")
                button_enabled = False
                max_button_wait = 10
                for i in range(max_button_wait * 2):
                    if not login_btn.is_disabled():
                        print("  ✓ Sign In button is enabled")
                        button_enabled = True
                        break
                    if i == 0:
                        print("  Button still disabled, waiting...")
                    time.sleep(0.5)

                if not button_enabled:
                    print(
                        f"  ❌ Error: Sign In button still disabled after "
                        f"{max_button_wait} seconds"
                    )
                    take_screenshot(page, "02_button_still_disabled", full_page=True)
                    dump_page_info(page, "button_disabled_final")

                    # Diagnostics: list all frames
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
                save_storage_state(context)

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
        "--save-session",
        action="store_true",
        help="Open browser to login manually and save full session "
             "(cookies + localStorage). Recommended for CI setup.",
    )
    # Legacy alias
    parser.add_argument(
        "--save-cookies-only",
        action="store_true",
        dest="save_session",
        help=argparse.SUPPRESS,
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

    # Special mode: Save session (cookies + localStorage + IndexedDB)
    if args.save_session:
        print("=== Session Setup Mode ===")
        print("This will open a browser for you to login manually.")
        print("After logging in, press Ctrl+C to save the full session.")
        print("(Saves cookies + localStorage — much more reliable than")
        print(" cookies alone!)\n")

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
            print("  3. Wait until you see LeetCode homepage (logged in)")
            print("  4. Press Ctrl+C in this terminal to save session")
            print("\nWaiting for you to login...")

            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n\nSaving session...")

            try:
                # Save full storage state (cookies + localStorage)
                state_path = get_storage_state_path()
                context.storage_state(path=state_path)
                print(f"✅ Full session saved to {state_path}")

                # Also save cookies separately for reference
                cookies = context.cookies()
                cookies_path = get_cookies_path()
                with open(cookies_path, "w") as f:
                    json.dump(cookies, f, indent=2)
                print(f"   ({len(cookies)} cookies also saved to {cookies_path})")

                print(
                    "\n💡 You can now run submissions without "
                    "needing to login each time!"
                )
                print(
                    "\n🔒 For CI: Base64-encode the state file and store "
                    "as a GitHub Secret:"
                )
                print(f"   base64 -w0 {state_path} | "
                      "pbcopy  # or xclip")
                print("   Then in CI, decode it back before running.")
                sys.exit(0)
            except Exception as e:
                print(f"❌ Error saving session: {e}")
                sys.exit(1)
            finally:
                browser.close()

    # Normal mode: Submit solution
    # Username/password are only required if no saved session exists
    if not has_saved_state():
        if not args.username or not args.password:
            print(
                "Error: No saved session found and no credentials provided.",
                file=sys.stderr,
            )
            print(
                "\nOption A (RECOMMENDED): Save session first:",
                file=sys.stderr,
            )
            print(
                "  python scripts/submit_to_leetcode.py --save-session",
                file=sys.stderr,
            )
            print(
                "\nOption B: Provide credentials:",
                file=sys.stderr,
            )
            print(
                "  --username USER --password PASS  or",
                file=sys.stderr,
            )
            print(
                "  LEETCODE_USERNAME / LEETCODE_PASSWORD env vars",
                file=sys.stderr,
            )
            sys.exit(1)

    # Read code file
    code_path = Path(args.file)
    if not code_path.exists():
        print(f"Error: File not found '{args.file}'", file=sys.stderr)
        sys.exit(1)

    code = code_path.read_text(encoding="utf-8")

    # Submit (credentials may be empty if relying on saved session)
    success = submit_solution(
        username=args.username or "",
        password=args.password or "",
        problem_slug=args.problem_slug,
        code=code,
        lang=args.lang,
        headless=not args.show_browser,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
