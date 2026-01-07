"""Player customization and editor endpoints."""

from __future__ import annotations

import asyncio
import json
import logging

from async_db_utils import async_execute
from async_db_utils import async_query
from quart import jsonify
from quart import request
from runs.encryption import get_save_manager
from runs.party_manager import _assign_damage_type
from runs.party_manager import _load_character_customization
from runs.party_manager import _load_player_customization

from plugins import characters as player_plugins

from . import bp

log = logging.getLogger(__name__)


async def _has_active_runs() -> bool:
    """Check if there are active game runs (async-safe).

    Returns:
        True if active runs exist
    """
    await async_execute(
        get_save_manager(),
        "CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, party TEXT, map TEXT)"
    )
    rows = await async_query(
        get_save_manager(),
        "SELECT COUNT(1) FROM runs"
    )
    try:
        return bool(rows and int(rows[0][0]) > 0)
    except Exception:
        return False


@bp.get("/player/editor")
async def get_player_editor() -> tuple[str, int, dict[str, object]]:
    """Get player editor customization settings.

    Returns:
        JSON with pronouns, damage type, and stat allocations
    """
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
    """Update player editor customization settings.

    Request JSON:
        pronouns: Player pronouns (max 15 chars)
        damage_type: Element type (Light/Dark/Wind/Lightning/Fire/Ice)
        hp, attack, defense, crit_rate, crit_damage: Stat allocations (total <= 100)

    Returns:
        JSON with status or error
    """
    data = await request.get_json(silent=True) or {}
    # Guard: do not allow edits while any run is active
    has_active = await _has_active_runs()
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

    async def update_player_data():
        """Update player data in database (async-safe)."""
        await async_execute(
            get_save_manager(),
            "CREATE TABLE IF NOT EXISTS options (key TEXT PRIMARY KEY, value TEXT)"
        )
        await async_execute(
            get_save_manager(),
            "INSERT OR REPLACE INTO options (key, value) VALUES (?, ?)",
            ("player_pronouns", pronouns),
        )
        await async_execute(
            get_save_manager(),
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
            await async_execute(
                get_save_manager(),
                "INSERT OR REPLACE INTO damage_types (id, type) VALUES (?, ?)",
                ("player", damage_type),
            )

    await update_player_data()
    log.debug("Player customization saved successfully")
    return jsonify({"status": "ok"})


@bp.get("/players/<pid>/editor")
async def get_character_editor(pid: str):
    """Fetch saved stat allocations for a specific character.

    Args:
        pid: Player/character ID

    Returns:
        JSON with stat allocations or 404 if player not found
    """
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
    """Save stat allocations for a specific character.

    Args:
        pid: Player/character ID

    Request JSON:
        hp, attack, defense, crit_rate, crit_damage: Stat allocations (total <= 100)

    Returns:
        JSON with status or error
    """
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

    async def update_data():
        """Update player stats in database (async-safe)."""
        payload = {
            "hp": hp,
            "attack": attack,
            "defense": defense,
            "crit_rate": crit_rate,
            "crit_damage": crit_damage,
        }
        await async_execute(
            get_save_manager(),
            "CREATE TABLE IF NOT EXISTS options (key TEXT PRIMARY KEY, value TEXT)"
        )
        await async_execute(
            get_save_manager(),
            "INSERT OR REPLACE INTO options (key, value) VALUES (?, ?)",
            (f"player_stats_{pid}", json.dumps(payload)),
        )
        if pid == "player":
            await async_execute(
                get_save_manager(),
                "INSERT OR REPLACE INTO options (key, value) VALUES (?, ?)",
                ("player_stats", json.dumps(payload)),
            )

    await update_data()
    return jsonify({"status": "ok"})
