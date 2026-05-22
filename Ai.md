
# Aviator Automation Project

## Overview
A Python + Playwright project that automates interaction with the Aviator game
on SportyBet Nigeria (https://www.sportybet.com/ng/sportygames/turbo-games/aviator).

The project is split into two distinct sections:
1. **Data Collection** — passively observes the game and records round multipliers
2. **Strategy Engine** — uses collected data to make automated betting decisions

---

## Project Structure

```
aviator/
├── ai.md                        # This file
├── requirements.txt             # Python dependencies
├── config.py                    # Shared config (credentials, file paths, selectors)
├── db.py                        # Database setup and helper functions (SQLite)
│
├── collector/
│   ├── __init__.py
│   └── scraper.py               # Playwright script that watches the game and records multipliers
│
└── strategy/
    ├── __init__.py
    ├── engine.py                # Strategy logic — decides when to bet and at what cashout target
    └── runner.py                # Playwright script that executes the strategy in the live game
```

---

## Database (`db.py`)

Single SQLite file: `aviator.db`

### Table: `rounds`
| Column      | Type    | Description                              |
|-------------|---------|------------------------------------------|
| id          | INTEGER | Primary key, auto-increment              |
| multiplier  | REAL    | The final crash multiplier for the round |
| recorded_at | TEXT    | ISO 8601 timestamp when it was recorded  |

### Helper functions exposed by `db.py`
- `init_db()` — creates the database and table if they don't exist
- `insert_round(multiplier: float, recorded_at: str)` — saves a new round
- `get_all_rounds()` — returns all rounds as a list
- `get_last_n_rounds(n: int)` — returns the most recent n rounds

---

## Section 1 — Data Collector (`collector/`)

### What it does
- Opens the Aviator game page in a browser using Playwright
- Watches the iframe served by `launch.spribegaming.com/aviator`
- After each round, detects the latest multiplier result from the history bar
- Saves each new result to the `rounds` table in `aviator.db`

### Key Details
- Runs passively — does not place any bets
- Polls the game iframe DOM every second to detect new multipliers
- Deduplicates results so the same round is never recorded twice
- Can be left running indefinitely to build up a dataset
- Requires an active logged-in SportyBet session

### Entry Point
```bash
python -m collector.scraper
```

---

## Section 2 — Strategy Engine (`strategy/`)

### What it does
- `engine.py` — contains the strategy logic as a pure function or class
  - Reads recent round history from the database
  - Returns a decision: whether to bet, stake amount, and target cashout multiplier
- `runner.py` — connects the strategy to the live game via Playwright
  - Reads decisions from the engine
  - Places bets and triggers cashouts in the game iframe at the right moment

### Strategy Interface (`engine.py`)
```python
def should_bet(history: list[float]) -> bool:
    """Given recent multiplier history, return True if we should bet this round."""
    ...

def get_cashout_target(history: list[float]) -> float:
    """Return the multiplier at which to cash out."""
    ...
```

### Key Details
- Strategy logic is completely decoupled from the automation code
- The engine only deals with numbers — no browser or UI logic
- Swap strategies by editing `engine.py` without touching `runner.py`
- Queries the live `aviator.db` database for history

### Entry Point
```bash
python -m strategy.runner
```

---

## Tech Stack
- **Python 3.11+**
- **Playwright (async)** — browser automation
- **SQLite (stdlib)** — data storage via `sqlite3` module (no extra dependencies)
- **pandas** (optional) — for analysing collected data offline

## Dependencies (`requirements.txt`)
```
playwright
pandas
```

> Note: `sqlite3` is built into Python's standard library — no install needed.

---

## Development Phases

### Phase 1 — Data Collection (current focus)
- [ ] Set up project structure
- [ ] Implement `db.py` with schema and helper functions
- [ ] Inspect Aviator iframe DOM to find correct CSS selectors for multiplier history
- [ ] Implement `collector/scraper.py`
- [ ] Handle login flow
- [ ] Validate data is being recorded correctly in `aviator.db`

### Phase 2 — Strategy Development
- [ ] Query and analyse collected data from `aviator.db`
- [ ] Define and test strategy logic in `engine.py`
- [ ] Implement `strategy/runner.py` to execute bets in the live game
- [ ] Test on small bet amounts before scaling

---

## Important Notes
- Automating gameplay likely violates SportyBet's terms of service
- The collector (Phase 1) is purely observational and carries less risk
- Never hardcode credentials — use environment variables or a `.env` file
- The game iframe is cross-origin (`spribegaming.com`) — Playwright handles
  this natively via `frame_locator()`
```
