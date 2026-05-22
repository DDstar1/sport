"""Run this to find the correct iframe selectors on the Aviator page."""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright
import config
from auth import load_cookies


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        if not await load_cookies(context):
            print("No cookies.json found — log in first via strategy.runner")
            return

        await page.goto(config.GAME_URL)
        await page.wait_for_load_state("networkidle")

        # Give the game extra time to render
        await asyncio.sleep(5)

        # Dump every iframe's id, class, src
        iframes = await page.evaluate("""() => {
            const frames = Array.from(document.querySelectorAll('iframe'));
            return frames.map(f => ({
                id: f.id,
                className: f.className,
                src: f.src,
                name: f.name,
            }));
        }""")

        print("\\n=== Top-level iframes ===")
        for f in iframes:
            print(f)

        # Screenshot so you can see what loaded
        await page.screenshot(path="debug_aviator.png", full_page=True)
        print("\\nScreenshot saved to debug_aviator.png")

        # Try to read iframes inside the first iframe
        for frame in page.frames:
            print(f"\\nFrame URL: {frame.url}")
            try:
                nested = await frame.evaluate("""() => {
                    const frames = Array.from(document.querySelectorAll('iframe'));
                    return frames.map(f => ({
                        id: f.id,
                        className: f.className,
                        src: f.src,
                    }));
                }""")
                if nested:
                    print(f"  Nested iframes: {nested}")
            except Exception as e:
                print(f"  (can't inspect: {e})")

        await browser.close()


asyncio.run(main())
