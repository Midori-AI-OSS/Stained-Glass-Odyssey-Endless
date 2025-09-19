from __future__ import annotations

import asyncio
from dataclasses import dataclass
from dataclasses import field
from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta
import json
import math
import random
from typing import Any
from zoneinfo import ZoneInfo

from runs.encryption import get_save_manager

from autofighter.gacha import GachaManager
from plugins.damage_types import ALL_DAMAGE_TYPES

PT_ZONE = ZoneInfo("America/Los_Angeles")
RESET_OFFSET = timedelta(hours=2)
STATE_KEY = "login_rewards"
ROOMS_REQUIRED = 3

DAILY_RDR_BONUS_KEY = "daily_rdr_bonus"
DAILY_RDR_TIER_WIDTH = 0.15
DAILY_RDR_DIMINISHING_FACTOR = 10.0
DAILY_RDR_BASE_CHUNK = 1.0

STATE_LOCK = asyncio.Lock()


def _as_positive_int(value: Any, default: int = 0) -> int:
    try:
        converted = int(value)
    except (TypeError, ValueError):
        return default
    return max(converted, 0)


def _as_iso(value: Any) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None


def _normalize_reward_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    normalized: list[dict[str, Any]] = []
    for entry in value:
        if not isinstance(entry, dict):
            continue
        stars = _as_positive_int(entry.get("stars"), default=-1)
        if stars <= 0:
            continue
        damage_source = entry.get("damage_type") or entry.get("id") or entry.get("item_id")
        if not isinstance(damage_source, str) or not damage_source:
            continue
        damage_type = damage_source.split("_")[0].lower()
        item_id = entry.get("item_id")
        if not isinstance(item_id, str) or not item_id:
            item_id = f"{damage_type}_{stars}"
        name = entry.get("name")
        if not isinstance(name, str) or not name:
            name = f"{stars}★ {damage_type.title()} Prism"
        normalized.append(
            {
                "item_id": item_id,
                "damage_type": damage_type,
                "stars": stars,
                "name": name,
            }
        )
    return normalized


def _build_reward_entry(damage_type: str, stars: int) -> dict[str, Any]:
    lowered = damage_type.lower()
    return {
        "item_id": f"{lowered}_{stars}",
        "damage_type": lowered,
        "stars": stars,
        "name": f"{stars}★ {damage_type.title()} Prism",
    }


def _calculate_daily_rdr_bonus(rooms_completed: int, streak: int) -> float:
    extra_rooms = max(_as_positive_int(rooms_completed) - ROOMS_REQUIRED, 0)
    effective_streak = max(_as_positive_int(streak), 0)
    if extra_rooms <= 0 or effective_streak <= 0:
        return 0.0

    raw_bonus = 0.0001 * extra_rooms * effective_streak
    if raw_bonus <= 0:
        return 0.0

    if raw_bonus <= DAILY_RDR_BASE_CHUNK:
        return raw_bonus

    bonus = DAILY_RDR_BASE_CHUNK
    remainder = raw_bonus - DAILY_RDR_BASE_CHUNK
    tier_width = DAILY_RDR_TIER_WIDTH
    diminishing = DAILY_RDR_DIMINISHING_FACTOR

    if tier_width <= 0 or diminishing <= 1:
        return raw_bonus

    base_multiplier = 1.0 / diminishing
    tier_count = int(remainder // tier_width)
    if tier_count > 0:
        sum_multiplier = base_multiplier * (1.0 - math.pow(base_multiplier, tier_count)) / (1.0 - base_multiplier)
        bonus += tier_width * sum_multiplier

    partial = remainder - (tier_count * tier_width)
    if partial > 0:
        bonus += partial * math.pow(base_multiplier, tier_count + 1)

    return bonus


@dataclass(slots=True)
class LoginRewardState:
    streak: int = 0
    last_login_day: str | None = None
    last_login_at: str | None = None
    last_claim_day: str | None = None
    last_claim_at: str | None = None
    rooms_completed: int = 0
    rooms_day: str | None = None
    reward_day: str | None = None
    reward_items: list[dict[str, Any]] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> LoginRewardState:
        data = dict(raw or {})
        known = {
            "streak",
            "last_login_day",
            "last_login_at",
            "last_claim_day",
            "last_claim_at",
            "rooms_completed",
            "rooms_day",
            "reward_day",
            "reward_items",
        }
        extra = {key: value for key, value in data.items() if key not in known}
        return cls(
            streak=_as_positive_int(data.get("streak")),
            last_login_day=_as_iso(data.get("last_login_day")),
            last_login_at=_as_iso(data.get("last_login_at")),
            last_claim_day=_as_iso(data.get("last_claim_day")),
            last_claim_at=_as_iso(data.get("last_claim_at")),
            rooms_completed=_as_positive_int(data.get("rooms_completed")),
            rooms_day=_as_iso(data.get("rooms_day")),
            reward_day=_as_iso(data.get("reward_day")),
            reward_items=_normalize_reward_items(data.get("reward_items")),
            extra=extra,
        )

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "streak": int(self.streak),
            "last_login_day": self.last_login_day,
            "last_login_at": self.last_login_at,
            "last_claim_day": self.last_claim_day,
            "last_claim_at": self.last_claim_at,
            "rooms_completed": int(self.rooms_completed),
            "rooms_day": self.rooms_day,
            "reward_day": self.reward_day,
            "reward_items": [dict(item) for item in self.reward_items],
        }
        payload.update(self.extra)
        return payload


def _get_daily_rdr_bonus_value(state: LoginRewardState) -> float:
    extra = state.extra
    if not isinstance(extra, dict):
        extra = {}
        state.extra = extra

    value = extra.get(DAILY_RDR_BONUS_KEY, 0.0)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _update_daily_rdr_bonus(state: LoginRewardState) -> bool:
    if not isinstance(state.extra, dict):
        state.extra = {}

    bonus = _calculate_daily_rdr_bonus(state.rooms_completed, state.streak)
    previous = _get_daily_rdr_bonus_value(state)
    if DAILY_RDR_BONUS_KEY not in state.extra or not math.isclose(previous, bonus, rel_tol=1e-9, abs_tol=1e-9):
        state.extra[DAILY_RDR_BONUS_KEY] = bonus
        return True

    return False


def _ensure_timezone(now: datetime | None = None) -> datetime:
    if now is None:
        return datetime.now(tz=PT_ZONE)
    if now.tzinfo is None:
        return now.replace(tzinfo=PT_ZONE)
    return now.astimezone(PT_ZONE)


def _reward_day(now: datetime) -> date:
    return (now - RESET_OFFSET).date()


def _next_reset(now: datetime) -> datetime:
    current_day = _reward_day(now)
    next_day = current_day + timedelta(days=1)
    return datetime.combine(next_day, time(hour=2, tzinfo=PT_ZONE))


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _load_state_sync() -> dict[str, Any]:
    with get_save_manager().connection() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS options (key TEXT PRIMARY KEY, value TEXT)"
        )
        cur = conn.execute("SELECT value FROM options WHERE key = ?", (STATE_KEY,))
        row = cur.fetchone()
    if row and row[0]:
        try:
            data = json.loads(row[0])
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            return {}
    return {}


def _save_state_sync(state: dict[str, Any]) -> None:
    payload = json.dumps(state)
    with get_save_manager().connection() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS options (key TEXT PRIMARY KEY, value TEXT)"
        )
        conn.execute(
            "INSERT OR REPLACE INTO options (key, value) VALUES (?, ?)",
            (STATE_KEY, payload),
        )


async def _load_state() -> LoginRewardState:
    raw = await asyncio.to_thread(_load_state_sync)
    return LoginRewardState.from_dict(raw)


async def _save_state(state: LoginRewardState) -> None:
    await asyncio.to_thread(_save_state_sync, state.to_dict())


def _refresh_state(state: LoginRewardState, now: datetime, *, mark_login: bool) -> bool:
    reward_day = _reward_day(now)
    reward_day_iso = reward_day.isoformat()
    updated = False

    last_login_day = _parse_date(state.last_login_day)
    new_streak = _as_positive_int(state.streak, default=0)

    if last_login_day is None:
        if mark_login:
            new_streak = max(new_streak, 1)
    else:
        delta = (reward_day - last_login_day).days
        if delta > 1:
            new_streak = 1 if mark_login else min(new_streak, 1)
        elif delta == 1:
            if mark_login:
                new_streak = new_streak + 1 if new_streak >= 1 else 1
        elif delta < 0:
            new_streak = max(new_streak, 1)

    if mark_login and new_streak == 0:
        new_streak = 1

    if new_streak != state.streak:
        state.streak = new_streak
        updated = True

    if state.rooms_day != reward_day_iso:
        state.rooms_day = reward_day_iso
        state.rooms_completed = 0
        updated = True
    elif state.rooms_completed < 0:
        state.rooms_completed = 0
        updated = True

    if mark_login:
        if state.last_login_day != reward_day_iso:
            state.last_login_day = reward_day_iso
            state.last_login_at = now.isoformat()
            updated = True
        elif state.last_login_at is None:
            state.last_login_at = now.isoformat()
            updated = True

    if state.reward_day != reward_day_iso:
        state.reward_day = reward_day_iso
        state.reward_items = _generate_reward_items(state.streak)
        updated = True
    elif not state.reward_items:
        state.reward_items = _generate_reward_items(state.streak)
        updated = True

    if _update_daily_rdr_bonus(state):
        updated = True

    return updated


def _generate_reward_items(streak: int) -> list[dict[str, Any]]:
    pool = list(ALL_DAMAGE_TYPES)
    rewards: list[dict[str, Any]] = []
    one_star = 1 + max(streak, 0) // 7
    two_star = max(streak, 0) // 100

    for _ in range(one_star):
        rewards.append(_build_reward_entry(random.choice(pool), 1))

    for _ in range(two_star):
        rewards.append(_build_reward_entry(random.choice(pool), 2))

    return rewards


async def _apply_rewards(items: list[dict[str, Any]]) -> dict[str, int]:
    manager = GachaManager(get_save_manager())

    def update_inventory() -> dict[str, int]:
        inventory = manager._get_items()
        for entry in items:
            key = entry.get("item_id") or f"{entry['damage_type']}_{entry['stars']}"
            inventory[key] = inventory.get(key, 0) + 1
        manager._auto_craft(inventory)
        manager._set_items(inventory)
        return inventory

    return await asyncio.to_thread(update_inventory)


async def get_login_reward_status(now: datetime | None = None) -> dict[str, Any]:
    async with STATE_LOCK:
        state = await _load_state()
        current_time = _ensure_timezone(now)
        changed = _refresh_state(state, current_time, mark_login=True)

        reward_day = _reward_day(current_time)
        claimed_today = _parse_date(state.last_claim_day) == reward_day
        can_claim = state.rooms_completed >= ROOMS_REQUIRED and not claimed_today
        reset_at = _next_reset(current_time)

        status = {
            "streak": state.streak,
            "rooms_completed": state.rooms_completed,
            "rooms_required": ROOMS_REQUIRED,
            "can_claim": can_claim,
            "claimed_today": claimed_today,
            "reward_items": [dict(item) for item in state.reward_items],
            "daily_rdr_bonus": _get_daily_rdr_bonus_value(state),
            "seconds_until_reset": max(int((reset_at - current_time).total_seconds()), 0),
            "reset_at": reset_at.isoformat(),
        }

        if changed:
            await _save_state(state)

        return status


async def record_room_completion(now: datetime | None = None) -> None:
    async with STATE_LOCK:
        state = await _load_state()
        current_time = _ensure_timezone(now)
        changed = _refresh_state(state, current_time, mark_login=True)

        previous = state.rooms_completed
        state.rooms_completed = previous + 1
        if state.rooms_completed != previous:
            changed = True

        if _update_daily_rdr_bonus(state):
            changed = True

        if changed:
            await _save_state(state)


async def claim_login_reward(now: datetime | None = None) -> dict[str, Any]:
    async with STATE_LOCK:
        state = await _load_state()
        current_time = _ensure_timezone(now)
        _refresh_state(state, current_time, mark_login=True)

        reward_day = _reward_day(current_time)
        rooms_completed = state.rooms_completed
        claimed_today = _parse_date(state.last_claim_day) == reward_day

        if claimed_today:
            raise ValueError("reward already claimed")
        if rooms_completed < ROOMS_REQUIRED:
            raise ValueError("daily requirement not met")

        if not state.reward_items:
            state.reward_items = _generate_reward_items(state.streak)

        items = [dict(item) for item in state.reward_items]
        inventory = await _apply_rewards(items)

        state.last_claim_day = reward_day.isoformat()
        state.last_claim_at = current_time.isoformat()
        await _save_state(state)

        return {
            "streak": state.streak,
            "reward_items": items,
            "inventory": inventory,
        }


async def get_daily_rdr_bonus(now: datetime | None = None) -> float:
    async with STATE_LOCK:
        state = await _load_state()
        current_time = _ensure_timezone(now)
        changed = _refresh_state(state, current_time, mark_login=False)
        if changed:
            await _save_state(state)
        return _get_daily_rdr_bonus_value(state)
