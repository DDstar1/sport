"""Entry point: python -m strategy.runner"""
import asyncio
import json
import random
import time
from datetime import datetime

from playwright.async_api import async_playwright, Page, BrowserContext

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import config
from db import init_db, insert_trade
from auth import login, load_cookies
from strategy.engine import next_stake, cashout_target


# ── logging ───────────────────────────────────────────────────────────────────

def _log(msg: str) -> None:
    print(f"[{datetime.now().isoformat()}] {msg}")


# ── network resilience ────────────────────────────────────────────────────────

async def wait_for_network(max_wait: int = 600) -> None:
    """Block until the network is reachable, checking every 10s. Max wait in seconds."""
    _log("Network lost — waiting for reconnection...")
    for elapsed in range(0, max_wait, 10):
        await asyncio.sleep(10)
        try:
            import urllib.request
            urllib.request.urlopen("https://www.sportybet.com", timeout=5)
            _log(f"Network restored after ~{elapsed + 10}s")
            return
        except Exception:
            _log(f"Still offline... ({elapsed + 10}s elapsed)")
    _log("Network did not recover within max wait — continuing anyway")


# ── API ───────────────────────────────────────────────────────────────────────

def _api_headers() -> dict:
    return {
        "accept": "*/*",
        "accept-language": "en",
        "clientid": "web",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "operid": "2",
        "platform": "web",
    }


def _cookies_to_header(cookies: list[dict]) -> str:
    return "; ".join(f"{c['name']}={c['value']}" for c in cookies)


class SessionExpired(Exception):
    pass


async def _api_get(context: BrowserContext, url: str) -> dict:
    """GET a SportyBet API endpoint. Raises SessionExpired on empty/auth response."""
    cookies = await context.cookies()
    headers = {**_api_headers(), "cookie": _cookies_to_header(cookies)}
    response = await context.request.get(url, headers=headers)
    text = await response.text()
    if not text.strip():
        raise SessionExpired("Empty response — session likely expired")
    data = json.loads(text)
    if data.get("bizCode") == 10001 or data.get("bizCode") == 10002:
        raise SessionExpired(f"Auth error from API: bizCode={data.get('bizCode')}")
    return data


async def fetch_balance(context: BrowserContext) -> float | None:
    try:
        data = await _api_get(context, config.WALLET_API_URL)
        raw = (data.get("data") or {}).get("balance")
        if raw is not None:
            return float(raw) / 100
    except SessionExpired:
        raise
    except Exception as e:
        _log(f"Balance fetch error: {e}")
    return None


async def fetch_statements(context: BrowserContext) -> list[dict]:
    url = f"{config.STATEMENTS_API_URL}?type=0&pageSize=20&pageNo=1"
    try:
        data = await _api_get(context, url)
        return (data.get("data") or {}).get("statements", [])
    except SessionExpired:
        raise
    except Exception as e:
        _log(f"Statements fetch error: {e}")
    return []


# ── disconnect guard ──────────────────────────────────────────────────────────

async def check_disconnect(page: Page) -> bool:
    try:
        return await page.locator(config.DISCONNECT_SEL).is_visible()
    except Exception:
        return False


# ── iframe helpers ────────────────────────────────────────────────────────────

def _inner_frame(page: Page):
    """Return the game Frame object, found by URL (works in both headless and visible mode)."""
    for f in page.frames:
        if "aviator-next" in f.url:
            return f
    return None


async def wait_for_game(page: Page, timeout: int = 60_000) -> None:
    _log("Waiting for game to load...")
    deadline = time.time() + timeout / 1000
    frame = None
    while time.time() < deadline:
        frame = _inner_frame(page)
        if frame is not None:
            break
        await asyncio.sleep(1)
    if frame is None:
        raise RuntimeError("Game frame (aviator-next) never appeared")
    # Poll via JS until the bet button is in the DOM and visible
    await frame.wait_for_function(
        """() => {
            const btn = document.querySelector('button.btn-success.bet');
            if (!btn) return false;
            const s = window.getComputedStyle(btn);
            return s.display !== 'none' && s.visibility !== 'hidden' && parseFloat(s.opacity) > 0;
        }""",
        timeout=int((deadline - time.time()) * 1000),
    )
    _log("Game loaded")


# ── betting ───────────────────────────────────────────────────────────────────

async def place_bet(page: Page, stake: float, cashout: float) -> int:
    """
    Switch to Auto tab via JS, set stake, enable auto-cashout at `cashout`x,
    then click Bet. Returns the bet timestamp in ms for statement matching.
    """
    frame = _inner_frame(page)
    if frame is None:
        raise RuntimeError("Game frame not found")

    # 1. Click the first "Auto" tab found by text content — avoids index confusion
    #    (panel 2 has an extra "Previous" button that shifts indices)
    tab_result = await frame.evaluate("""() => {
        const secondRow = document.querySelector('.second-row');
        const alreadyOpen = secondRow && !secondRow.classList.contains('d-none');
        if (alreadyOpen) return 'already-open';

        const autoTab = Array.from(document.querySelectorAll('.navigation-switcher .tab'))
            .find(t => t.textContent.trim() === 'Auto');
        if (!autoTab) return 'no-tab';
        autoTab.click();
        return 'clicked';
    }""")
    _log(f"Auto tab: {tab_result}")

    # 2. Wait for .second-row to lose d-none (auto panel revealed)
    await frame.wait_for_function("""() => {
        const row = document.querySelector('.second-row');
        return row && !row.classList.contains('d-none');
    }""", timeout=15_000)
    _log("Auto panel visible")

    # 3. Set stake via Playwright locator (visible input)
    stake_input = frame.locator(config.BET_INPUT_SEL).first
    await stake_input.click(click_count=3)
    await stake_input.fill(str(int(stake)))
    _log(f"Stake: {stake} NGN")

    # 4. Enable auto-cashout toggle via JS if currently off
    toggle_result = await frame.evaluate("""() => {
        const toggle = document.querySelector('.cash-out-switcher .input-switch');
        if (!toggle) return 'not-found';
        if (!toggle.classList.contains('off')) return 'already-on';
        toggle.click();
        return 'clicked';
    }""")
    _log(f"Cashout toggle: {toggle_result}")
    if toggle_result == "clicked":
        await asyncio.sleep(0.4)

    # 5. Set cashout value via JS (input may be disabled to Playwright)
    fill_result = await frame.evaluate(f"""() => {{
        const input = document.querySelector('.cashout-spinner input[inputmode="decimal"]');
        if (!input) return 'not-found';
        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype, 'value').set;
        nativeInputValueSetter.call(input, '{cashout}');
        input.dispatchEvent(new Event('input', {{bubbles: true}}));
        return 'filled:' + input.value;
    }}""")
    _log(f"Cashout value: {fill_result}")

    # 6. Click Bet
    bet_time_ms = int(time.time() * 1000)
    await frame.locator(config.BET_BUTTON_SEL).first.click()
    _log(f"Bet placed: {stake} NGN @ {cashout}x")

    return bet_time_ms


# ── outcome detection ─────────────────────────────────────────────────────────

async def wait_for_outcome(context: BrowserContext, bet_time_ms: int) -> tuple[str, float]:
    """
    Poll statements until the round settles.
    Returns ('win', payout_ngn) or ('loss', 0.0).
    Network failures pause the poll and wait for reconnection — never counted as loss.
    """
    our_order_id: str | None = None
    pb_found_at: float | None = None
    network_fail_streak = 0
    start_time = time.time()
    last_status_log = 0.0

    while True:
        await asyncio.sleep(2)

        # Log progress every 15s so the user can see what we're waiting for
        now = time.time()
        if now - last_status_log >= 15:
            if our_order_id is None:
                _log(f"Waiting for bet to appear in statements... ({int(now - start_time)}s)")
            else:
                _log(f"Waiting for cashout (orderId={our_order_id})... ({int(now - pb_found_at)}s / 90s)")
            last_status_log = now

        try:
            stmts = await fetch_statements(context)
            network_fail_streak = 0
        except Exception:
            network_fail_streak += 1
            if network_fail_streak >= 3:
                _log("Network down during outcome poll — waiting for reconnection")
                await wait_for_network()
                network_fail_streak = 0
            continue

        if our_order_id is None:
            for s in stmts:
                if s.get("tradeCode") == "PB0001" and s.get("createTime", 0) >= bet_time_ms - 5000:
                    our_order_id = s["orderId"]
                    pb_found_at = time.time()
                    _log(f"Bet confirmed — orderId={our_order_id}")
                    break

            # If bet hasn't appeared in statements after 3 min, assume it didn't go through
            if our_order_id is None and time.time() - start_time > 180:
                _log("Bet never confirmed in statements after 3 min — treating as no-bet, retrying")
                return "no-bet", 0.0
        else:
            for s in stmts:
                if s.get("tradeCode") == "CB0001" and s.get("orderId") == our_order_id:
                    payout = s.get("amount", 0) / 100
                    _log(f"WIN — payout={payout} NGN")
                    return "win", payout

            # Only declare loss if network is healthy and 90s have passed with no CB0001
            if time.time() - pb_found_at > 90:
                _log(f"LOSS — no cashout for orderId={our_order_id}")
                return "loss", 0.0


# ── main loop ─────────────────────────────────────────────────────────────────

def _ask_headless() -> bool:
    """Prompt the user at startup to choose headless or visible browser."""
    while True:
        ans = input("Run browser headless (hidden)? [y/n]: ").strip().lower()
        if ans in ("y", "yes"):
            return True
        if ans in ("n", "no"):
            return False
        print("Please enter y or n.")


async def run() -> None:
    init_db()
    headless = _ask_headless()
    _log(f"Browser mode: {'headless' if headless else 'visible'}")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--use-gl=swiftshader",        # software WebGL renderer for headless
                "--enable-webgl",
                "--ignore-gpu-blocklist",
                "--disable-web-security",
                "--no-sandbox",
            ],
        )

        # Detect screen size → open at 90% width × 80% height
        _probe = await browser.new_page()
        screen = await _probe.evaluate("({w: window.screen.width, h: window.screen.height})")
        await _probe.close()
        vp_w = int(screen["w"] * 0.9)
        vp_h = int(screen["h"] * 0.8)
        _log(f"Screen {screen['w']}×{screen['h']} → window {vp_w}×{vp_h}")

        context = await browser.new_context(viewport={"width": vp_w, "height": vp_h})
        page = await context.new_page()
        await page.set_viewport_size({"width": vp_w, "height": vp_h})

        if not await load_cookies(context):
            await login(page, context)

        # Verify session is still valid — re-login if cookies have expired
        try:
            balance = await fetch_balance(context)
        except SessionExpired:
            _log("Saved cookies expired — re-logging in")
            await login(page, context)
            balance = await fetch_balance(context)

        _log(f"Opening balance: {balance} NGN")

        await page.goto(config.GAME_URL)
        await page.wait_for_load_state("networkidle")
        _log("Navigated to Aviator")
        await wait_for_game(page)

        consecutive_losses = 0

        while True:
            try:
                if await check_disconnect(page):
                    _log("Disconnect banner — reloading")
                    await page.reload()
                    await page.wait_for_load_state("networkidle")
                    await wait_for_game(page)
                    continue

                stake = next_stake(consecutive_losses)
                cashout = cashout_target()
                _log(f"--- stake={stake} NGN | cashout={cashout}x | losses={consecutive_losses} ---")

                try:
                    bet_time_ms = await place_bet(page, stake, cashout)
                except Exception as e:
                    _log(f"place_bet error: {e} — retrying in 10s")
                    await asyncio.sleep(10)
                    continue

                outcome, payout = await wait_for_outcome(context, bet_time_ms)

                try:
                    balance = await fetch_balance(context)
                except Exception:
                    balance = None

                insert_trade(
                    placed_at=datetime.fromtimestamp(bet_time_ms / 1000).isoformat(),
                    stake=stake,
                    cashout_target=cashout,
                    outcome=outcome,
                    payout=payout,
                    balance_after=balance,
                    consecutive_losses=consecutive_losses,
                )

                if outcome == "no-bet":
                    _log("Bet not confirmed — retrying without changing stake")
                    await asyncio.sleep(5)
                elif outcome == "win":
                    consecutive_losses = 0
                    _log(f"WIN +{payout} NGN | balance={balance} NGN — waiting 5s")
                    await asyncio.sleep(5)
                else:
                    consecutive_losses += 1
                    wait_secs = random.randint(2 * 60, 3 * 60)
                    mins, secs = divmod(wait_secs, 60)
                    _log(f"LOSS (consecutive={consecutive_losses}) | balance={balance} NGN — waiting {mins}m {secs}s")
                    await asyncio.sleep(wait_secs)

            except SessionExpired:
                _log("Session expired — re-logging in")
                try:
                    await login(page, context)
                    await page.goto(config.GAME_URL)
                    await page.wait_for_load_state("networkidle")
                    await wait_for_game(page)
                except Exception as relogin_err:
                    _log(f"Re-login failed: {relogin_err} — retrying in 30s")
                    await asyncio.sleep(30)

            except Exception as e:
                _log(f"Network/browser error: {e}")
                await wait_for_network()
                try:
                    await page.reload()
                    await page.wait_for_load_state("networkidle")
                    await wait_for_game(page)
                except Exception as reload_err:
                    _log(f"Reload failed: {reload_err} — retrying in 30s")
                    await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.run(run())
