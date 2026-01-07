"""Player catalog and listing endpoints."""

from __future__ import annotations

import asyncio
from dataclasses import fields
import logging

from async_db_utils import async_query
from quart import jsonify
from runs.encryption import get_save_manager
from runs.party_manager import _apply_character_customization
from runs.party_manager import _apply_player_upgrades
from runs.party_manager import _assign_damage_type
from services.user_level_service import get_user_state
from tracking import log_menu_action
from tracking import log_overlay_action

from plugins import characters as player_plugins

from . import bp
from .upgrade_utils import _get_player_stat_upgrades

log = logging.getLogger(__name__)


def _serialize_stats(obj) -> dict:
    """Serialize player stats object for JSON response.

    Args:
        obj: Player stats object to serialize

    Returns:
        Dictionary representation of player stats
    """
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

    try:
        raw_cap = getattr(obj, "ultimate_charge_max")
    except Exception:
        raw_cap = None
    if raw_cap is None:
        try:
            raw_cap = getattr(obj, "ultimate_charge_capacity")
        except Exception:
            raw_cap = None
    try:
        data["ultimate_max"] = max(1, int(raw_cap))
    except Exception:
        data["ultimate_max"] = 15

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


async def _get_owned_players():
    """Fetch set of owned player IDs (async-safe).

    Returns:
        Set of owned player IDs
    """
    rows = await async_query(
        get_save_manager(),
        "SELECT id FROM owned_players"
    )
    return {row[0] for row in rows}


@bp.get("/players")
async def get_players() -> tuple[str, int, dict[str, str]]:
    """List all available players with ownership status and stats.

    Returns:
        JSON response with player roster and user state
    """
    owned = await _get_owned_players()
    roster: dict[str, dict[str, object]] = {}
    export_names = getattr(
        player_plugins, "_PLAYABLE_EXPORTS", tuple(player_plugins.__all__)
    )

    for name in export_names:
        cls = getattr(player_plugins, name, None)
        if cls is None:
            continue
        if getattr(cls, "plugin_type", "player") != "player":
            continue
        inst = cls()
        await asyncio.to_thread(_assign_damage_type, inst)
        await asyncio.to_thread(_apply_character_customization, inst, inst.id)
        await asyncio.to_thread(_apply_player_upgrades, inst)
        stats = _serialize_stats(inst)

        # Send both description fields to frontend for client-side switching
        full_about_text = getattr(inst, "full_about", "")
        summarized_about_text = getattr(inst, "summarized_about", "")

        if inst.id in roster:
            continue

        roster[inst.id] = {
            "id": inst.id,
            "name": inst.name,
            "full_about": full_about_text,
            "summarized_about": summarized_about_text,
            "owned": inst.id in owned,
            "is_player": inst.id == "player",
            "element": inst.element_id,
            "stats": stats,
            "ui": cls.get_ui_metadata() or {},
            "music": cls.get_music_metadata(),
        }
    players = list(roster.values())
    payload = {"players": players, "user": get_user_state()}
    try:
        await log_menu_action("Party", "view", {"count": len(players)})
        await log_overlay_action("party", {"count": len(players)})
    except Exception:
        pass
    return jsonify(payload)
