"""Player statistics endpoints."""

from __future__ import annotations

import asyncio
import logging

from async_db_utils import async_query
from quart import jsonify
from runs.encryption import get_save_manager
from runs.party_manager import _apply_player_customization
from runs.party_manager import _apply_player_upgrades
from runs.party_manager import _assign_damage_type
from services.user_level_service import get_user_state

from autofighter.stats import apply_status_hooks
from plugins import characters as player_plugins

from . import bp

log = logging.getLogger(__name__)


async def _get_stat_refresh_rate() -> int:
    """Get stat refresh rate from options (async-safe).

    Returns:
        Refresh rate integer between 1 and 10 (default: 5)
    """
    try:
        rows = await async_query(
            get_save_manager(),
            "SELECT value FROM options WHERE key = ?",
            ("stat_refresh_rate",)
        )
        rate = int(rows[0][0]) if rows else 5
    except (TypeError, ValueError, IndexError):
        rate = 5
    return max(1, min(rate, 10))


@bp.get("/player/stats")
async def player_stats() -> tuple[str, int, dict[str, object]]:
    """Get current player statistics with base stats and active effects.

    Returns:
        JSON response with categorized stats, refresh rate, and user state
    """
    refresh = await _get_stat_refresh_rate()
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
