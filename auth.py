"""Shared login and cookie utilities."""
import json
from datetime import datetime
from pathlib import Path

from playwright.async_api import Page, BrowserContext

import config

COOKIES_FILE = Path("cookies.json")


def _log(msg: str) -> None:
    print(f"[{datetime.now().isoformat()}] {msg}")


async def login(page: Page, context: BrowserContext) -> None:
    """Log in to SportyBet and save cookies to cookies.json."""
    if not config.USERNAME or not config.PASSWORD:
        raise RuntimeError("SPORTYBET_USERNAME and SPORTYBET_PASSWORD must be set in your .env file")

    await page.goto(config.LOGIN_URL)

    await page.locator('input[name="phone"]').fill(config.USERNAME)
    await page.locator('input[type="password"]').fill(config.PASSWORD)
    await page.locator("button.af-button--primary").click()

    # Wait until we have actually left the login page, then wait for all
    # network activity (including session-cookie requests) to settle.
    await page.wait_for_url(lambda url: "/login" not in url, timeout=20_000)
    await page.wait_for_load_state("networkidle")

    cookies = await context.cookies()
    COOKIES_FILE.write_text(json.dumps(cookies, indent=2))
    _log(f"Logged in — {len(cookies)} cookies saved to {COOKIES_FILE}")


async def load_cookies(context: BrowserContext) -> bool:
    """Restore cookies from cookies.json if it exists. Returns True if loaded."""
    if not COOKIES_FILE.exists():
        return False
    cookies = json.loads(COOKIES_FILE.read_text())
    await context.add_cookies(cookies)
    _log(f"Restored {len(cookies)} cookies from {COOKIES_FILE}")
    return True
