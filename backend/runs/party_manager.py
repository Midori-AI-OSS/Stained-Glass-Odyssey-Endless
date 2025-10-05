"""Party and player management utilities."""

from __future__ import annotations

import json
import logging
import math
from typing import Any

from autofighter.effects import create_stat_buff
from autofighter.party import Party
from autofighter.passives import PassiveRegistry
from autofighter.stats import Stats
from autofighter.stats import apply_status_hooks
from plugins import characters as player_plugins
from plugins.characters._base import PlayerBase
from plugins.damage_types import load_damage_type

from .encryption import get_save_manager

log = logging.getLogger(__name__)


def _describe_passives(obj: Stats | list[str]) -> list[dict[str, Any]]:
    registry = PassiveRegistry()
    if isinstance(obj, list):
        temp = Stats()
        temp.passives = obj
        return registry.describe(temp)
    return registry.describe(obj)


def _extract_base_rdr(party: Party) -> float:
    try:
        current_rdr = float(getattr(party, "rdr", 1.0))
    except (TypeError, ValueError):
        current_rdr = 1.0

    try:
        bonus_value = float(getattr(party, "login_rdr_bonus", 0.0))
    except (TypeError, ValueError):
        bonus_value = 0.0

    base_rdr = current_rdr - bonus_value
    if not math.isfinite(base_rdr):
        base_rdr = 1.0
    base_rdr = max(base_rdr, 0.0)
    setattr(party, "base_rdr", base_rdr)
    return base_rdr

def _load_character_customization(pid: str) -> dict[str, int]:
    """Load saved stat allocations for a character."""

    stats: dict[str, int] = {
        "hp": 0,
        "attack": 0,
        "defense": 0,
        "crit_rate": 0,
        "crit_damage": 0,
    }

    key = f"player_stats_{pid}" if pid != "player" else "player_stats"
    with get_save_manager().connection() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS options (key TEXT PRIMARY KEY, value TEXT)"
        )
        cur = conn.execute("SELECT value FROM options WHERE key = ?", (key,))
        row = cur.fetchone()
        if row:
            try:
                stats.update(json.loads(row[0]))
            except (TypeError, ValueError, json.JSONDecodeError):
                pass
    return stats


def _load_player_customization() -> tuple[str, dict[str, int]]:
    pronouns = ""
    stats = _load_character_customization("player")
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
    return pronouns, stats


def _apply_character_customization(player: PlayerBase, pid: str) -> None:
    """Apply saved customization multipliers to any character."""

    loaded = _load_character_customization(pid)
    multipliers = {
        "max_hp_mult": 1 + loaded.get("hp", 0) * 0.01,
        "atk_mult": 1 + loaded.get("attack", 0) * 0.01,
        "defense_mult": 1 + loaded.get("defense", 0) * 0.01,
        "crit_rate_mult": 1 + loaded.get("crit_rate", 0) * 0.01,
        "crit_damage_mult": 1 + loaded.get("crit_damage", 0) * 0.01,
    }

    log.debug(
        "Applying customization: player_id=%s, multipliers=%s",
        pid,
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


def _apply_player_customization(player: PlayerBase) -> None:
    """Apply saved customization for the main player character."""

    _apply_character_customization(player, "player")


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
    # Freeze-in user level captured at run start (default 1 for legacy runs)
    try:
        run_user_level = int(data.get("user_level", 1) or 1)
    except Exception:
        run_user_level = 1
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
                else:
                    _assign_damage_type(inst)
                _apply_character_customization(inst, inst.id)
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
                # Apply the run-frozen user level buff to base stats exactly once per load
                try:
                    mult = 1.0 + float(run_user_level) * 0.01
                    inst._base_max_hp = int(inst._base_max_hp * mult)
                    inst._base_atk = int(inst._base_atk * mult)
                    inst._base_defense = int(inst._base_defense * mult)
                    inst._base_crit_rate *= mult
                    inst._base_crit_damage *= mult
                    inst._base_effect_hit_rate *= mult
                    inst._base_mitigation *= mult
                    inst._base_regain = int(inst._base_regain * mult)
                    inst._base_dodge_odds *= mult
                    inst._base_effect_resistance *= mult
                    inst._base_vitality *= mult
                except Exception:
                    pass
                apply_status_hooks(inst)
                members.append(inst)
                break
    stored_rdr_raw = data.get("rdr", 1.0)
    try:
        stored_rdr = float(stored_rdr_raw)
    except (TypeError, ValueError):
        stored_rdr = 1.0

    try:
        from services.login_reward_service import (
            get_daily_rdr_bonus_sync,  # local import to avoid circular dependency
        )

        daily_bonus = float(get_daily_rdr_bonus_sync())
    except Exception:
        log.exception("Failed to resolve daily RDR bonus; falling back to base value")
        daily_bonus = 0.0

    party = Party(
        members=members,
        gold=data.get("gold", 0),
        relics=data.get("relics", []),
        cards=data.get("cards", []),
        rdr=stored_rdr + daily_bonus,
        no_shops=bool(data.get("no_shops", False)),
        no_rests=bool(data.get("no_rests", False)),
    )
    setattr(party, "login_rdr_bonus", daily_bonus)
    setattr(party, "base_rdr", stored_rdr)
    if "config" in data:
        setattr(party, "run_config", data.get("config"))
    try:
        cleared = int(data.get("null_lantern_cleared", 0) or 0)
    except Exception:
        cleared = 0
    if cleared:
        setattr(party, "_null_lantern_cleared", cleared)
    try:
        tokens = int(data.get("pull_tokens", 0) or 0)
    except Exception:
        tokens = 0
    setattr(party, "pull_tokens", tokens)
    return party

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
        base: dict[str, Any]
        if isinstance(existing, dict):
            base = dict(existing)
        else:
            base = {}
        base.update(
            {
                "members": [m.id for m in party.members],
                "gold": party.gold,
                "relics": party.relics,
                "cards": party.cards,
                "exp": {m.id: m.exp for m in party.members},
                "level": {m.id: m.level for m in party.members},
                "exp_multiplier": {m.id: m.exp_multiplier for m in party.members},
                "rdr": _extract_base_rdr(party),
                "no_shops": bool(getattr(party, "no_shops", False)),
                "no_rests": bool(getattr(party, "no_rests", False)),
                "null_lantern_cleared": int(getattr(party, "_null_lantern_cleared", 0) or 0),
                "pull_tokens": int(getattr(party, "pull_tokens", 0) or 0),
                "player": snapshot,
            }
        )
        conn.execute(
            "UPDATE runs SET party = ? WHERE id = ?",
            (json.dumps(base), run_id),
        )
__all__ = [
    "_describe_passives",
    "_load_character_customization",
    "_load_player_customization",
    "_apply_character_customization",
    "_apply_player_customization",
    "_load_individual_stat_upgrades",
    "_apply_player_upgrades",
    "_assign_damage_type",
    "load_party",
    "save_party",
]

