from __future__ import annotations

import asyncio

from autofighter.party import Party
from autofighter.stats import apply_status_hooks


def user_exp_to_level(level: int) -> int:
    base = 100
    return int(base * (1.05 ** (level - 1)))


def get_user_state() -> dict[str, int]:
    from game import get_save_manager

    with get_save_manager().connection() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS options (key TEXT PRIMARY KEY, value TEXT)"
        )
        row = conn.execute(
            "SELECT value FROM options WHERE key = ?", ("user_level",)
        ).fetchone()
        try:
            level = int(row[0]) if row else 1
        except (TypeError, ValueError):
            level = 1
        row = conn.execute(
            "SELECT value FROM options WHERE key = ?", ("user_exp",)
        ).fetchone()
        try:
            exp = int(row[0]) if row else 0
        except (TypeError, ValueError):
            exp = 0
    next_level_exp = user_exp_to_level(level)
    return {"level": level, "exp": exp, "next_level_exp": next_level_exp}


def get_user_level() -> int:
    return get_user_state()["level"]


async def gain_user_exp(amount: int) -> dict[str, int]:
    if amount <= 0:
        return get_user_state()
    state = get_user_state()
    exp = state["exp"] + amount
    level = state["level"]
    next_exp = user_exp_to_level(level)
    while exp >= next_exp:
        exp -= next_exp
        level += 1
        next_exp = user_exp_to_level(level)
    await _persist_user_state(level, exp)
    return {"level": level, "exp": exp, "next_level_exp": next_exp}


async def _persist_user_state(level: int, exp: int) -> None:
    await asyncio.to_thread(_write_user_state, level, exp)


def _write_user_state(level: int, exp: int) -> None:
    from game import get_save_manager

    with get_save_manager().connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO options (key, value) VALUES (?, ?)",
            ("user_level", str(level)),
        )
        conn.execute(
            "INSERT OR REPLACE INTO options (key, value) VALUES (?, ?)",
            ("user_exp", str(exp)),
        )


def apply_user_level_to_party(party: Party) -> None:
    for member in party.members:
        apply_status_hooks(member)
