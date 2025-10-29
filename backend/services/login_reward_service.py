from __future__ import annotations

import asyncio
import calendar
from dataclasses import dataclass
from dataclasses import field
from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta
import json
import math
import random
import threading
from typing import Any
from zoneinfo import ZoneInfo

from runs.encryption import get_save_manager
from tracking import log_login_event

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

DAILY_THEME_BONUS_KEY = "daily_theme_bonuses"

THEME_CONFIG: dict[int, dict[str, Any]] = {
    6: {
        "identifier": "exp_theme",
        "title": "EXP Overflow",
        "icon": "exp",
        "base_rate": 0.00001,
        "stat_bonuses": ("exp_multiplier",),
        "damage_types": (),
        "damage_adjustments": False,
        "drop_scope": "matching",
    },
    0: {
        "identifier": "fire_theme",
        "title": "Fire Infusion",
        "icon": "fire",
        "base_rate": 0.05,
        "stat_bonuses": (),
        "damage_types": (
            {"id": "fire", "label": "Fire", "icon": "fire"},
        ),
        "damage_adjustments": True,
        "drop_scope": "matching",
    },
    1: {
        "identifier": "ice_theme",
        "title": "Ice Harmony",
        "icon": "ice",
        "base_rate": 0.05,
        "stat_bonuses": (),
        "damage_types": (
            {"id": "ice", "label": "Ice", "icon": "ice"},
        ),
        "damage_adjustments": True,
        "drop_scope": "matching",
    },
    2: {
        "identifier": "light_dark_theme",
        "title": "Light & Dark Concord",
        "icon": "light-dark",
        "base_rate": 0.05,
        "stat_bonuses": (),
        "damage_types": (
            {"id": "light", "label": "Light", "icon": "light"},
            {"id": "dark", "label": "Dark", "icon": "dark"},
        ),
        "damage_adjustments": True,
        "drop_scope": "matching",
    },
    3: {
        "identifier": "wind_theme",
        "title": "Wind Uplift",
        "icon": "wind",
        "base_rate": 0.05,
        "stat_bonuses": (),
        "damage_types": (
            {"id": "wind", "label": "Wind", "icon": "wind"},
        ),
        "damage_adjustments": True,
        "drop_scope": "matching",
    },
    4: {
        "identifier": "lightning_theme",
        "title": "Lightning Flux",
        "icon": "lightning",
        "base_rate": 0.05,
        "stat_bonuses": (),
        "damage_types": (
            {"id": "lightning", "label": "Lightning", "icon": "lightning"},
        ),
        "damage_adjustments": True,
        "drop_scope": "matching",
    },
    5: {
        "identifier": "all_stats_theme",
        "title": "All-Stat Resonance",
        "icon": "all-stats",
        "base_rate": 0.000001,
        "stat_bonuses": (
            "all_stat_multiplier",
            "crit_rate_bonus",
            "crit_damage_bonus",
        ),
        "damage_types": (
            {"id": "all", "label": "All Elements", "icon": "all"},
        ),
        "damage_adjustments": False,
        "drop_scope": "all",
    },
}

STATE_LOCK = asyncio.Lock()
STATE_THREAD_LOCK = threading.RLock()
STATE_LOOP_INFO_LOCK = threading.Lock()
STATE_LOOP_INFO: tuple[asyncio.AbstractEventLoop, int] | None = None


def _register_state_loop(loop: asyncio.AbstractEventLoop) -> None:
    thread_id = threading.get_ident()
    with STATE_LOOP_INFO_LOCK:
        global STATE_LOOP_INFO
        STATE_LOOP_INFO = (loop, thread_id)


def _get_registered_state_loop() -> tuple[asyncio.AbstractEventLoop, int] | None:
    with STATE_LOOP_INFO_LOCK:
        info = STATE_LOOP_INFO
    if not info:
        return None
    loop, thread_id = info
    if loop.is_closed():
        return None
    return loop, thread_id


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


def _calculate_scaled_bonus(
    rooms_completed: int,
    streak: int,
    *,
    base_rate: float,
) -> float:
    extra_rooms = max(_as_positive_int(rooms_completed) - ROOMS_REQUIRED, 0)
    effective_streak = max(_as_positive_int(streak), 0)
    try:
        rate = float(base_rate)
    except (TypeError, ValueError):
        rate = 0.0
    if extra_rooms <= 0 or effective_streak <= 0 or rate <= 0:
        return 0.0

    raw_bonus = rate * extra_rooms * effective_streak
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


def _calculate_daily_rdr_bonus(rooms_completed: int, streak: int) -> float:
    return _calculate_scaled_bonus(rooms_completed, streak, base_rate=0.0001)


def _format_percent(value: float) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 0.0
    numeric = max(numeric, 0.0)
    percent = numeric * 100.0
    if percent >= 1000:
        return f"{percent:.0f}%"
    if percent >= 100:
        return f"{percent:.1f}%"
    return f"{percent:.2f}%"


def _percent_payload(value: float) -> dict[str, Any]:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 0.0
    numeric = max(numeric, 0.0)
    formatted = _format_percent(numeric)
    signed = formatted if numeric <= 0 else f"+{formatted}"
    return {
        "value": numeric,
        "percent": numeric * 100.0,
        "formatted": formatted,
        "formatted_with_sign": signed,
    }


def _build_theme_entry(
    weekday: int,
    config: dict[str, Any],
    rooms_completed: int,
    streak: int,
    scalar: float,
) -> dict[str, Any]:
    weekday_index = weekday % 7
    weekday_name = calendar.day_name[weekday_index]
    identifier = str(config.get("identifier") or f"theme_{weekday_index}")
    title = str(config.get("title") or identifier.replace("_", " ").title())
    base_rate = float(config.get("base_rate", 0.0) or 0.0)
    drop_scope = str(config.get("drop_scope", "matching") or "matching")
    adjustments = bool(config.get("damage_adjustments", False))

    entry: dict[str, Any] = {
        "weekday": weekday_index,
        "weekday_name": weekday_name,
        "identifier": identifier,
        "title": title,
        "label": f"{weekday_name} • {title}",
        "icon": str(config.get("icon") or identifier),
        "base_rate": base_rate,
        "rooms_completed": max(_as_positive_int(rooms_completed), 0),
        "streak": max(_as_positive_int(streak), 0),
        "bonus_value": float(scalar),
        "drop_scope": drop_scope,
        "stat_bonuses": {},
        "damage_types": [],
        "display": {
            "bonus_percent": _percent_payload(scalar),
        },
    }

    stat_entries: dict[str, Any] = {}
    for stat_name in config.get("stat_bonuses", ()):  # type: ignore[arg-type]
        key = str(stat_name)
        stat_entries[key] = _percent_payload(scalar)
    if stat_entries:
        entry["stat_bonuses"] = stat_entries

    damage_types: list[dict[str, Any]] = []
    for raw in config.get("damage_types", ()):  # type: ignore[arg-type]
        if not isinstance(raw, dict):
            continue
        type_id = str(raw.get("id") or "").lower() or "unknown"
        label = str(raw.get("label") or type_id.title())
        icon = str(raw.get("icon") or type_id)
        damage_value = scalar if adjustments else 0.0
        damage_types.append(
            {
                "id": type_id,
                "label": label,
                "icon": icon,
                "damage_bonus": damage_value,
                "damage_bonus_display": _percent_payload(damage_value),
                "damage_reduction": damage_value,
                "damage_reduction_display": _percent_payload(damage_value),
                "drop_weight_bonus": scalar,
                "drop_weight_display": _percent_payload(scalar),
            }
        )
    if damage_types:
        entry["damage_types"] = damage_types

    summary_parts: list[str] = []
    if stat_entries:
        for key, payload in stat_entries.items():
            formatted = payload["formatted_with_sign"]
            if key == "exp_multiplier":
                summary_parts.append(f"EXP gain {formatted}")
            elif key == "all_stat_multiplier":
                summary_parts.append(f"Core stats {formatted}")
            elif key == "crit_rate_bonus":
                summary_parts.append(f"Crit rate {formatted}")
            elif key == "crit_damage_bonus":
                summary_parts.append(f"Crit damage {formatted}")
            else:
                summary_parts.append(f"{key.replace('_', ' ').title()} {formatted}")
    if damage_types:
        type_names = "/".join(dt["label"] for dt in damage_types)
        drop_display = damage_types[0]["drop_weight_display"]["formatted_with_sign"]
        if adjustments and scalar > 0:
            damage_display = damage_types[0]["damage_bonus_display"]["formatted_with_sign"]
            reduction_display = damage_types[0]["damage_reduction_display"]["formatted_with_sign"]
            summary_parts.append(f"{type_names} damage dealt {damage_display}")
            summary_parts.append(f"{type_names} damage taken {reduction_display}")
        summary_parts.append(f"{type_names} drops {drop_display}")
    entry["display"]["summary"] = " • ".join(summary_parts) if summary_parts else ""

    return entry


def _build_theme_map(state: LoginRewardState, now: datetime) -> dict[str, Any]:
    entries: dict[int, dict[str, Any]] = {}
    for weekday, config in THEME_CONFIG.items():
        scalar = _calculate_scaled_bonus(
            state.rooms_completed,
            state.streak,
            base_rate=config.get("base_rate", 0.0),
        )
        entries[weekday] = _build_theme_entry(
            weekday,
            config,
            state.rooms_completed,
            state.streak,
            scalar,
        )

    active_weekday = _reward_day(now).weekday()
    payload = {
        "active_weekday": active_weekday,
        "active_theme": entries.get(active_weekday),
        "themes": {str(key): value for key, value in entries.items()},
        "updated_at": now.isoformat(),
    }
    return payload


def _get_daily_theme_bonus_value(state: LoginRewardState) -> dict[str, Any]:
    extra = state.extra
    if not isinstance(extra, dict):
        extra = {}
        state.extra = extra
    payload = extra.get(DAILY_THEME_BONUS_KEY)
    if isinstance(payload, dict):
        return payload
    return {
        "active_weekday": None,
        "active_theme": None,
        "themes": {},
    }


def _update_daily_theme_bonuses(
    state: LoginRewardState, now: datetime
) -> bool:
    if not isinstance(state.extra, dict):
        state.extra = {}

    payload = _build_theme_map(state, now)
    previous = state.extra.get(DAILY_THEME_BONUS_KEY)
    if previous != payload:
        state.extra[DAILY_THEME_BONUS_KEY] = payload
        return True
    return False


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
    with STATE_THREAD_LOCK:
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
    with STATE_THREAD_LOCK:
        with get_save_manager().connection() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS options (key TEXT PRIMARY KEY, value TEXT)"
            )
            conn.execute(
                "INSERT OR REPLACE INTO options (key, value) VALUES (?, ?)",
                (STATE_KEY, payload),
            )


async def _load_state() -> LoginRewardState:
    _register_state_loop(asyncio.get_running_loop())
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

    if _update_daily_theme_bonuses(state, now):
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


async def _attempt_grant_login_reward(
    state: LoginRewardState,
    current_time: datetime,
) -> tuple[str, dict[str, Any] | None]:
    reward_day = _reward_day(current_time)
    claimed_today = _parse_date(state.last_claim_day) == reward_day
    if claimed_today:
        return "already_claimed", None

    rooms_completed = state.rooms_completed
    if rooms_completed < ROOMS_REQUIRED:
        return "requirement_not_met", None

    if not state.reward_items:
        state.reward_items = _generate_reward_items(state.streak)

    items = [dict(item) for item in state.reward_items]
    inventory = await _apply_rewards(items)

    state.last_claim_day = reward_day.isoformat()
    state.last_claim_at = current_time.isoformat()
    await _save_state(state)

    payload = {
        "streak": state.streak,
        "reward_items": items,
        "inventory": inventory,
    }
    return "granted", payload


async def get_login_reward_status(now: datetime | None = None) -> dict[str, Any]:
    async with STATE_LOCK:
        state = await _load_state()
        current_time = _ensure_timezone(now)
        changed = _refresh_state(state, current_time, mark_login=True)
        try:
            await log_login_event("local", "login_reward_status", True, {"changed": changed})
        except Exception:
            pass

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
            "daily_theme": _get_daily_theme_bonus_value(state),
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
        try:
            await log_login_event("local", "login_reward_status", True, {"changed": changed})
        except Exception:
            pass

        previous = state.rooms_completed
        state.rooms_completed = previous + 1
        if state.rooms_completed != previous:
            changed = True

        if _update_daily_rdr_bonus(state):
            changed = True

        if _update_daily_theme_bonuses(state, current_time):
            changed = True

        auto_granted = False
        grant_error: Exception | None = None
        if state.rooms_completed >= ROOMS_REQUIRED:
            try:
                result, _ = await _attempt_grant_login_reward(state, current_time)
            except Exception as error:  # noqa: BLE001 - ensure room progress is persisted first
                grant_error = error
            else:
                auto_granted = result == "granted"

        if changed and (grant_error is not None or not auto_granted):
            await _save_state(state)

        if grant_error is not None:
            raise grant_error


async def claim_login_reward(now: datetime | None = None) -> dict[str, Any]:
    async with STATE_LOCK:
        state = await _load_state()
        current_time = _ensure_timezone(now)
        _refresh_state(state, current_time, mark_login=True)

        result, payload = await _attempt_grant_login_reward(state, current_time)
        if result == "already_claimed":
            raise ValueError("reward already claimed")
        if result == "requirement_not_met":
            raise ValueError("daily requirement not met")
        if payload is None:
            raise ValueError("unable to grant reward")
        return payload


async def get_daily_rdr_bonus(now: datetime | None = None) -> float:
    async with STATE_LOCK:
        state = await _load_state()
        current_time = _ensure_timezone(now)
        changed = _refresh_state(state, current_time, mark_login=False)
        if changed:
            await _save_state(state)
        return _get_daily_rdr_bonus_value(state)


def get_daily_rdr_bonus_sync(now: datetime | None = None) -> float:
    current_time = _ensure_timezone(now)
    loop_info = _get_registered_state_loop()
    if loop_info:
        loop, thread_id = loop_info
        if loop.is_running() and thread_id != threading.get_ident():
            try:
                future = asyncio.run_coroutine_threadsafe(
                    get_daily_rdr_bonus(current_time),
                    loop,
                )
            except RuntimeError:
                pass
            else:
                return future.result()
    with STATE_THREAD_LOCK:
        raw_state = _load_state_sync()
        state = LoginRewardState.from_dict(raw_state)
        changed = _refresh_state(state, current_time, mark_login=False)
        if changed:
            _save_state_sync(state.to_dict())
        return _get_daily_rdr_bonus_value(state)


async def get_daily_theme_bonuses(now: datetime | None = None) -> dict[str, Any]:
    async with STATE_LOCK:
        state = await _load_state()
        current_time = _ensure_timezone(now)
        changed = _refresh_state(state, current_time, mark_login=False)
        theme_changed = _update_daily_theme_bonuses(state, current_time)
        if changed or theme_changed:
            await _save_state(state)
        return _get_daily_theme_bonus_value(state)


def get_daily_theme_bonuses_sync(now: datetime | None = None) -> dict[str, Any]:
    current_time = _ensure_timezone(now)
    loop_info = _get_registered_state_loop()
    if loop_info:
        loop, thread_id = loop_info
        if loop.is_running() and thread_id != threading.get_ident():
            try:
                future = asyncio.run_coroutine_threadsafe(
                    get_daily_theme_bonuses(current_time),
                    loop,
                )
            except RuntimeError:
                pass
            else:
                return future.result()
    with STATE_THREAD_LOCK:
        raw_state = _load_state_sync()
        state = LoginRewardState.from_dict(raw_state)
        changed = _refresh_state(state, current_time, mark_login=False)
        theme_changed = _update_daily_theme_bonuses(state, current_time)
        if changed or theme_changed:
            _save_state_sync(state.to_dict())
        return _get_daily_theme_bonus_value(state)
