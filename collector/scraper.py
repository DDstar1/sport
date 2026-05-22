"""Entry point: python -m collector.scraper"""
import asyncio
from datetime import datetime

from playwright.async_api import async_playwright

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import config
from db import init_db, insert_round
from auth import login, load_cookies


async def main() -> None:
    """Launch browser, log in, and poll the Aviator iframe for new round results."""
    init_db()

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=config.HEADLESS)
        context = await browser.new_context()
        page = await context.new_page()

        if not await load_cookies(context):
            await login(page, context)

        # Navigate to game
        await page.goto(config.GAME_URL)
        iframe_locator = page.frame_locator(config.IFRAME_SEL)

        # Wait for multiplier history to be visible
        await iframe_locator.locator(config.MULTIPLIER_HISTORY_SEL).first.wait_for()

        # seen stores "multiplier_value|minute" combos so the same multiplier value
        # appearing in different rounds is still treated as distinct.
        seen: set[str] = set()

        print(f"[{datetime.now().isoformat()}] Collector started — watching for new rounds")

        while True:
            # Check for disconnect banner on the shell page
            try:
                if await page.locator(config.DISCONNECT_SEL).is_visible():
                    print(f"[{datetime.now().isoformat()}] Disconnect detected — reloading")
                    await page.reload()
                    await page.wait_for_load_state("networkidle")
            except Exception as e:
                print(f"[{datetime.now().isoformat()}] Disconnect check error: {e}")

            try:
                chips = await iframe_locator.locator(config.MULTIPLIER_HISTORY_SEL).all()
                now = datetime.now().isoformat()

                for chip in chips:
                    raw_text = await chip.inner_text()
                    clean = raw_text.strip().rstrip("x").strip()
                    if not clean:
                        continue

                    key = f"{clean}|{now[:16]}"
                    if key in seen:
                        continue

                    seen.add(key)
                    multiplier = float(clean)
                    insert_round(multiplier, now)
                    print(f"[{now}] {multiplier:.2f}x")

            except Exception as e:
                print(f"[{datetime.now().isoformat()}] WARNING: {e}")

            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
