"""Pure strategy logic — no Playwright, no database calls, no I/O."""

STAKE_LADDER = [10,10,10,10,10,10,10,10,10]
CASHOUT_TARGET = 1.1


def next_stake(consecutive_losses: int) -> float:
    """Cycle through STAKE_LADDER; wraps back to start after the last entry."""
    idx = consecutive_losses % len(STAKE_LADDER)
    return STAKE_LADDER[idx]


def cashout_target() -> float:
    """Return the auto cashout multiplier."""
    return CASHOUT_TARGET
