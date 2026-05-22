import sqlite3
from config import DB_PATH


def init_db() -> None:
    """Create the database file and all tables if they don't exist."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rounds (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                multiplier  REAL    NOT NULL,
                recorded_at TEXT    NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                placed_at           TEXT    NOT NULL,
                stake               REAL    NOT NULL,
                cashout_target      REAL    NOT NULL,
                outcome             TEXT    NOT NULL,
                payout              REAL    NOT NULL,
                profit              REAL    NOT NULL,
                balance_after       REAL,
                consecutive_losses  INTEGER NOT NULL
            )
        """)
        conn.commit()


def insert_trade(
    placed_at: str,
    stake: float,
    cashout_target: float,
    outcome: str,
    payout: float,
    balance_after: float | None,
    consecutive_losses: int,
) -> None:
    """Record a completed trade (win or loss)."""
    profit = payout - stake
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """INSERT INTO trades
               (placed_at, stake, cashout_target, outcome, payout, profit, balance_after, consecutive_losses)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (placed_at, stake, cashout_target, outcome, payout, profit, balance_after, consecutive_losses),
        )
        conn.commit()


def get_all_trades() -> list[dict]:
    """Return all trades ordered by placed_at ascending."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM trades ORDER BY placed_at ASC")
        return [dict(row) for row in cursor.fetchall()]


def insert_round(multiplier: float, recorded_at: str) -> None:
    """Insert a single completed round into the database."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO rounds (multiplier, recorded_at) VALUES (?, ?)",
            (multiplier, recorded_at),
        )
        conn.commit()


def get_last_n_rounds(n: int) -> list[dict]:
    """Return the n most recent rounds as a list of dicts with keys: id, multiplier, recorded_at."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT id, multiplier, recorded_at FROM rounds ORDER BY recorded_at DESC LIMIT ?",
            (n,),
        )
        return [dict(row) for row in cursor.fetchall()]


def get_all_rounds() -> list[dict]:
    """Return all rounds ordered by recorded_at ascending."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT id, multiplier, recorded_at FROM rounds ORDER BY recorded_at ASC"
        )
        return [dict(row) for row in cursor.fetchall()]
