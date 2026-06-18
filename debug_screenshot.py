"""Run headless, take screenshot when game stalls."""
import asyncio, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--use-gl=swiftshader",
                "--enable-webgl",
                "--ignore-gpu-blocklist",
                "--disable-web-security",
                "--no-sandbox",
                "--mute-audio",
                "--disable-extensions",
                "--disable-sync",
                "--disable-renderer-backgrounding",
                "--disable-backgrounding-occluded-windows",
                "--disable-background-timer-throttling",
            ],
        )
        context = await browser.new_context(viewport={"width": 1152, "height": 576})

        async def _block(route):
            if route.request.resource_type in ("image", "media", "font"):
                await route.abort()
            else:
                await route.continue_()
        await context.route("**/*", _block)

        page = await context.new_page()

        from auth import login, load_cookies
        import config, json
        from strategy.runner import fetch_balance, SessionExpired

        if not await load_cookies(context):
            print("No cookies — logging in...")
            await login(page, context)
        else:
            try:
                bal = await fetch_balance(context)
                print(f"Balance: {bal} NGN")
            except SessionExpired:
                print("Cookies expired — re-logging in...")
                await login(page, context)

        print("Navigating to game...")
        await page.goto("https://www.sportybet.com/ng/sportygames/turbo-games/aviator")
        await page.wait_for_load_state("domcontentloaded")

        # Wait for game frame
        game_frame = None
        for _ in range(30):
            for f in page.frames:
                if "aviator-next" in f.url:
                    game_frame = f
                    break
            if game_frame:
                break
            await asyncio.sleep(1)
        print(f"Game frame: {game_frame.url[:80] if game_frame else 'NOT FOUND'}")

        # Poll every 5s for up to 60s, screenshot each time
        for i in range(12):
            await asyncio.sleep(5)
            await page.screenshot(path=f"snap_{i:02d}.png")
            result = await game_frame.evaluate("""() => {
                const btn = document.querySelector('button.btn-success.bet');
                if (!btn) return 'no-button';
                const s = window.getComputedStyle(btn);
                return s.display + '|' + s.visibility + '|' + s.opacity + '|' + btn.textContent.trim().slice(0,20);
            }""") if game_frame else "no frame"
            print(f"  t={5*(i+1)}s — {result}")
            if "flex|visible|1" in str(result):
                print("  >>> Bet button visible!")
                break

        await browser.close()
        print("Done. Check snap_*.png files.")

asyncio.run(main())
