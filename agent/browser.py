"""
browser.py — Playwright browser automation for the IT Admin Panel.
Rules: ONLY get_by_role / get_by_label / get_by_text. No CSS selectors.
"""

import time
from playwright.sync_api import sync_playwright, Page

from config import BASE_URL, BROWSER_HEADLESS, BROWSER_SLOW_MO


# ── Internal helpers ───────────────────────────────────────────────────────

def _launch():
    """Start Playwright and return (playwright, browser, page)."""
    pw      = sync_playwright().start()
    browser = pw.chromium.launch(headless=BROWSER_HEADLESS, slow_mo=BROWSER_SLOW_MO)
    page    = browser.new_page()
    return pw, browser, page


def _login(page: Page) -> None:
    """Navigate to /login and sign in with admin credentials."""
    print("[Browser] Opening login page...")
    page.goto(f"{BASE_URL}/login")
    time.sleep(0.5)

    print("[Browser] Filling credentials...")
    page.get_by_label("Username").fill("admin")
    time.sleep(0.3)
    page.get_by_label("Password").fill("admin")
    time.sleep(0.3)

    print("[Browser] Clicking Sign In...")
    page.get_by_role("button", name="Sign In").click()
    page.wait_for_url(f"{BASE_URL}/users", timeout=6000)
    print("[Browser] Logged in successfully.")
    time.sleep(0.4)


def _read_message(page: Page) -> str:
    """Read the on-screen result message if present."""
    try:
        el = page.locator(".message")
        el.wait_for(timeout=3000)
        return el.inner_text().strip()
    except Exception:
        return "(no message returned)"


# ── Public actions ─────────────────────────────────────────────────────────

def create_user(email: str, name: str) -> None:
    """
    Automate: login → navigate to Create User → fill form → submit.
    Raises on any failure so safe_execute can retry.
    """
    pw, browser, page = _launch()
    try:
        _login(page)

        print("[Browser] Navigating to Create User...")
        page.get_by_role("link", name="Create User").click()
        page.wait_for_url(f"{BASE_URL}/create-user", timeout=5000)
        time.sleep(0.4)

        print(f"[Browser] Filling Email Address: {email}")
        page.get_by_label("Email Address").fill(email)
        time.sleep(0.3)

        print(f"[Browser] Filling Full Name: {name}")
        page.get_by_label("Full Name").fill(name)
        time.sleep(0.3)

        print("[Browser] Clicking Create User...")
        page.get_by_role("button", name="Create User").click()
        time.sleep(1)

        msg = _read_message(page)
        print(f"[Browser] Result: {msg}")

        if "already exists" in msg.lower():
            raise RuntimeError(f"User already exists: {email}")

    finally:
        time.sleep(1.5)
        browser.close()
        pw.stop()


def reset_password(email: str) -> None:
    """
    Automate: login → find user row → click Reset Password.
    Raises on any failure so safe_execute can retry.
    """
    pw, browser, page = _launch()
    try:
        _login(page)

        print(f"[Browser] Locating row for {email}...")
        time.sleep(0.4)

        row = page.get_by_role("row").filter(has_text=email)
        if not row.count():
            raise RuntimeError(f"User '{email}' not found in the users table.")

        print("[Browser] Clicking Reset Password...")
        row.get_by_role("button", name="Reset Password").click()
        time.sleep(1)

        msg = _read_message(page)
        print(f"[Browser] Result: {msg}")

        if "not found" in msg.lower():
            raise RuntimeError(f"Backend reported user not found: {email}")

    finally:
        time.sleep(1.5)
        browser.close()
        pw.stop()
