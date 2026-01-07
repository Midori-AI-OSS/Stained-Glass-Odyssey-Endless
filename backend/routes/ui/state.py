"""UI state endpoint."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from quart import jsonify
from runs.encryption import get_save_manager
from runs.lifecycle import battle_snapshots
from runs.lifecycle import battle_tasks
from runs.lifecycle import load_map
from runs.party_manager import load_party
from services.asset_service import get_asset_manifest
from services.room_service import BATTLE_ROOM_TYPES
from services.run_configuration import METADATA_VERSION
from services.run_configuration import RunModifierContext

from autofighter.rooms.shop import serialize_shop_payload

from . import bp
from .utils import determine_ui_mode
from .utils import get_available_actions
from .utils import get_default_active_run


@bp.get("/ui")
async def get_ui_state() -> tuple[str, int, dict[str, Any]]:
    """Get complete UI state for the active run.

    Returns:
        JSON with mode, active_run, game_state, available_actions, asset_manifest
    """
    run_id = get_default_active_run()
    asset_manifest = get_asset_manifest()
    metadata_hash = METADATA_VERSION

    if not run_id:
        return jsonify({
            "mode": "menu",
            "active_run": None,
            "game_state": None,
            "available_actions": ["start_run"],
            "asset_manifest": asset_manifest,
            "run_config_metadata_hash": metadata_hash,
        })

    try:
        # Load map and party data directly (simpler than reusing get_map)
        state, rooms = await asyncio.to_thread(load_map, run_id)
        if not state:
            return jsonify({
                "mode": "menu",
                "active_run": None,
                "game_state": None,
                "available_actions": ["start_run"],
                "asset_manifest": asset_manifest,
            })

        def get_party_data():
            with get_save_manager().connection() as conn:
                cur = conn.execute("SELECT party FROM runs WHERE id = ?", (run_id,))
                row = cur.fetchone()
                return json.loads(row[0]) if row and row[0] else {}

        party_state = await asyncio.to_thread(get_party_data)
        run_configuration_snapshot = (
            party_state.get("config")
            if isinstance(party_state, dict)
            else None
        )
        if isinstance(run_configuration_snapshot, dict):
            hash_candidate = run_configuration_snapshot.get("version")
            if isinstance(hash_candidate, str) and hash_candidate.strip():
                metadata_hash = hash_candidate.strip()

        # Determine current room state and what the frontend should display
        current_index = int(state.get("current", 0))
        current_room_data = None
        current_room_type = None
        next_room_type = None
        all_battle_types = set(BATTLE_ROOM_TYPES) | {"battle-boss-floor"}

        if rooms and 0 <= current_index < len(rooms):
            current_node = rooms[current_index]
            current_room_type = current_node.room_type

            # Get next room type if available
            if current_index + 1 < len(rooms):
                next_room_type = rooms[current_index + 1].room_type

            # Check if there's an active battle snapshot
            snap = battle_snapshots.get(run_id)
            is_battle_room = current_room_type in all_battle_types
            awaiting_flags = (
                state.get("awaiting_next")
                or state.get("awaiting_card")
                or state.get("awaiting_relic")
                or state.get("awaiting_loot")
            )
            progression = state.get("reward_progression")
            awaiting_progression = awaiting_flags or (
                isinstance(progression, dict) and progression.get("current_step")
            )

            has_active_battle_task = (
                run_id in battle_tasks and not battle_tasks[run_id].done()
            )
            state_reports_battle = bool(state.get("battle"))

            if snap is not None and is_battle_room:
                snap.setdefault("tags", list(getattr(current_node, "tags", ()) or []))
                current_room_data = snap
            elif (
                is_battle_room
                and not awaiting_progression
                and (has_active_battle_task or state_reports_battle)
            ):
                # Battle is active but no snapshot is available yet.
                current_room_data = {
                    "result": "battle",
                    "snapshot_missing": True,
                    "current_index": current_index,
                    "current_room": current_room_type,
                    "next_room": next_room_type,
                }
                current_room_data["tags"] = list(getattr(current_node, "tags", ()) or [])
            elif current_room_type == "shop" and not state.get("awaiting_next"):
                stock_state = state.get("shop_stock", {})
                stored_stock: list[dict[str, Any]] = []
                if isinstance(stock_state, dict):
                    stored_stock = stock_state.get(str(current_node.room_id), []) or []

                try:
                    items_bought = int(state.get("shop_items_bought", 0) or 0)
                except (TypeError, ValueError):
                    items_bought = 0

                party_snapshot = await asyncio.to_thread(load_party, run_id)
                context = getattr(current_node, "run_modifier_context", None)
                if isinstance(context, dict):
                    try:
                        context = RunModifierContext.from_dict(context)
                        setattr(current_node, "run_modifier_context", context)
                    except Exception:
                        context = None
                if context is None:
                    snapshot_context = getattr(party_snapshot, "run_modifier_context", None)
                    if isinstance(snapshot_context, dict):
                        try:
                            snapshot_context = RunModifierContext.from_dict(snapshot_context)
                        except Exception:
                            snapshot_context = None
                    context = snapshot_context
                    if context is not None:
                        setattr(current_node, "run_modifier_context", context)
                if context is None:
                    stored_context = state.get("modifier_context")
                    if isinstance(stored_context, dict):
                        try:
                            context = RunModifierContext.from_dict(stored_context)
                        except Exception:
                            context = None

                shop_view = serialize_shop_payload(
                    party_snapshot,
                    stored_stock,
                    getattr(current_node, "pressure", 0),
                    items_bought,
                    context=context,
                )
                shop_view.update(
                    {
                        "current_index": current_index,
                        "current_room": current_room_type,
                        "next_room": next_room_type,
                    }
                )
                current_room_data = shop_view
            elif state.get("awaiting_next"):
                # Provide basic state when awaiting next room
                current_room_data = {
                    "result": current_room_type.replace('-', '_') if current_room_type else "unknown",
                    "awaiting_next": True,
                    "current_index": current_index,
                    "current_room": current_room_type,
                    "next_room": next_room_type
                }

        game_state = {
            "map": state,
            "party": party_state.get("members", []),
            "current_state": {
                "current_index": current_index,
                "current_room_type": current_room_type,
                "next_room_type": next_room_type,
                "awaiting_next": state.get("awaiting_next", False),
                "awaiting_card": state.get("awaiting_card", False),
                "awaiting_relic": state.get("awaiting_relic", False),
                "awaiting_loot": state.get("awaiting_loot", False),
                "reward_progression": state.get("reward_progression"),
                "room_data": current_room_data
            }
        }

        if isinstance(run_configuration_snapshot, dict):
            game_state["run_configuration"] = run_configuration_snapshot
            game_state["run_configuration_metadata_hash"] = metadata_hash

        # Determine UI mode based on game state
        mode = determine_ui_mode(game_state)

        return jsonify({
            "mode": mode,
            "active_run": run_id,
            "game_state": game_state,
            "available_actions": get_available_actions(mode, game_state),
            "asset_manifest": asset_manifest,
            "run_config_metadata_hash": metadata_hash,
        })

    except Exception as e:
        # If there's an error, fall back to menu mode
        return jsonify({
            "mode": "menu",
            "active_run": None,
            "game_state": None,
            "available_actions": ["start_run"],
            "error": str(e),
            "asset_manifest": asset_manifest,
        })
