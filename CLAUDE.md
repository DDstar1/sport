Here's a Claude Code-optimised `CLAUDE.md` that gives it everything it needs to build the full codebase from scratch:

---

```markdown
# CLAUDE.md — Aviator Automation Project

## What This Project Does
This is a Python + Playwright project that interacts with the Aviator crash game
on SportyBet Nigeria. It has two independent modules:

1. **Collector** — a passive scraper that watches the live Aviator game and 
   records every round's final crash multiplier into a SQLite database
2. **Strategy** — an engine that reads the collected data and makes automated 
   betting decisions in the live game

The two modules share a database but are otherwise fully decoupled.
Build Phase 1 (collector) first. Do not build Phase 2 until instructed.

---

## Tech Stack
- Python 3.11+
- Playwright (async API) for browser automation
- SQLite via Python's built-in `sqlite3` module (no ORM)
- python-dotenv for environment variables
- No frameworks, no heavy dependencies

---

## Project Structure

```
aviator/
├── CLAUDE.md
├── .env                         # Never commit this
├── .env.example                 # Commit this — shows required env vars
├── requirements.txt
├── config.py                    # Loads env vars, defines constants
├── db.py                        # All SQLite logic lives here
│
├── collector/
│   ├── __init__.py              # Empty
│   └── scraper.py               # Entry point for data collection
│
└── strategy/
    ├── __init__.py              # Empty
    ├── engine.py                # Pure strategy logic, no browser code
    └── runner.py                # Playwright automation that runs the strategy
```

---

## Environment Variables

### `.env.example`
```
SPORTYBET_USERNAME=
SPORTYBET_PASSWORD=
DB_PATH=aviator.db
HEADLESS=false
```

### `.env` (not committed)
Fill in real credentials here.

---

## config.py

Load all env vars here. Other modules import from config, never from dotenv directly.

```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

USERNAME = os.getenv("SPORTYBET_USERNAME")
PASSWORD = os.getenv("SPORTYBET_PASSWORD")
DB_PATH = os.getenv("DB_PATH", "aviator.db")
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"

# URLs
LOGIN_URL = "https://www.sportybet.com/ng/"
GAME_URL = "https://www.sportybet.com/ng/sportygames/turbo-games/aviator"

# Selectors — SportyBet shell
LOGIN_BUTTON_SEL = ""        # TODO: fill after DOM inspection
USERNAME_INPUT_SEL = ""      # TODO: fill after DOM inspection
PASSWORD_INPUT_SEL = ""      # TODO: fill after DOM inspection

# Selectors — Spribe iframe (cross-origin: launch.spribegaming.com)
IFRAME_SEL = "iframe[src*='spribegaming.com']"
MULTIPLIER_HISTORY_SEL = ""  # TODO: fill after DOM inspection — the row of past round results
BET_BUTTON_SEL = ""          # TODO: fill after DOM inspection
CASHOUT_BUTTON_SEL = ""      # TODO: fill after DOM inspection
BET_INPUT_SEL = ""           # TODO: fill after DOM inspection
```

> Note to Claude: The TODO selectors are intentionally blank. They will be 
> filled in after inspecting the live DOM. Do not guess them — leave them 
> as empty strings with the TODO comment.

---

## db.py

All database logic. Uses raw sqlite3, no ORM.

### Schema

**Table: `rounds`**
| Column       | Type    | Notes                                 |
|--------------|---------|---------------------------------------|
| id           | INTEGER | PRIMARY KEY AUTOINCREMENT             |
| multiplier   | REAL    | The crash multiplier e.g. 2.43        |
| recorded_at  | TEXT    | ISO 8601 timestamp e.g. 2026-05-21T10:00:01 |

### Functions to implement

```python
def init_db() -> None:
    """Create the database file and rounds table if they don't exist."""

def insert_round(multiplier: float, recorded_at: str) -> None:
    """Insert a single completed round into the database."""

def get_last_n_rounds(n: int) -> list[dict]:
    """Return the n most recent rounds as a list of dicts with keys: id, multiplier, recorded_at."""

def get_all_rounds() -> list[dict]:
    """Return all rounds ordered by recorded_at ascending."""
```

---

## collector/scraper.py

Entry point: `python -m collector.scraper`

### What it does
1. Calls `init_db()` to ensure the database exists
2. Launches a Playwright browser (headless based on config)
3. Navigates to `LOGIN_URL` and logs in using credentials from config
4. Navigates to `GAME_URL` and waits for the Spribe iframe to load
5. Enters a polling loop (every 1 second):
   - Reads all multiplier chips from `MULTIPLIER_HISTORY_SEL` inside the iframe
   - Compares against an in-memory set of already-seen values
   - Any new value gets inserted into the database via `insert_round()`
   - Prints each new entry to stdout: `[timestamp] 2.43x`
6. Runs until manually stopped with Ctrl+C

### Important implementation details
- Use `page.frame_locator(IFRAME_SEL)` to target the Spribe iframe
- Strip the "x" suffix from multiplier text before saving as float
- Use `datetime.now().isoformat()` for the timestamp
- Wrap the polling loop in try/except to handle mid-round DOM states gracefully
- The in-memory `seen` set should store multiplier+timestamp combos, 
  not just multipliers — the same multiplier value can appear in multiple rounds

---

## strategy/engine.py

Pure logic only. No Playwright, no database calls, no I/O.

### Functions to implement

```python
def should_bet(history: list[float]) -> bool:
    """
    Given a list of recent multipliers (most recent last),
    return True if the strategy says to place a bet this round.
    Placeholder implementation: always return True.
    """

def get_cashout_target(history: list[float]) -> float:
    """
    Given a list of recent multipliers (most recent last),
    return the multiplier at which to cash out.
    Placeholder implementation: always return 1.5.
    """

def get_stake_amount(history: list[float], balance: float) -> float:
    """
    Given recent history and current balance,
    return the stake amount in NGN.
    Placeholder implementation: always return 50.0.
    """
```

> Note to Claude: These are placeholders only. The real strategy logic 
> will be filled in later. Just implement the placeholders as described.

---

## strategy/runner.py

Entry point: `python -m strategy.runner`

> Note to Claude: Do not build this file yet. Create it as an empty module 
> with a single comment: `# Strategy runner — not yet implemented`.

---

## requirements.txt

```
playwright
python-dotenv
pandas
```

---

## How to Run

### Install dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### Set up environment
```bash
cp .env.example .env
# Fill in your SportyBet credentials in .env
```

### Run the collector
```bash
python -m collector.scraper
```

---

## Coding Conventions
- All async functions use `async/await` — no mixing with sync Playwright
- All database connections use context managers (`with sqlite3.connect(...)`)
- No global state except what is defined in `config.py`
- Every function has a docstring
- Errors are logged to stdout with a timestamp prefix
- No bare `except:` clauses — always catch specific exceptions or `Exception`

---

## What NOT to Do
- Do not use an ORM (SQLAlchemy, etc.) — raw sqlite3 only
- Do not hardcode credentials anywhere
- Do not guess CSS selectors — leave TODOs where marked
- Do not build `strategy/runner.py` until Phase 2 is started
- Do not install unnecessary packages
```

---

This is written specifically for how Claude Code reads context — it tells it exactly what to build, what to leave blank, what conventions to follow, and what to avoid. Just drop this file as `CLAUDE.md` in your project root and run `claude` in that directory.