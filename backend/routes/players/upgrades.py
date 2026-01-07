"""Player upgrade routes for star system and stat upgrades."""

from __future__ import annotations

import asyncio
import logging
import math
from typing import Dict

from quart import jsonify
from quart import request
from runs.encryption import get_save_manager
from runs.party_manager import _assign_damage_type

from autofighter.gacha import GachaManager
from plugins import characters as player_plugins

from . import bp
from .materials import ITEM_UNIT_SCALE
from .materials import MATERIAL_STAR_LEVEL
from .materials import STAR_TO_MATERIALS
from .materials import UPGRADEABLE_STATS
from .materials import InsufficientMaterialsError
from .materials import _canonical_material_breakdown
from .materials import _consume_material_units
from .materials import _get_total_material_units
from .materials import _parse_material_request
from .materials import _resolve_player_element
from .materials import _sanitize_breakdown_map
from .upgrade_utils import _build_player_upgrade_payload
from .upgrade_utils import _ensure_upgrade_tables
from .upgrade_utils import _get_next_cost_for_stat

log = logging.getLogger(__name__)


@bp.get("/players/<pid>/upgrade")
async def get_player_upgrade(pid: str):
    """Get upgrade information for a player.

    Args:
        pid: Player identifier

    Returns:
        JSON with items, stat_upgrades, stat_totals, stat_counts, next_costs, element
    """
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
    """Upgrade a player character using the new individual stat upgrade system.

    Args:
        pid: Player identifier

    Request JSON:
        star_level: Star level of items to consume (1-4)
        item_count: Number of items to use (>= 1)

    Returns:
        JSON with upgrade results or error
    """
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
        unit_scale = ITEM_UNIT_SCALE[star_level]
        required_units = item_count * unit_scale

        def _consume_items(key_list: list[str], tier: int, remaining: int) -> int:
            units_per_item = ITEM_UNIT_SCALE[tier]
            for item_key in key_list:
                available = int(items.get(item_key, 0))
                if available <= 0:
                    continue
                if remaining <= 0:
                    break
                needed_items = min(
                    available,
                    math.ceil(remaining / units_per_item),
                )
                if needed_items <= 0:
                    continue
                items[item_key] = available - needed_items
                consumed_items[item_key] = consumed_items.get(item_key, 0) + needed_items
                remaining -= needed_items * units_per_item
            return remaining

        if pid == "player":
            tiers = range(star_level, 5)
            tier_keys: dict[int, list[str]] = {}
            total_units = 0
            for tier in tiers:
                suffix = f"_{tier}"
                active_key = f"{element}{suffix}"
                keys: list[str] = [active_key, f"generic{suffix}"]
                keys.extend(
                    key
                    for key in sorted(items)
                    if key.endswith(suffix) and key not in keys
                )
                tier_keys[tier] = keys
                units_per_item = ITEM_UNIT_SCALE[tier]
                total_units += sum(int(items.get(key, 0)) for key in keys) * units_per_item

            if total_units < required_units:
                available_equivalent = total_units // unit_scale
                return {
                    "error": (
                        f"insufficient {star_level}★ items (need {item_count}, "
                        f"found {available_equivalent})"
                    )
                }

            remaining_units = required_units
            for tier in tiers:
                remaining_units = _consume_items(tier_keys[tier], tier, remaining_units)
                if remaining_units <= 0:
                    break
            if remaining_units > 0:
                return {"error": "failed to consume required materials"}
            materials_added = item_count * materials_per_item
        else:
            tiers = range(star_level, 5)
            tier_keys: dict[int, list[str]] = {
                tier: [f"{element}_{tier}"] for tier in tiers
            }
            total_units = sum(
                int(items.get(keys[0], 0)) * ITEM_UNIT_SCALE[tier]
                for tier, keys in tier_keys.items()
            )
            if total_units < required_units:
                available_equivalent = total_units // unit_scale
                return {
                    "error": (
                        f"insufficient {element} {star_level}★ items "
                        f"(need {item_count}, found {available_equivalent})"
                    )
                }

            remaining_units = required_units
            for tier in tiers:
                remaining_units = _consume_items(tier_keys[tier], tier, remaining_units)
                if remaining_units <= 0:
                    break
            if remaining_units > 0:
                return {"error": "failed to consume required materials"}
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
    """Spend upgrade points on a specific stat.

    Args:
        pid: Player identifier

    Request JSON:
        stat_name: Stat to upgrade (from UPGRADEABLE_STATS)
        materials/points: Material cost or breakdown
        repeat/repeats: Number of times to repeat upgrade (default: 1, max: 1000)
        total_materials/total_points: Optional budget limit

    Returns:
        JSON with upgrade results or error
    """
    data = await request.get_json(silent=True) or {}
    stat_name = data.get("stat_name")
    requested_materials = data.get("materials")
    if requested_materials is None:
        requested_materials = data.get("points")
    raw_repeat = data.get("repeat", data.get("repeats"))
    raw_total_materials = data.get("total_materials")
    if raw_total_materials is None:
        raw_total_materials = data.get("total_points")

    if stat_name not in UPGRADEABLE_STATS:
        return jsonify({"error": f"invalid stat, must be one of: {UPGRADEABLE_STATS}"}), 400

    if isinstance(requested_materials, str):
        try:
            int(requested_materials.strip())
        except (TypeError, ValueError):
            return jsonify({"error": "materials must be numeric or a breakdown map"}), 400
    elif requested_materials is not None and not isinstance(
        requested_materials, (int, float, dict)
    ):
        return jsonify({"error": "materials must be numeric or a breakdown map"}), 400

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
        remaining_units_total = 0

        with get_save_manager().connection() as conn:
            _ensure_upgrade_tables(conn)
            element = _resolve_player_element(conn, pid)
            material_key = f"{element}_{MATERIAL_STAR_LEVEL}"
            expected_units, requested_breakdown = _parse_material_request(
                element, requested_materials
            )
            if expected_units is not None and expected_units < 1:
                return {
                    "error": "materials must be at least 1",
                }

            while completed < repeat:
                cost_to_spend = _get_next_cost_for_stat(pid, stat_name, conn=conn)
                last_cost = cost_to_spend

                expected_payload_breakdown = _canonical_material_breakdown(
                    element, cost_to_spend
                )
                expected_clean = _sanitize_breakdown_map(expected_payload_breakdown)

                if not validated_cost:
                    if expected_units is not None and expected_units != cost_to_spend:
                        payload = _build_player_upgrade_payload(pid)
                        payload.update(
                            {
                                "error": "invalid material cost",
                                "expected_units": cost_to_spend,
                                "expected_materials": {
                                    "units": cost_to_spend,
                                    "breakdown": expected_payload_breakdown,
                                },
                            }
                        )
                        return payload

                    if requested_breakdown and requested_breakdown != expected_clean:
                        payload = _build_player_upgrade_payload(pid)
                        payload.update(
                            {
                                "error": "invalid material cost",
                                "expected_units": cost_to_spend,
                                "expected_materials": {
                                    "units": cost_to_spend,
                                    "breakdown": expected_payload_breakdown,
                                },
                            }
                        )
                        return payload

                    validated_cost = True

                if budget_remaining is not None and cost_to_spend > budget_remaining:
                    break

                try:
                    _consume_material_units(conn, element, cost_to_spend)
                except InsufficientMaterialsError:
                    payload = _build_player_upgrade_payload(pid)
                    available_units = _get_total_material_units(conn, element)
                    payload.update(
                        {
                            "error": "insufficient materials",
                            "required_units": cost_to_spend,
                            "required_materials": {
                                "units": cost_to_spend,
                                "breakdown": expected_payload_breakdown,
                            },
                            "attempted_upgrades": repeat,
                            "completed_upgrades": completed,
                            "materials_spent": total_spent,
                            "upgrade_percent": total_percent,
                            "materials_available": available_units,
                            "materials_available_units": available_units,
                        }
                    )
                    return payload

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
            remaining_units_total = _get_total_material_units(conn, element)
            conn.commit()

        payload = _build_player_upgrade_payload(pid)
        response = {
            "stat_upgraded": stat_name,
            "materials_spent": total_spent,
            "upgrade_percent": total_percent,
            "completed_upgrades": completed,
            "attempted_upgrades": repeat,
            "materials_remaining": remaining_materials,
            "materials_remaining_units": remaining_units_total,
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
