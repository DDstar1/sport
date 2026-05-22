"""Pure strategy logic — no Playwright, no database calls, no I/O."""

STAKE_LADDER = [10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0,]
CASHOUT_TARGET = 1.1


def next_stake(consecutive_losses: int) -> float:
    """Return the stake for the current loss position: 10 → 100 → 1000."""
    idx = min(consecutive_losses, len(STAKE_LADDER) - 1)
    return STAKE_LADDER[idx]


def cashout_target() -> float:
    """Return the auto cashout multiplier."""
    return CASHOUT_TARGET
