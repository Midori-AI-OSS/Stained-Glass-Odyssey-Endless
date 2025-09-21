from __future__ import annotations

import asyncio
from dataclasses import fields
import json
import logging
import math
from typing import Dict
from typing import List

from quart import Blueprint
from quart import jsonify
from quart import request
from runs.encryption import get_save_manager
from runs.party_manager import _apply_character_customization
from runs.party_manager import _apply_player_customization
from runs.party_manager import _apply_player_upgrades
from runs.party_manager import _assign_damage_type
from runs.party_manager import _load_character_customization
from runs.party_manager import _load_player_customization
from services.user_level_service import get_user_state

from autofighter.gacha import GachaManager
from autofighter.stats import apply_status_hooks
from plugins import players as player_plugins

bp = Blueprint("players", __name__)
log = logging.getLogger(__name__)


def _get_stat_refresh_rate() -> int:
    def get_rate():
        with get_save_manager().connection() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS options (key TEXT PRIMARY KEY, value TEXT)"
            )
            cur = conn.execute(
                "SELECT value FROM options WHERE key = ?", ("stat_refresh_rate",)
            )
            return cur.fetchone()

    try:
        # This function is called synchronously from sync endpoints for now
        # Could be made async in the future if needed
        row = get_rate()
        rate = int(row[0]) if row else 5
    except (TypeError, ValueError):
        rate = 5
    return max(1, min(rate, 10))


@bp.get("/players")
async def get_players() -> tuple[str, int, dict[str, str]]:
    def _serialize_stats(obj) -> dict:
        data: dict[str, object] = {}
        # Build a dict without triggering dataclasses.asdict deep-copy, which
        # chokes on complex objects (e.g., langchain/pydantic bindings).
        for f in fields(obj):
            name = f.name
            if name == "lrm_memory":
                # Non-serializable, runtime-only memory object
                continue
            value = getattr(obj, name)
            if name == "char_type":
                # Enum-like object; surface the name/string
                try:
                    data[name] = value.name
                except Exception:
                    data[name] = str(value)
                continue
            if name == "damage_type":
                # Surface damage type as element id string
                try:
                    data[name] = obj.element_id
                except Exception:
                    data[name] = str(value)
                continue
            # Keep primitives as-is, shallow-copy containers, stringify others
            if isinstance(value, (int, float, bool, str)) or value is None:
                data[name] = value
            elif isinstance(value, list):
                data[name] = list(value)
            elif isinstance(value, dict):
                data[name] = dict(value)
            else:
                data[name] = str(value)

        # Append in-run (computed) stats so the Party Picker can show live values
        try:
            data["max_hp"] = int(getattr(obj, "max_hp"))
            data["atk"] = int(getattr(obj, "atk"))
            data["defense"] = int(getattr(obj, "defense"))
            data["crit_rate"] = float(getattr(obj, "crit_rate"))
            data["crit_damage"] = float(getattr(obj, "crit_damage"))
            data["effect_hit_rate"] = float(getattr(obj, "effect_hit_rate"))
            data["effect_resistance"] = float(getattr(obj, "effect_resistance"))
            data["mitigation"] = float(getattr(obj, "mitigation"))
            data["vitality"] = float(getattr(obj, "vitality"))
            data["regain"] = int(getattr(obj, "regain"))
            data["dodge_odds"] = float(getattr(obj, "dodge_odds"))
            # Surface active effects (buffs/debuffs), including upgrade modifiers
            try:
                effects = []
                for eff in getattr(obj, "get_active_effects", lambda: [])() or []:
                    # Eff might be a StatEffect or compatible object
                    effects.append({
                        "id": getattr(eff, "name", "effect"),
                        "name": getattr(eff, "name", "effect"),
                        "duration": getattr(eff, "duration", -1),
                        "source": getattr(eff, "source", "unknown"),
                        "modifiers": dict(getattr(eff, "stat_modifiers", {})),
                    })
                data["active_effects"] = effects
            except Exception:
                data["active_effects"] = []
            # Also surface upgrade totals per stat so the UI can present
            # base vs upgraded values without depending on effect scaling.
            try:
                totals: dict[str, float] = {}
                for up in _get_player_stat_upgrades(getattr(obj, 'id', '')):
                    totals[up["stat_name"]] = totals.get(up["stat_name"], 0.0) + float(up["upgrade_percent"])
                data["upgrade_totals"] = totals
            except Exception:
                data["upgrade_totals"] = {}
        except Exception:
            # If any property access fails, leave as-is
            pass

        # Provide base_stats map when available for delta display
        try:
            getb = getattr(obj, "get_base_stat")
            data["base_stats"] = {
                "max_hp": getb("max_hp"),
                "atk": getb("atk"),
                "defense": getb("defense"),
                "crit_rate": getb("crit_rate"),
                "crit_damage": getb("crit_damage"),
                "effect_hit_rate": getb("effect_hit_rate"),
                "effect_resistance": getb("effect_resistance"),
                "mitigation": getb("mitigation"),
                "vitality": getb("vitality"),
                "regain": getb("regain"),
                "dodge_odds": getb("dodge_odds"),
            }
        except Exception:
            pass

        return data

    def get_owned_players():
        with get_save_manager().connection() as conn:
            cur = conn.execute("SELECT id FROM owned_players")
            return {row[0] for row in cur.fetchall()}

    owned = await asyncio.to_thread(get_owned_players)
    roster = []
    for name in player_plugins.__all__:
        cls = getattr(player_plugins, name)
        inst = cls()
        await asyncio.to_thread(_assign_damage_type, inst)
        await asyncio.to_thread(_apply_character_customization, inst, inst.id)
        await asyncio.to_thread(_apply_player_upgrades, inst)
        stats = _serialize_stats(inst)
        # Prefer instance about; if it's the PlayerBase placeholder, fall back to class attribute
        inst_about = getattr(inst, "about", "") or ""
        if inst_about == "Player description placeholder":
            inst_about = getattr(type(inst), "about", inst_about)

        roster.append(
            {
                "id": inst.id,
                "name": inst.name,
                "about": inst_about,
                "owned": inst.id in owned,
                "is_player": inst.id == "player",
                "element": inst.element_id,
                "stats": stats,
            }
        )
    return jsonify({"players": roster, "user": get_user_state()})


@bp.get("/player/stats")
async def player_stats() -> tuple[str, int, dict[str, object]]:
    refresh = _get_stat_refresh_rate()
    player = player_plugins.player.Player()
    await asyncio.to_thread(_assign_damage_type, player)

    # Store original stats before customization
    orig_stats = (player.max_hp, player.atk, player.defense)

    await asyncio.to_thread(_apply_player_customization, player)
    await asyncio.to_thread(_apply_player_upgrades, player)
    apply_status_hooks(player)

    # Log the stat changes for debugging
    log.debug(
        "Player stats endpoint: original=(%d, %d, %d), final=(%d, %d, %d), mods=%s",
        orig_stats[0],
        orig_stats[1],
        orig_stats[2],
        player.max_hp,
        player.atk,
        player.defense,
        player.mods,
    )

    # Get base stats and active effects if available
    base_stats = {}
    active_effects = []
    if hasattr(player, 'get_base_stat'):
        base_stats = {
            "max_hp": player.get_base_stat("max_hp"),
            "atk": player.get_base_stat("atk"),
            "defense": player.get_base_stat("defense"),
            "crit_rate": player.get_base_stat("crit_rate"),
            "crit_damage": player.get_base_stat("crit_damage"),
            "effect_hit_rate": player.get_base_stat("effect_hit_rate"),
            "mitigation": player.get_base_stat("mitigation"),
            "regain": player.get_base_stat("regain"),
            "dodge_odds": player.get_base_stat("dodge_odds"),
            "effect_resistance": player.get_base_stat("effect_resistance"),
            "vitality": player.get_base_stat("vitality"),
        }

    if hasattr(player, 'get_active_effects'):
        for effect in player.get_active_effects():
            # Import effect descriptions
            description = "Unknown effect"
            try:
                if effect.name == "aftertaste":
                    from plugins.effects.aftertaste import Aftertaste
                    description = Aftertaste.get_description()
                elif effect.name == "critical_boost":
                    from plugins.effects.critical_boost import CriticalBoost
                    description = CriticalBoost.get_description()
            except Exception:
                pass

            active_effects.append({
                "name": effect.name,
                "source": effect.source,
                "duration": effect.duration,
                "modifiers": effect.stat_modifiers,
                "description": description
            })

    stats = {
        "core": {
            "hp": player.hp,
            "max_hp": player.max_hp,
            "exp": player.exp,
            "level": player.level,
            "exp_multiplier": player.exp_multiplier,
            "actions_per_turn": player.actions_per_turn,
        },
        "offense": {
            "atk": player.atk,
            "crit_rate": player.crit_rate,
            "crit_damage": player.crit_damage,
            "effect_hit_rate": player.effect_hit_rate,
            "damage_type": player.element_id,
        },
        "defense": {
            "defense": player.defense,
            "mitigation": player.mitigation,
            "regain": player.regain,
            "dodge_odds": player.dodge_odds,
            "effect_resistance": player.effect_resistance,
        },
        "vitality": {"vitality": player.vitality},
        "advanced": {
            "action_points": player.action_points,
            "damage_taken": player.damage_taken,
            "damage_dealt": player.damage_dealt,
            "kills": player.kills,
            "aggro": player.aggro,
        },
        "status": {
            "passives": player.passives,
            "dots": player.dots,
            "hots": player.hots,
        },
        "base_stats": base_stats,
        "active_effects": active_effects,
    }
    return jsonify({"stats": stats, "refresh_rate": refresh, "user": get_user_state()})


@bp.get("/player/editor")
async def get_player_editor() -> tuple[str, int, dict[str, object]]:
    player = player_plugins.player.Player()
    await asyncio.to_thread(_assign_damage_type, player)
    pronouns, stats = await asyncio.to_thread(_load_player_customization)
    log.debug("Loading player editor data: pronouns=%s, stats=%s", pronouns, stats)
    return jsonify(
        {
            "pronouns": pronouns,
            "damage_type": player.element_id,
            "hp": stats.get("hp", 0),
            "attack": stats.get("attack", 0),
            "defense": stats.get("defense", 0),
            "crit_rate": stats.get("crit_rate", 0),
            "crit_damage": stats.get("crit_damage", 0),
        }
    )


@bp.put("/player/editor")
async def update_player_editor() -> tuple[str, int, dict[str, str]]:
    data = await request.get_json(silent=True) or {}
    # Guard: do not allow edits while any run is active
    def _has_active_runs() -> bool:
        with get_save_manager().connection() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, party TEXT, map TEXT)")
            cur = conn.execute("SELECT COUNT(1) FROM runs")
            row = cur.fetchone()
            try:
                return bool(row and int(row[0]) > 0)
            except Exception:
                return False

    has_active = await asyncio.to_thread(_has_active_runs)
    if has_active:
        return jsonify({"error": "run active"}), 409
    pronouns = (data.get("pronouns") or "").strip()
    damage_type = (data.get("damage_type") or "").capitalize()
    try:
        hp = int(data.get("hp", 0))
        attack = int(data.get("attack", 0))
        defense = int(data.get("defense", 0))
        crit_rate = int(data.get("crit_rate", 0))
        crit_damage = int(data.get("crit_damage", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "invalid stats"}), 400
    total = hp + attack + defense + crit_rate + crit_damage
    if len(pronouns) > 15:
        return jsonify({"error": "invalid pronouns"}), 400
    allowed = {"Light", "Dark", "Wind", "Lightning", "Fire", "Ice"}
    if damage_type and damage_type not in allowed:
        return jsonify({"error": "invalid damage type"}), 400

    # Calculate max allowed points. Legacy point-based caps are no longer in
    # effect; upgrades now spend materials directly so the editor always uses
    # the base cap of 100.
    max_allowed = 100

    log.debug(
        "Player editor validation: total=%d, max_allowed=%d",
        total,
        max_allowed,
    )

    if total > max_allowed:
        return jsonify({"error": "over-allocation"}), 400

    log.debug(
        "Updating player editor: pronouns=%s, damage_type=%s, hp=%d, attack=%d, defense=%d, crit_rate=%d, crit_damage=%d",
        pronouns,
        damage_type,
        hp,
        attack,
        defense,
        crit_rate,
        crit_damage,
    )

    def update_player_data():
        with get_save_manager().connection() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS options (key TEXT PRIMARY KEY, value TEXT)"
            )
            conn.execute(
                "INSERT OR REPLACE INTO options (key, value) VALUES (?, ?)",
                ("player_pronouns", pronouns),
            )
            conn.execute(
                "INSERT OR REPLACE INTO options (key, value) VALUES (?, ?)",
                (
                    "player_stats",
                    json.dumps({
                        "hp": hp,
                        "attack": attack,
                        "defense": defense,
                        "crit_rate": crit_rate,
                        "crit_damage": crit_damage,
                    }),
                ),
            )
            if damage_type:
                conn.execute(
                    "INSERT OR REPLACE INTO damage_types (id, type) VALUES (?, ?)",
                    ("player", damage_type),
                )

    await asyncio.to_thread(update_player_data)
    log.debug("Player customization saved successfully")
    return jsonify({"status": "ok"})


@bp.get("/players/<pid>/editor")
async def get_character_editor(pid: str):
    """Fetch saved stat allocations for a specific character."""

    inst = None
    for name in player_plugins.__all__:
        cls = getattr(player_plugins, name)
        if getattr(cls, "id", name) == pid:
            inst = cls()
            break
    if inst is None:
        return jsonify({"error": "unknown player"}), 404

    stats = await asyncio.to_thread(_load_character_customization, pid)
    return jsonify(
        {
            "hp": stats.get("hp", 0),
            "attack": stats.get("attack", 0),
            "defense": stats.get("defense", 0),
            "crit_rate": stats.get("crit_rate", 0),
            "crit_damage": stats.get("crit_damage", 0),
        }
    )


@bp.put("/players/<pid>/editor")
async def update_character_editor(pid: str):
    """Save stat allocations for a specific character."""

    data = await request.get_json(silent=True) or {}
    try:
        hp = int(data.get("hp", 0))
        attack = int(data.get("attack", 0))
        defense = int(data.get("defense", 0))
        crit_rate = int(data.get("crit_rate", 0))
        crit_damage = int(data.get("crit_damage", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "invalid stats"}), 400

    total = hp + attack + defense + crit_rate + crit_damage
    max_allowed = 100
    if total > max_allowed:
        return jsonify({"error": "over-allocation"}), 400

    def update_data():
        payload = {
            "hp": hp,
            "attack": attack,
            "defense": defense,
            "crit_rate": crit_rate,
            "crit_damage": crit_damage,
        }
        with get_save_manager().connection() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS options (key TEXT PRIMARY KEY, value TEXT)"
            )
            conn.execute(
                "INSERT OR REPLACE INTO options (key, value) VALUES (?, ?)",
                (f"player_stats_{pid}", json.dumps(payload)),
            )
            if pid == "player":
                conn.execute(
                    "INSERT OR REPLACE INTO options (key, value) VALUES (?, ?)",
                    ("player_stats", json.dumps(payload)),
                )

    await asyncio.to_thread(update_data)
    return jsonify({"status": "ok"})


# Constants for new upgrade system
UPGRADEABLE_STATS = [
    "max_hp",
    "atk",
    "defense",
    "crit_rate",
    "crit_damage",
    "vitality",
    "mitigation",
]
STAR_TO_MATERIALS = {1: 1, 2: 150, 3: 22500, 4: 3375000}
MATERIAL_STAR_LEVEL = 1


def _resolve_player_element(conn, player_id: str) -> str:
    """Resolve the active element for a player identifier."""

    element = None
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS damage_types (id TEXT PRIMARY KEY, type TEXT)"
        )
        row = conn.execute(
            "SELECT type FROM damage_types WHERE id = ?",
            (player_id,),
        ).fetchone()
        if row and row[0]:
            element = str(row[0])
    except Exception:
        element = None

    if element:
        return element.lower()

    for name in player_plugins.__all__:
        cls = getattr(player_plugins, name)
        if getattr(cls, "id", name) != player_id:
            continue
        inst = cls()
        try:
            return inst.element_id.lower()
        except Exception:
            return str(getattr(inst, "damage_type", "generic")).lower()

    return "generic"


def _estimate_cost_from_upgrade_percent(upgrade_percent: object) -> int | None:
    """Translate a stored percent boost back into spent upgrade points."""

    try:
        percent = float(upgrade_percent)
    except (TypeError, ValueError):
        return None

    if percent <= 0:
        return None

    points = int(round(percent * 1000))
    return points if points > 0 else None


def _backfill_upgrade_costs(conn) -> None:
    """Populate missing ``cost_spent`` values for legacy upgrade rows."""

    cur = conn.execute(
        """
        SELECT id, player_id, stat_name, upgrade_percent, cost_spent, source_star
        FROM player_stat_upgrades
        ORDER BY player_id ASC, stat_name ASC, created_at ASC, id ASC
        """
    )

    updates: list[tuple[int, int]] = []
    stat_counts: dict[tuple[str, str], int] = {}

    for row in cur.fetchall():
        upgrade_id, player_id, stat_name, upgrade_percent, cost_spent, source_star = row

        if not player_id or not stat_name:
            continue

        key = (str(player_id), str(stat_name))
        upgrade_count = stat_counts.get(key, 0)

        try:
            source_value = int(source_star)
        except (TypeError, ValueError):
            source_value = 1

        if source_value <= 0:
            stat_counts[key] = upgrade_count + 1
            continue

        if cost_spent and cost_spent > 0:
            stat_counts[key] = upgrade_count + 1
            continue

        estimated_points = _estimate_cost_from_upgrade_percent(upgrade_percent)
        if estimated_points is None:
            estimated_points = upgrade_count + 1

        stat_counts[key] = upgrade_count + 1
        updates.append((int(estimated_points), upgrade_id))

    if updates:
        conn.executemany(
            "UPDATE player_stat_upgrades SET cost_spent = ? WHERE id = ?",
            updates,
        )


def _migrate_legacy_points(conn) -> None:
    """Convert legacy upgrade points into 1★ materials."""

    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'player_upgrade_points'"
    )
    if cur.fetchone() is None:
        return

    rows = conn.execute(
        "SELECT player_id, points FROM player_upgrade_points"
    ).fetchall()
    for player_id, points in rows:
        try:
            material_count = int(points)
        except (TypeError, ValueError):
            material_count = 0
        if material_count <= 0:
            continue
        element = _resolve_player_element(conn, str(player_id))
        item_key = f"{element}_{MATERIAL_STAR_LEVEL}"
        current = conn.execute(
            "SELECT count FROM upgrade_items WHERE id = ?",
            (item_key,),
        ).fetchone()
        existing = int(current[0]) if current else 0
        conn.execute(
            "INSERT OR REPLACE INTO upgrade_items (id, count) VALUES (?, ?)",
            (item_key, existing + material_count),
        )

    conn.execute("DROP TABLE IF EXISTS player_upgrade_points")


def _ensure_upgrade_tables(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS player_stat_upgrades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT NOT NULL,
            stat_name TEXT NOT NULL,
            upgrade_percent REAL NOT NULL,
            source_star INTEGER NOT NULL,
            cost_spent INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS upgrade_items (id TEXT PRIMARY KEY, count INTEGER NOT NULL)"
    )

    cur = conn.execute("PRAGMA table_info(player_stat_upgrades)")
    columns = {row[1] for row in cur.fetchall()}
    has_source_star = "source_star" in columns
    if not has_source_star:
        conn.execute(
            "ALTER TABLE player_stat_upgrades ADD COLUMN source_star INTEGER NOT NULL DEFAULT 0"
        )
        has_source_star = True
    needs_backfill = False
    if "cost_spent" not in columns:
        conn.execute(
            "ALTER TABLE player_stat_upgrades ADD COLUMN cost_spent INTEGER NOT NULL DEFAULT 0"
        )
        needs_backfill = True

    if not needs_backfill:
        if has_source_star:
            cur = conn.execute(
                """
                SELECT 1
                FROM player_stat_upgrades
                WHERE (cost_spent IS NULL OR cost_spent <= 0) AND source_star > 0
                LIMIT 1
                """
            )
        else:
            cur = conn.execute(
                "SELECT 1 FROM player_stat_upgrades WHERE cost_spent <= 0 LIMIT 1"
            )
        needs_backfill = cur.fetchone() is not None

    if needs_backfill:
        _backfill_upgrade_costs(conn)

    _migrate_legacy_points(conn)


def _create_upgrade_tables():
    with get_save_manager().connection() as conn:
        _ensure_upgrade_tables(conn)
        conn.commit()


def _get_player_stat_upgrades(player_id: str) -> List[Dict]:
    """Get all stat upgrades for a player."""
    with get_save_manager().connection() as conn:
        _ensure_upgrade_tables(conn)
        cur = conn.execute("""
            SELECT id, stat_name, upgrade_percent, source_star, cost_spent, created_at
            FROM player_stat_upgrades
            WHERE player_id = ?
            ORDER BY created_at DESC, id DESC
        """, (player_id,))
        return [
            {
                "id": row[0],
                "stat_name": row[1],
                "upgrade_percent": row[2],
                "source_star": row[3],
                "cost_spent": row[4],
                "created_at": row[5]
            }
            for row in cur.fetchall()
        ]


def _count_completed_upgrades(stat_upgrades: List[Dict]) -> Dict[str, int]:
    counts: Dict[str, int] = {stat: 0 for stat in UPGRADEABLE_STATS}
    for upgrade in stat_upgrades:
        stat_name = upgrade.get("stat_name")
        if stat_name is None:
            continue
        counts[stat_name] = counts.get(stat_name, 0) + 1
    return counts


def _calculate_next_cost(last_cost: int | None) -> int:
    if not last_cost or last_cost < 1:
        return 1
    return max(1, math.ceil(last_cost * 1.05))


def _determine_next_costs(stat_upgrades: List[Dict], element_key: str) -> Dict[str, dict[str, int | str]]:
    last_costs: Dict[str, int] = {}
    for upgrade in stat_upgrades:
        stat_name = upgrade.get("stat_name")
        if stat_name is None or stat_name in last_costs:
            continue
        try:
            raw_cost = upgrade.get("cost_spent")
            if raw_cost in (None, 0):
                raw_cost = upgrade.get("materials_spent")
            if raw_cost in (None, 0):
                percent_value = float(upgrade.get("upgrade_percent") or 0.0)
                raw_cost = int(round(percent_value * 1000))
            last_costs[stat_name] = int(raw_cost or 0)
        except (TypeError, ValueError):
            last_costs[stat_name] = 0

    next_costs: Dict[str, dict[str, int | str]] = {}
    seen_stats = set(UPGRADEABLE_STATS)
    item_key = f"{element_key}_{MATERIAL_STAR_LEVEL}"
    for stat in UPGRADEABLE_STATS:
        next_costs[stat] = {
            "item": item_key,
            "count": _calculate_next_cost(last_costs.get(stat)),
        }
    for stat, last_cost in last_costs.items():
        if stat in seen_stats:
            continue
        next_costs[stat] = {
            "item": item_key,
            "count": _calculate_next_cost(last_cost),
        }
    return next_costs


def _get_next_cost_for_stat(player_id: str, stat_name: str, *, conn=None) -> int:
    def _resolve_last_cost(row) -> int:
        if not row:
            return 0
        cost_spent, upgrade_percent = row
        try:
            if cost_spent and int(cost_spent) > 0:
                return int(cost_spent)
        except (TypeError, ValueError):
            pass
        try:
            percent_value = float(upgrade_percent or 0.0)
        except (TypeError, ValueError):
            percent_value = 0.0
        estimated = int(round(percent_value * 1000))
        return max(0, estimated)

    if conn is None:
        with get_save_manager().connection() as local_conn:
            _ensure_upgrade_tables(local_conn)
            cur = local_conn.execute(
                """
                SELECT cost_spent, upgrade_percent
                FROM player_stat_upgrades
                WHERE player_id = ? AND stat_name = ?
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                (player_id, stat_name),
            )
            last_cost = _resolve_last_cost(cur.fetchone())
            return _calculate_next_cost(last_cost)

    cur = conn.execute(
        """
        SELECT cost_spent, upgrade_percent
        FROM player_stat_upgrades
        WHERE player_id = ? AND stat_name = ?
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """,
        (player_id, stat_name),
    )
    last_cost = _resolve_last_cost(cur.fetchone())
    return _calculate_next_cost(last_cost)


def _build_player_upgrade_payload(player_id: str) -> Dict:
    stat_upgrades_raw = _get_player_stat_upgrades(player_id)
    stat_upgrades: List[Dict] = []
    for upgrade in stat_upgrades_raw:
        converted = dict(upgrade)
        converted["materials_spent"] = converted.pop("cost_spent", 0)
        stat_upgrades.append(converted)

    stat_totals: Dict[str, float] = {stat: 0.0 for stat in UPGRADEABLE_STATS}
    for upgrade in stat_upgrades:
        stat_name = upgrade.get("stat_name")
        if stat_name is None:
            continue
        stat_totals[stat_name] = stat_totals.get(stat_name, 0.0) + float(
            upgrade.get("upgrade_percent") or 0.0
        )

    stat_counts = _count_completed_upgrades(stat_upgrades)

    with get_save_manager().connection() as conn:
        _ensure_upgrade_tables(conn)
        element = _resolve_player_element(conn, player_id)

    next_costs = _determine_next_costs(stat_upgrades, element)

    for stat in UPGRADEABLE_STATS:
        stat_totals.setdefault(stat, 0.0)
        next_costs.setdefault(
            stat,
            {
                "item": f"{element}_{MATERIAL_STAR_LEVEL}",
                "count": _calculate_next_cost(None),
            },
        )

    return {
        "stat_upgrades": stat_upgrades,
        "stat_totals": stat_totals,
        "stat_counts": stat_counts,
        "next_costs": next_costs,
        "element": element,
    }
@bp.get("/players/<pid>/upgrade")
async def get_player_upgrade(pid: str):
    manager = GachaManager(get_save_manager())
    items = await asyncio.to_thread(manager._get_items)

    def fetch_new_upgrade_data() -> Dict:
        return _build_player_upgrade_payload(pid)

    new_data = await asyncio.to_thread(fetch_new_upgrade_data)

    return jsonify({
        "items": items,
        **new_data
    })


@bp.post("/players/<pid>/upgrade")
async def upgrade_player(pid: str):
    """Upgrade a player character using the new individual stat upgrade system."""
    data = await request.get_json(silent=True) or {}

    manager = GachaManager(get_save_manager())

    # Find the player instance
    inst = None
    for name in player_plugins.__all__:
        cls = getattr(player_plugins, name)
        if getattr(cls, "id", name) == pid:
            inst = cls()
            break
    if inst is None:
        return jsonify({"error": "unknown player"}), 404

    await asyncio.to_thread(_assign_damage_type, inst)
    items = await asyncio.to_thread(manager._get_items)

    # Get the item to use (star level and count) - JSON data is required
    if not data:
        return jsonify({"error": "JSON data required with star_level and item_count"}), 400

    star_level = data.get("star_level")
    item_count = data.get("item_count", 1)

    if star_level not in [1, 2, 3, 4]:
        return jsonify({"error": "invalid star_level, must be 1-4"}), 400

    if item_count < 1:
        return jsonify({"error": "item_count must be at least 1"}), 400

    element = inst.element_id.lower()
    target_material_key = f"{element}_{MATERIAL_STAR_LEVEL}"

    def perform_upgrade():
        materials_added = 0
        consumed_items: dict[str, int] = {}
        materials_per_item = STAR_TO_MATERIALS[star_level]

        if pid == "player":
            items_needed = item_count
            preferred_keys: list[str] = []
            active_key = f"{element}_{star_level}"
            preferred_keys.append(active_key)
            preferred_keys.append(f"generic_{star_level}")
            for item_key in sorted(items):
                if not item_key.endswith(f"_{star_level}"):
                    continue
                if item_key in preferred_keys:
                    continue
                preferred_keys.append(item_key)

            for item_key in preferred_keys:
                available = items.get(item_key, 0)
                if available <= 0:
                    continue
                consume = min(available, items_needed)
                items[item_key] -= consume
                consumed_items[item_key] = consume
                materials_added += consume * materials_per_item
                items_needed -= consume
                if items_needed <= 0:
                    break
            if items_needed > 0:
                return {
                    "error": (
                        f"insufficient {star_level}★ items (need {item_count}, "
                        f"found {item_count - items_needed})"
                    )
                }
        else:
            source_key = f"{element}_{star_level}"
            available = int(items.get(source_key, 0))
            if available < item_count:
                return {"error": f"insufficient {element} {star_level}★ items"}
            items[source_key] = available - item_count
            consumed_items[source_key] = item_count
            materials_added = item_count * materials_per_item

        if materials_added <= 0:
            return {"error": "no materials gained"}

        items[target_material_key] = items.get(target_material_key, 0) + materials_added

        return {
            "materials_gained": materials_added,
            "items_consumed": consumed_items,
            "materials_balance": items.get(target_material_key, 0),
            "material_key": target_material_key,
        }

    result = await asyncio.to_thread(perform_upgrade)

    if "error" in result:
        return jsonify(result), 400

    # Update items in database
    await asyncio.to_thread(manager._set_items, items)

    # Get updated information
    new_data = await asyncio.to_thread(lambda: _build_player_upgrade_payload(pid))

    return jsonify({
        **result,
        "items": items,
        **new_data
    })


@bp.post("/players/<pid>/upgrade-stat")
async def upgrade_player_stat(pid: str):
    """Spend upgrade points on a specific stat."""

    data = await request.get_json(silent=True) or {}
    stat_name = data.get("stat_name")
    requested_materials = data.get("materials")
    if requested_materials is None:
        requested_materials = data.get("points")
    if requested_materials is not None:
        try:
            requested_materials = int(requested_materials)
        except (TypeError, ValueError):
            return jsonify({"error": "materials must be an integer >= 1"}), 400
        if requested_materials < 1:
            return jsonify({"error": "materials must be at least 1"}), 400
    raw_repeat = data.get("repeat", data.get("repeats"))
    raw_total_materials = data.get("total_materials")
    if raw_total_materials is None:
        raw_total_materials = data.get("total_points")

    if stat_name not in UPGRADEABLE_STATS:
        return jsonify({"error": f"invalid stat, must be one of: {UPGRADEABLE_STATS}"}), 400

    try:
        repeat = int(raw_repeat) if raw_repeat is not None else 1
    except (TypeError, ValueError):
        repeat = 1
    if repeat < 1:
        repeat = 1
    repeat = min(repeat, 1000)

    if raw_total_materials is not None:
        try:
            material_budget = int(raw_total_materials)
        except (TypeError, ValueError):
            return jsonify({"error": "total_materials must be an integer >= 1"}), 400
        if material_budget < 1:
            return jsonify({"error": "total_materials must be at least 1"}), 400
    else:
        material_budget = None

    def apply_material_upgrades():
        validated_cost = False
        completed = 0
        total_spent = 0
        total_percent = 0.0
        budget_remaining = material_budget
        last_cost = None

        with get_save_manager().connection() as conn:
            _ensure_upgrade_tables(conn)
            element = _resolve_player_element(conn, pid)
            material_key = f"{element}_{MATERIAL_STAR_LEVEL}"

            while completed < repeat:
                cost_to_spend = _get_next_cost_for_stat(pid, stat_name, conn=conn)
                last_cost = cost_to_spend

                if (
                    not validated_cost
                    and requested_materials is not None
                    and int(requested_materials) != cost_to_spend
                ):
                    payload = _build_player_upgrade_payload(pid)
                    payload.update({
                        "error": "invalid material cost",
                        "expected_materials": cost_to_spend,
                    })
                    return payload

                validated_cost = True

                if budget_remaining is not None and cost_to_spend > budget_remaining:
                    break

                row = conn.execute(
                    "SELECT count FROM upgrade_items WHERE id = ?",
                    (material_key,),
                ).fetchone()
                available = int(row[0]) if row else 0
                if available < cost_to_spend:
                    payload = _build_player_upgrade_payload(pid)
                    payload.update({
                        "error": "insufficient materials",
                        "required_materials": cost_to_spend,
                        "attempted_upgrades": repeat,
                        "completed_upgrades": completed,
                        "materials_spent": total_spent,
                        "upgrade_percent": total_percent,
                        "materials_available": available,
                    })
                    return payload

                conn.execute(
                    "UPDATE upgrade_items SET count = count - ? WHERE id = ?",
                    (cost_to_spend, material_key),
                )

                upgrade_percent = cost_to_spend * 0.001
                conn.execute(
                    """
                    INSERT INTO player_stat_upgrades (player_id, stat_name, upgrade_percent, source_star, cost_spent)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (pid, stat_name, upgrade_percent, MATERIAL_STAR_LEVEL, cost_to_spend),
                )

                completed += 1
                total_spent += cost_to_spend
                total_percent += upgrade_percent
                if budget_remaining is not None:
                    budget_remaining = max(0, budget_remaining - cost_to_spend)

            remaining_row = conn.execute(
                "SELECT count FROM upgrade_items WHERE id = ?",
                (material_key,),
            ).fetchone()
            remaining_materials = int(remaining_row[0]) if remaining_row else 0
            conn.commit()

        payload = _build_player_upgrade_payload(pid)
        response = {
            "stat_upgraded": stat_name,
            "materials_spent": total_spent,
            "upgrade_percent": total_percent,
            "completed_upgrades": completed,
            "attempted_upgrades": repeat,
            "materials_remaining": remaining_materials,
        }
        response.update(payload)

        if completed == 0:
            response.update({
                "error": "insufficient materials",
                "required_materials": last_cost,
            })
            if budget_remaining is not None and last_cost is not None and budget_remaining < last_cost:
                response["error"] = "insufficient material budget"
            return response

        if budget_remaining is not None:
            response["budget_remaining"] = budget_remaining
            if completed < repeat:
                response["partial"] = True

        return response

    result = await asyncio.to_thread(apply_material_upgrades)

    if "error" in result:
        return jsonify(result), 400

    return jsonify(result)
