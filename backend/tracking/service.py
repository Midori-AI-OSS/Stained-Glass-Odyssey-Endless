"""Async helpers for writing tracking telemetry."""
from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from collections.abc import Callable
from typing import Any

from .manager import get_tracking_manager

log = logging.getLogger(__name__)


async def _execute(write: Callable[[Any], None]) -> None:
    manager = get_tracking_manager()

    def runner() -> None:
        with manager.connection() as conn:
            write(conn)

    try:
        await asyncio.to_thread(runner)
    except Exception:  # pragma: no cover - defensive logging
        log.exception("Failed to record tracking event")


def _now() -> int:
    return int(time.time())


def _dump(details: Any) -> str:
    if details is None:
        return "{}"
    if isinstance(details, str):
        return details
    try:
        return json.dumps(details)
    except Exception:
        return json.dumps({"value": str(details)})


async def log_run_start(
    run_id: str,
    start_ts: int,
    members: list[dict[str, Any]],
    outcome: str | None = None,
) -> None:
    def write(conn: Any) -> None:
        conn.execute(
            "INSERT OR REPLACE INTO runs (run_id, start_ts, end_ts, outcome) VALUES (?, ?, ?, ?)",
            (run_id, start_ts, None, outcome),
        )
        conn.execute("DELETE FROM party_members WHERE run_id = ?", (run_id,))
        for member in members:
            slot = int(member.get("slot", 0))
            stats = member.get("stats", {})
            conn.execute(
                "INSERT OR REPLACE INTO party_members (run_id, slot, character_id, stats_json) VALUES (?, ?, ?, ?)",
                (
                    run_id,
                    slot,
                    member.get("character_id", "unknown"),
                    _dump(stats),
                ),
            )

    await _execute(write)


async def log_run_end(run_id: str, outcome: str, end_ts: int | None = None) -> None:
    if end_ts is None:
        end_ts = _now()

    def write(conn: Any) -> None:
        conn.execute(
            "UPDATE runs SET end_ts = ?, outcome = ? WHERE run_id = ?",
            (end_ts, outcome, run_id),
        )

    await _execute(write)


async def log_play_session_start(session_id: str, user_id: str, login_ts: int | None = None) -> None:
    login_ts = login_ts or _now()

    def write(conn: Any) -> None:
        conn.execute(
            "INSERT OR REPLACE INTO play_sessions (session_id, user_id, login_ts, logout_ts, duration) VALUES (?, ?, ?, NULL, NULL)",
            (session_id, user_id, login_ts),
        )

    await _execute(write)


async def log_play_session_end(session_id: str, logout_ts: int | None = None) -> None:
    logout_ts = logout_ts or _now()

    def write(conn: Any) -> None:
        cur = conn.execute(
            "SELECT login_ts FROM play_sessions WHERE session_id = ?",
            (session_id,),
        )
        row = cur.fetchone()
        if not row:
            conn.execute(
                "INSERT OR REPLACE INTO play_sessions (session_id, user_id, login_ts, logout_ts, duration) VALUES (?, ?, ?, ?, 0)",
                (session_id, "unknown", logout_ts, logout_ts),
            )
            return
        login_ts = int(row[0])
        duration = max(logout_ts - login_ts, 0)
        conn.execute(
            "UPDATE play_sessions SET logout_ts = ?, duration = ? WHERE session_id = ?",
            (logout_ts, duration, session_id),
        )

    await _execute(write)


async def log_card_acquisition(
    run_id: str,
    room_id: str | None,
    card_id: str,
    source: str,
    ts: int | None = None,
) -> None:
    ts = ts or _now()

    def write(conn: Any) -> None:
        conn.execute(
            "INSERT INTO cards (run_id, room_id, card_id, source, ts) VALUES (?, ?, ?, ?, ?)",
            (run_id, room_id, card_id, source, ts),
        )

    await _execute(write)


async def log_relic_acquisition(
    run_id: str,
    room_id: str | None,
    relic_id: str,
    source: str,
    ts: int | None = None,
) -> None:
    ts = ts or _now()

    def write(conn: Any) -> None:
        conn.execute(
            "INSERT INTO relics (run_id, room_id, relic_id, source, ts) VALUES (?, ?, ?, ?, ?)",
            (run_id, room_id, relic_id, source, ts),
        )

    await _execute(write)


async def log_battle_summary(
    run_id: str,
    room_id: str | None,
    turns: int,
    dmg_dealt: int,
    dmg_taken: int,
    victory: bool,
    ts: int | None = None,
) -> None:
    ts = ts or _now()
    def write(conn: Any) -> None:
        conn.execute(
            "INSERT INTO battle_summaries (run_id, room_id, turns, dmg_dealt, dmg_taken, victory, ts) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (run_id, room_id, turns, dmg_dealt, dmg_taken, 1 if victory else 0, ts),
        )

    await _execute(write)


async def log_menu_action(menu_item: str, result: str, details: Any | None = None) -> None:
    action_id = str(uuid.uuid4())
    ts = _now()

    def write(conn: Any) -> None:
        conn.execute(
            "INSERT INTO menu_actions (action_id, ts, menu_item, result, details_json) VALUES (?, ?, ?, ?, ?)",
            (action_id, ts, menu_item, result, _dump(details)),
        )

    await _execute(write)


async def log_game_action(
    action_type: str,
    *,
    run_id: str | None = None,
    room_id: str | None = None,
    details: Any | None = None,
    ts: int | None = None,
) -> None:
    ts = ts or _now()

    def write(conn: Any) -> None:
        conn.execute(
            "INSERT INTO game_actions (run_id, room_id, action_type, ts, details_json) VALUES (?, ?, ?, ?, ?)",
            (run_id, room_id, action_type, ts, _dump(details)),
        )

    await _execute(write)


async def log_settings_change(setting: str, old_value: Any, new_value: Any) -> None:
    action_id = str(uuid.uuid4())
    ts = _now()

    def write(conn: Any) -> None:
        conn.execute(
            "INSERT INTO settings_changes (action_id, ts, setting, old_value, new_value) VALUES (?, ?, ?, ?, ?)",
            (action_id, ts, setting, None if old_value is None else str(old_value), None if new_value is None else str(new_value)),
        )

    await _execute(write)


async def log_deck_change(
    run_id: str | None,
    room_id: str | None,
    change_type: str,
    card_id: str | None,
    details: Any | None = None,
    ts: int | None = None,
) -> None:
    ts = ts or _now()

    def write(conn: Any) -> None:
        conn.execute(
            "INSERT INTO deck_changes (run_id, room_id, change_type, card_id, ts, details_json) VALUES (?, ?, ?, ?, ?, ?)",
            (run_id, room_id, change_type, card_id, ts, _dump(details)),
        )

    await _execute(write)


async def log_shop_transaction(
    run_id: str | None,
    room_id: str | None,
    item_type: str | None,
    item_id: str | None,
    cost: int | None,
    action: str,
    details: Any | None = None,
    ts: int | None = None,
) -> None:
    ts = ts or _now()

    def write(conn: Any) -> None:
        conn.execute(
            "INSERT INTO shop_transactions (run_id, room_id, item_type, item_id, cost, action, ts) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (run_id, room_id, item_type, item_id, cost, action, ts),
        )

    await _execute(write)
    if item_type == "card" and item_id:
        await log_deck_change(run_id, room_id, "shop_purchase", item_id, details, ts=ts)


async def log_event_choice(
    run_id: str | None,
    room_id: str | None,
    event_name: str,
    choice: str | None,
    outcome: Any | None = None,
    ts: int | None = None,
) -> None:
    ts = ts or _now()

    def write(conn: Any) -> None:
        conn.execute(
            "INSERT INTO event_choices (run_id, room_id, event_name, choice, outcome_json, ts) VALUES (?, ?, ?, ?, ?, ?)",
            (run_id, room_id, event_name, choice, _dump(outcome), ts),
        )

    await _execute(write)


async def log_overlay_action(overlay: str, details: Any | None = None) -> None:
    action_id = str(uuid.uuid4())
    ts = _now()

    def write(conn: Any) -> None:
        conn.execute(
            "INSERT INTO overlay_actions (action_id, ts, overlay, details_json) VALUES (?, ?, ?, ?)",
            (action_id, ts, overlay, _dump(details)),
        )

    await _execute(write)


async def log_character_pull(
    character_id: str,
    rarity: str,
    source: str,
    *,
    ts: int | None = None,
    pull_id: str | None = None,
) -> None:
    ts = ts or _now()
    pull_id = pull_id or str(uuid.uuid4())

    def write(conn: Any) -> None:
        conn.execute(
            "INSERT OR REPLACE INTO character_pulls (pull_id, ts, character_id, rarity, source) VALUES (?, ?, ?, ?, ?)",
            (pull_id, ts, character_id, rarity, source),
        )

    await _execute(write)


async def log_login_event(
    user_id: str,
    method: str,
    success: bool,
    details: Any | None = None,
    ts: int | None = None,
) -> None:
    event_id = str(uuid.uuid4())
    ts = ts or _now()

    def write(conn: Any) -> None:
        conn.execute(
            "INSERT INTO login_events (event_id, ts, user_id, method, success, details_json) VALUES (?, ?, ?, ?, ?, ?)",
            (event_id, ts, user_id, method, 1 if success else 0, _dump(details)),
        )

    await _execute(write)


async def log_achievement_unlock(
    run_id: str | None,
    achievement_id: str,
    details: Any | None = None,
    ts: int | None = None,
) -> None:
    ts = ts or _now()

    def write(conn: Any) -> None:
        conn.execute(
            "INSERT INTO achievement_unlocks (run_id, achievement_id, ts, details_json) VALUES (?, ?, ?, ?)",
            (run_id, achievement_id, ts, _dump(details)),
        )

    await _execute(write)
