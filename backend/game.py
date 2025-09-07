from __future__ import annotations

import asyncio
import base64
from collections.abc import Awaitable
from collections.abc import Callable
import hashlib
import json
import logging
from pathlib import Path
import random
from typing import Any

# Import battle logging
from battle_logging import end_run_logging
from cryptography.fernet import Fernet

from autofighter.effects import create_stat_buff
from autofighter.gacha import GachaManager
from autofighter.mapgen import MapNode
from autofighter.party import Party
from autofighter.passives import PassiveRegistry
from autofighter.rooms import BattleRoom
from autofighter.rooms import _build_foes  # noqa: F401
from autofighter.rooms import _scale_stats  # noqa: F401
from autofighter.rooms import _serialize  # noqa: F401
from autofighter.save_manager import SaveManager
from autofighter.stats import Stats
from plugins import players as player_plugins
from plugins.damage_types import load_damage_type
from plugins.players._base import PlayerBase

log = logging.getLogger(__name__)

SAVE_MANAGER: SaveManager | None = None
FERNET: Fernet | None = None


def get_save_manager() -> SaveManager:
    global SAVE_MANAGER
    global FERNET

    if SAVE_MANAGER is None:
        manager = SaveManager.from_env()
        manager.migrate(Path(__file__).resolve().parent / "migrations")
        with manager.connection() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS damage_types (id TEXT PRIMARY KEY, type TEXT)"
            )
            count = conn.execute("SELECT COUNT(*) FROM owned_players").fetchone()[0]
            if count == 1:
                persona = random.choice(["lady_darkness", "lady_light"])
                conn.execute("INSERT INTO owned_players (id) VALUES (?)", (persona,))

        SAVE_MANAGER = manager

        key = base64.urlsafe_b64encode(
            hashlib.sha256((manager.key or "plaintext").encode()).digest()
        )
        FERNET = Fernet(key)

    return SAVE_MANAGER


def get_fernet() -> Fernet:
    if FERNET is None:
        get_save_manager()
    assert FERNET is not None
    return FERNET

battle_tasks: dict[str, asyncio.Task] = {}
battle_snapshots: dict[str, dict[str, Any]] = {}

def _describe_passives(obj: Stats | list[str]) -> list[dict[str, Any]]:
    registry = PassiveRegistry()
    if isinstance(obj, list):
        temp = Stats()
        temp.passives = obj
        return registry.describe(temp)
    return registry.describe(obj)

def _load_player_customization() -> tuple[str, dict[str, int]]:
    pronouns = ""
    stats: dict[str, int] = {"hp": 0, "attack": 0, "defense": 0, "crit_rate": 0, "crit_damage": 0}
    with get_save_manager().connection() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS options (key TEXT PRIMARY KEY, value TEXT)"
        )
        cur = conn.execute(
            "SELECT value FROM options WHERE key = ?", ("player_pronouns",)
        )
        row = cur.fetchone()
        if row:
            pronouns = row[0]
        cur = conn.execute("SELECT value FROM options WHERE key = ?", ("player_stats",))
        row = cur.fetchone()
        if row:
            try:
                stats.update(json.loads(row[0]))
            except (TypeError, ValueError, json.JSONDecodeError):
                pass
    return pronouns, stats

def _apply_player_customization(player: PlayerBase) -> None:
    """Apply saved customization multipliers to a player."""

    _, loaded = _load_player_customization()
    multipliers = {
        "max_hp_mult": 1 + loaded.get("hp", 0) * 0.01,
        "atk_mult": 1 + loaded.get("attack", 0) * 0.01,
        "defense_mult": 1 + loaded.get("defense", 0) * 0.01,
        "crit_rate_mult": 1 + loaded.get("crit_rate", 0) * 0.01,
        "crit_damage_mult": 1 + loaded.get("crit_damage", 0) * 0.01,
    }

    log.debug(
        "Applying player customization: player_id=%s, multipliers=%s",
        player.id,
        multipliers,
    )

    if all(v == 1 for v in multipliers.values()):
        log.debug("No customizations to apply (all multipliers are 1)")
        return

    # Store original stats for debugging
    orig_stats = (player.max_hp, player.atk, player.defense)

    mod = create_stat_buff(
        player,
        name="customization",
        turns=10**9,
        id="player_custom",
        bypass_diminishing=True,  # Player customization should not be subject to diminishing returns
        **multipliers,
    )
    player.mods.append(mod.id)

    # Log the stat changes for debugging
    log.debug(
        "Player customization applied: stats changed from %s to (%d, %d, %d)",
        orig_stats,
        player.max_hp,
        player.atk,
        player.defense,
    )


def _load_individual_stat_upgrades(pid: str) -> dict[str, float]:
    """Load individual stat upgrades from the new system."""
    with get_save_manager().connection() as conn:
        # Create table if it doesn't exist
        conn.execute("""
            CREATE TABLE IF NOT EXISTS player_stat_upgrades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id TEXT NOT NULL,
                stat_name TEXT NOT NULL,
                upgrade_percent REAL NOT NULL,
                source_star INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Sum up all upgrades per stat
        cur = conn.execute("""
            SELECT stat_name, SUM(upgrade_percent)
            FROM player_stat_upgrades
            WHERE player_id = ?
            GROUP BY stat_name
        """, (pid,))

        return {row[0]: float(row[1]) for row in cur.fetchall()}


def _apply_player_upgrades(player: PlayerBase) -> None:
    """Apply individual stat upgrades as a persistent, non-diminished effect.

    Keeps base stats unchanged so UI can show deltas (e.g., 5% (+2%)).
    """
    stat_upgrades = _load_individual_stat_upgrades(player.id)
    if not stat_upgrades:
        return

    percent_stats = {"crit_rate", "effect_hit_rate", "effect_resistance", "dodge_odds"}
    multiplier_like_stats = {"crit_damage", "mitigation", "vitality"}
    flat_stats = {"max_hp", "atk", "defense", "regain"}

    deltas: dict[str, float] = {}
    mults: dict[str, float] = {}
    for stat_name, upgrade_percent in stat_upgrades.items():
        if stat_name in flat_stats:
            mults[f"{stat_name}_mult"] = 1.0 + float(upgrade_percent)
        elif stat_name in multiplier_like_stats:
            # Treat as absolute additive (e.g., crit_damage +0.20 for +20%)
            deltas[stat_name] = deltas.get(stat_name, 0.0) + float(upgrade_percent)
        elif stat_name in percent_stats:
            deltas[stat_name] = deltas.get(stat_name, 0.0) + float(upgrade_percent)
        else:
            # Default additive
            deltas[stat_name] = deltas.get(stat_name, 0.0) + float(upgrade_percent)

    if deltas or mults:
        mod = create_stat_buff(
            player,
            name="upgrade_individual",
            turns=10**9,
            id="upgrade_bonus_individual",
            bypass_diminishing=True,  # Player upgrades from items should not be subject to diminishing returns
            **{**deltas, **mults},
        )
        player.mods.append(mod.id)

def _assign_damage_type(player: PlayerBase) -> None:
    with get_save_manager().connection() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS damage_types (id TEXT PRIMARY KEY, type TEXT)"
        )
        cur = conn.execute("SELECT type FROM damage_types WHERE id = ?", (player.id,))
        row = cur.fetchone()
        if row:
            player.damage_type = load_damage_type(row[0])
        else:
            conn.execute(
                "INSERT INTO damage_types (id, type) VALUES (?, ?)",
                (player.id, player.element_id),
            )

def load_party(run_id: str) -> Party:
    with get_save_manager().connection() as conn:
        cur = conn.execute("SELECT party FROM runs WHERE id = ?", (run_id,))
        row = cur.fetchone()
    data = json.loads(row[0]) if row else {}
    if isinstance(data, list):
        data = {"members": data, "gold": 0, "relics": [], "cards": []}
    snapshot = data.get("player", {})
    exp_map: dict[str, int] = data.get("exp", {})
    level_map: dict[str, int] = data.get("level", {})
    exp_mult_map: dict[str, float] = data.get("exp_multiplier", {})
    members: list[PlayerBase] = []
    for pid in data.get("members", []):
        for name in player_plugins.__all__:
            cls = getattr(player_plugins, name)
            if cls.id == pid:
                inst = cls()
                if inst.id == "player":
                    with get_save_manager().connection() as conn:
                        row = conn.execute(
                            "SELECT type FROM damage_types WHERE id = ?", ("player",)
                        ).fetchone()
                    if row and row[0]:
                        inst.damage_type = load_damage_type(row[0])
                    else:
                        inst.damage_type = load_damage_type(
                            snapshot.get("damage_type", inst.element_id)
                        )
                    _apply_player_customization(inst)
                    _apply_player_upgrades(inst)
                else:
                    _assign_damage_type(inst)
                    _apply_player_upgrades(inst)
                target_level = int(level_map.get(pid, 1) or 1)
                if target_level > 1:
                    for _ in range(target_level - 1):
                        inst._on_level_up()
                inst.level = target_level
                inst.exp = int(exp_map.get(pid, 0) or 0)
                try:
                    inst.exp_multiplier = float(
                        exp_mult_map.get(pid, inst.exp_multiplier)
                    )
                except Exception:
                    pass
                members.append(inst)
                break
    party = Party(
        members=members,
        gold=data.get("gold", 0),
        relics=data.get("relics", []),
        cards=data.get("cards", []),
        rdr=data.get("rdr", 1.0),
    )
    return party

def load_map(run_id: str) -> tuple[dict, list[MapNode]]:
    with get_save_manager().connection() as conn:
        cur = conn.execute("SELECT map FROM runs WHERE id = ?", (run_id,))
        row = cur.fetchone()
    if row is None:
        return {"rooms": [], "current": 0, "battle": False}, []
    state = json.loads(row[0])
    rooms = [MapNode.from_dict(n) for n in state.get("rooms", [])]
    return state, rooms

def save_map(run_id: str, state: dict) -> None:
    with get_save_manager().connection() as conn:
        conn.execute(
            "UPDATE runs SET map = ? WHERE id = ?",
            (json.dumps(state), run_id),
        )

def save_party(run_id: str, party: Party) -> None:
    with get_save_manager().connection() as conn:
        cur = conn.execute("SELECT party FROM runs WHERE id = ?", (run_id,))
        row = cur.fetchone()
    existing = json.loads(row[0]) if row else {}
    snapshot = existing.get("player", {})
    for member in party.members:
        if member.id == "player":
            # Persist the player's chosen damage type
            snapshot = {**snapshot, "damage_type": member.element_id}
            break
    with get_save_manager().connection() as conn:
        data = {
            "members": [m.id for m in party.members],
            "gold": party.gold,
            "relics": party.relics,
            "cards": party.cards,
            "exp": {m.id: m.exp for m in party.members},
            "level": {m.id: m.level for m in party.members},
            "exp_multiplier": {m.id: m.exp_multiplier for m in party.members},
            "rdr": party.rdr,
            "player": snapshot,
        }
        conn.execute(
            "UPDATE runs SET party = ? WHERE id = ?",
            (json.dumps(data), run_id),
        )

async def _run_battle(
    run_id: str,
    room: BattleRoom,
    foes: Stats | list[Stats],
    party: Party,
    data: dict[str, Any],
    state: dict[str, Any],
    rooms: list[MapNode],
    progress: Callable[[dict[str, Any]], Awaitable[None]],
) -> None:
    try:
        try:
            result = await room.resolve(party, data, progress, foes)
        except Exception as exc:
            state["battle"] = False
            log.exception("Battle resolution failed for %s", run_id)
            battle_snapshots[run_id] = {
                "result": "error",
                "error": str(exc),
                "ended": True,
                "party": [],
                "foes": [],
                "awaiting_next": False,
                "awaiting_card": False,
                "awaiting_relic": False,
                "awaiting_loot": False,
            }
            try:
                await asyncio.to_thread(save_map, run_id, state)
                await asyncio.to_thread(save_party, run_id, party)
            except Exception:
                pass
            return
        state["battle"] = False
        try:
            loot_items = result.get("loot", {}).get("items", [])
            manager = GachaManager(get_save_manager())
            items = manager._get_items()
            for entry in loot_items:
                if entry.get("id") == "ticket":
                    items["ticket"] = items.get("ticket", 0) + 1
                else:
                    key = f"{entry['id']}_{entry['stars']}"
                    items[key] = items.get(key, 0) + 1
            manager._auto_craft(items)
            manager._set_items(items)
            result["items"] = items
            if result.get("result") == "defeat":
                state["awaiting_card"] = False
                state["awaiting_relic"] = False
                state["awaiting_loot"] = False
                state["awaiting_next"] = False
                try:
                    await asyncio.to_thread(save_map, run_id, state)
                    await asyncio.to_thread(save_party, run_id, party)
                    result.update(
                        {
                            "run_id": run_id,
                            "current_room": rooms[state["current"]].room_type,
                            "current_index": state["current"],
                            "awaiting_card": False,
                            "awaiting_relic": False,
                            "awaiting_loot": False,
                            "awaiting_next": False,
                            "next_room": None,
                            "ended": True,
                        }
                    )
                    battle_snapshots[run_id] = result
                finally:
                    try:
                        # End run logging when run is deleted due to defeat
                        end_run_logging()
                        with get_save_manager().connection() as conn:
                            conn.execute("DELETE FROM runs WHERE id = ?", (run_id,))
                    except Exception:
                        pass
                return
            has_card_choices = bool(result.get("card_choices"))
            has_relic_choices = bool(result.get("relic_choices"))
            # Check if there's loot to review (gold or items)
            has_loot = bool(result.get("loot", {}).get("gold", 0) > 0 or
                           len(result.get("loot", {}).get("items", [])) > 0)

            # Set up reward progression sequence for proper UI flow
            if has_card_choices or has_relic_choices or has_loot:
                progression = {
                    "available": [],
                    "completed": [],
                    "current_step": None
                }

                # Build sequence of steps based on what rewards are available
                if has_card_choices:
                    progression["available"].append("card")
                if has_relic_choices:
                    progression["available"].append("relic")
                if has_loot:
                    progression["available"].append("loot")

                # If there are no actual reward choices, allow immediate advancement
                if not (has_card_choices or has_relic_choices or has_loot):
                    # No rewards at all, ready to advance immediately
                    state["awaiting_card"] = False
                    state["awaiting_relic"] = False
                    state["awaiting_loot"] = False
                    state["awaiting_next"] = True
                    next_type = (
                        rooms[state["current"] + 1].room_type
                        if state["current"] + 1 < len(rooms)
                        else None
                    )
                else:
                    # Start with first available step
                    progression["current_step"] = progression["available"][0]

                    state["reward_progression"] = progression
                    state["awaiting_card"] = has_card_choices
                    state["awaiting_relic"] = has_relic_choices
                    state["awaiting_loot"] = has_loot
                    state["awaiting_next"] = False
                    next_type = None
            else:
                # No rewards at all, ready to advance immediately
                state["awaiting_card"] = False
                state["awaiting_relic"] = False
                state["awaiting_loot"] = False
                state["awaiting_next"] = True
                next_type = (
                    rooms[state["current"] + 1].room_type
                    if state["current"] + 1 < len(rooms)
                    else None
                )
            await asyncio.to_thread(save_map, run_id, state)
            await asyncio.to_thread(save_party, run_id, party)
            result.update(
                {
                    "run_id": run_id,
                    "action": data.get("action", ""),
                    "next_room": next_type,
                    "current_room": rooms[state["current"]].room_type,
                    "current_index": state["current"],
                    "awaiting_card": state.get("awaiting_card", False),
                    "awaiting_relic": state.get("awaiting_relic", False),
                    "awaiting_loot": state.get("awaiting_loot", False),
                    "awaiting_next": state.get("awaiting_next", False),
                }
            )
            battle_snapshots[run_id] = result
        except Exception as exc:
            log.exception("Battle processing failed for %s", run_id)
            battle_snapshots[run_id] = {
                "result": "error",
                "loot": result.get("loot"),
                "error": str(exc),
                "ended": True,
                "party": [],
                "foes": [],
                "awaiting_next": False,
                "awaiting_card": False,
                "awaiting_relic": False,
                "awaiting_loot": False,
            }
    finally:
        battle_tasks.pop(run_id, None)
