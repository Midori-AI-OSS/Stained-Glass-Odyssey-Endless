from __future__ import annotations

import asyncio
import json
import traceback
from typing import Any

from battle_logging.writers import end_run_logging
from quart import Blueprint
from quart import jsonify
from quart import request
from runs.encryption import get_save_manager
from runs.lifecycle import battle_locks
from runs.lifecycle import battle_snapshots
from runs.lifecycle import battle_tasks
from runs.lifecycle import emit_battle_end_for_runs
from runs.lifecycle import load_map
from runs.lifecycle import purge_all_run_state
from runs.lifecycle import purge_run_state
from runs.lifecycle import save_map
from runs.party_manager import load_party
from services.asset_service import get_asset_manifest
from services.reward_service import select_card
from services.reward_service import select_relic
from services.room_service import room_action
from services.run_service import advance_room
from services.run_service import backup_save
from services.run_service import get_battle_events
from services.run_service import get_battle_summary
from services.run_service import restore_save
from services.run_service import shutdown_run
from services.run_service import start_run
from services.run_service import update_party
from services.run_service import wipe_save
from tracking import log_game_action
from tracking import log_menu_action
from tracking import log_play_session_end
from tracking import log_run_end

from autofighter.rooms.shop import serialize_shop_payload

bp = Blueprint("ui", __name__)


def create_error_response(message: str, status_code: int = 400, include_traceback: bool = False) -> tuple[str, int, dict[str, Any]]:
    """Create a consistent error response format."""
    error_data = {
        "error": message,
        "status": "error"
    }

    if include_traceback:
        error_data["traceback"] = traceback.format_exc()

    return jsonify(error_data), status_code


def validate_action_params(action: str, params: dict, required_fields: list[str]) -> str | None:
    """Validate that required parameters are present for an action.

    Returns None if validation passes, or error message if validation fails.
    """
    missing_fields = [field for field in required_fields if not params.get(field)]
    if missing_fields:
        return f"Action '{action}' missing required parameters: {', '.join(missing_fields)}"
    return None


def get_default_active_run() -> str | None:
    """Get the most recent active run, or None if no runs exist."""
    try:
        with get_save_manager().connection() as conn:
            # Get the first run (most recently created)
            cur = conn.execute("SELECT id FROM runs LIMIT 1")
            row = cur.fetchone()
            return row[0] if row else None
    except Exception:
        return None


def determine_ui_mode(game_state: dict[str, Any]) -> str:
    """Determine the current UI mode based on game state."""
    if not game_state:
        return "menu"

    current_state = game_state.get("current_state", {})
    room_data = current_state.get("room_data")

    # Check for reward progression sequence first
    progression = current_state.get("reward_progression")
    if progression and progression.get("current_step"):
        step = progression["current_step"]
        if step == "card":
            return "card_selection"
        elif step == "relic":
            return "relic_selection"
        elif step == "loot":
            return "loot"
        elif step == "battle_review":
            return "battle_review"

    # Check for legacy awaiting states (for backward compatibility)
    if current_state.get("awaiting_card"):
        return "card_selection"
    elif current_state.get("awaiting_relic"):
        return "relic_selection"
    elif current_state.get("awaiting_loot"):
        return "loot"
    elif current_state.get("awaiting_next"):
        return "playing"

    # Check for battle state
    if room_data and room_data.get("result") == "battle":
        # If battle has ended, check for reward states
        if room_data.get("ended"):
            if room_data.get("card_choices"):
                return "card_selection"
            elif room_data.get("relic_choices"):
                return "relic_selection"
            elif room_data.get("loot"):
                return "loot"
            else:
                return "playing"
        else:
            return "battle"

    return "playing"


def get_available_actions(mode: str, game_state: dict[str, Any]) -> list[str]:
    """Get list of available actions for the current UI mode."""
    if mode == "menu":
        return ["start_run", "load_run"]
    elif mode == "playing":
        return ["room_action", "advance_room", "end_run"]
    elif mode == "battle":
        return ["battle_snapshot", "pause_combat", "resume_combat"]
    elif mode == "card_selection":
        return ["choose_card"]
    elif mode == "relic_selection":
        return ["choose_relic"]
    elif mode == "loot":
        return ["advance_room"]
    elif mode == "battle_review":
        return ["advance_room"]
    else:
        return []


@bp.get("/ui")
async def get_ui_state() -> tuple[str, int, dict[str, Any]]:
    """Get complete UI state for the active run."""
    run_id = get_default_active_run()
    asset_manifest = get_asset_manifest()

    if not run_id:
        return jsonify({
            "mode": "menu",
            "active_run": None,
            "game_state": None,
            "available_actions": ["start_run"],
            "asset_manifest": asset_manifest,
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

        # Determine current room state and what the frontend should display
        current_index = int(state.get("current", 0))
        current_room_data = None
        current_room_type = None
        next_room_type = None

        if rooms and 0 <= current_index < len(rooms):
            current_node = rooms[current_index]
            current_room_type = current_node.room_type

            # Get next room type if available
            if current_index + 1 < len(rooms):
                next_room_type = rooms[current_index + 1].room_type

            # Check if there's an active battle snapshot
            snap = battle_snapshots.get(run_id)
            is_battle_room = current_room_type in {"battle-weak", "battle-normal", "battle-boss-floor"}
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

            if snap is not None and is_battle_room:
                current_room_data = snap
            elif is_battle_room and not awaiting_progression:
                # Battle is active but no snapshot is available yet.
                current_room_data = {
                    "result": "battle",
                    "snapshot_missing": True,
                    "current_index": current_index,
                    "current_room": current_room_type,
                    "next_room": next_room_type,
                }
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
                shop_view = serialize_shop_payload(
                    party_snapshot,
                    stored_stock,
                    getattr(current_node, "pressure", 0),
                    items_bought,
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

        # Determine UI mode based on game state
        mode = determine_ui_mode(game_state)

        return jsonify({
            "mode": mode,
            "active_run": run_id,
            "game_state": game_state,
            "available_actions": get_available_actions(mode, game_state),
            "asset_manifest": asset_manifest,
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


@bp.post("/ui/action")
async def handle_ui_action() -> tuple[str, int, dict[str, Any]]:
    """Handle UI actions and dispatch to appropriate backend functions."""
    try:
        data = await request.get_json()
        if not data:
            return create_error_response("Request body must be valid JSON", 400)

        action = data.get("action")
        if not action:
            return create_error_response("Missing 'action' field in request", 400)

        params = data.get("params", {})

        run_id = get_default_active_run()

        if action == "start_run":
            # Validate start_run parameters
            members = params.get("party", ["player"])
            damage_type = params.get("damage_type", "")
            pressure = params.get("pressure", 0)

            if not isinstance(members, list):
                return create_error_response("Party must be a list of member IDs", 400)

            try:
                result = await start_run(members, damage_type, pressure)
                return jsonify(result)
            except ValueError as exc:
                await log_menu_action(
                    "Run",
                    "error",
                    {"members": members, "damage_type": damage_type, "pressure": pressure, "error": str(exc)},
                )
                return create_error_response(str(exc), 400)

        elif action == "update_party":
            target_run_id = params.get("run_id") or run_id
            if not target_run_id:
                return create_error_response("No active run", 400)

            members = params.get("party") or params.get("members")
            if not isinstance(members, list):
                return create_error_response("Party must be a list of member IDs", 400)

            try:
                updated = await update_party(target_run_id, members)
                return jsonify({"party": updated})
            except LookupError:
                return create_error_response("Run not found", 404)
            except ValueError as exc:
                return create_error_response(str(exc), 400)

        elif action == "room_action":
            if not run_id:
                return create_error_response("No active run", 400)

            room_id = params.get("room_id", "0")
            try:
                result = await room_action(run_id, room_id, params)
                await log_game_action(
                    "room_action",
                    run_id=run_id,
                    room_id=room_id,
                    details={"params": params},
                )
                return jsonify(result)
            except LookupError as exc:
                await log_game_action(
                    "room_action_error",
                    run_id=run_id,
                    room_id=room_id,
                    details={"params": params, "error": str(exc)},
                )
                return create_error_response(str(exc), 404)
            except ValueError as exc:
                await log_game_action(
                    "room_action_error",
                    run_id=run_id,
                    room_id=room_id,
                    details={"params": params, "error": str(exc)},
                )
                return create_error_response(str(exc), 400)

        elif action == "advance_room":
            if not run_id:
                return create_error_response("No active run", 400)

            # Load current map state to ensure rewards are resolved
            state, rooms = await asyncio.to_thread(load_map, run_id)
            if (
                state.get("awaiting_card")
                or state.get("awaiting_relic")
                or state.get("awaiting_loot")
            ):
                return create_error_response("Cannot advance room while rewards are pending", 400)

            progression = state.get("reward_progression")

            if progression and progression.get("current_step"):
                current_step = progression["current_step"]

                # Special handling for battle_review step - it's informational only
                if current_step == "battle_review":
                    # Complete battle_review and any remaining steps automatically
                    state["awaiting_next"] = True
                    state["awaiting_card"] = False
                    state["awaiting_relic"] = False
                    state["awaiting_loot"] = False
                    del state["reward_progression"]
                else:
                    # Complete the current step and advance progression
                    progression["completed"].append(current_step)

                    # Find next step in progression
                    available = progression.get("available", [])
                    completed = progression.get("completed", [])
                    next_steps = [step for step in available if step not in completed]

                    if next_steps:
                        # Move to next step in progression
                        progression["current_step"] = next_steps[0]
                        state["reward_progression"] = progression
                    else:
                        # All progression steps completed, ready to advance room
                        state["awaiting_next"] = True
                        state["awaiting_card"] = False
                        state["awaiting_relic"] = False
                        state["awaiting_loot"] = False
                        del state["reward_progression"]

                await asyncio.to_thread(save_map, run_id, state)

                # If we still have progression steps, return the updated state
                if current_step != "battle_review" and progression and progression.get("current_step"):
                    return jsonify({
                        "progression_advanced": True,
                        "current_step": progression["current_step"]
                    })

            try:
                result = await advance_room(run_id)
                return jsonify(result)
            except ValueError as exc:
                await log_game_action(
                    "advance_room_error",
                    run_id=run_id,
                    details={"error": str(exc)},
                )
                return create_error_response(str(exc), 400)

        elif action == "choose_card":
            if not run_id:
                return create_error_response("No active run", 400)

            card_id = params.get("card_id") or params.get("card")
            if not card_id:
                return create_error_response("Missing required parameter: card_id", 400)

            try:
                result = await select_card(run_id, card_id)
                return jsonify(result)
            except ValueError as exc:
                return create_error_response(str(exc), 400)

        elif action == "choose_relic":
            if not run_id:
                return create_error_response("No active run", 400)

            relic_id = params.get("relic_id") or params.get("relic")
            if not relic_id:
                return create_error_response("Missing required parameter: relic_id", 400)

            try:
                result = await select_relic(run_id, relic_id)
                return jsonify(result)
            except ValueError as exc:
                return create_error_response(str(exc), 400)

        elif action == "end_run":
            target_run_id = params.get("run_id") or run_id
            if not target_run_id:
                return create_error_response("No active run", 400)

            run_ended = await shutdown_run(target_run_id)
            if not run_ended:
                return jsonify({"error": "Run not found"}), 404

            return jsonify({"message": "Run ended successfully"})

        else:
            return create_error_response(f"Unknown action: {action}", 400)

    except Exception as e:
        return create_error_response(f"Action failed: {str(e)}", 500, include_traceback=True)


@bp.get("/battles/<int:index>/summary")
async def battle_summary(index: int):
    run_id = get_default_active_run()
    if not run_id:
        return create_error_response("No active run", 404)

    data = await get_battle_summary(run_id, index)
    if data is None:
        return create_error_response("Battle summary not found", 404)

    return jsonify(data)


@bp.get("/battles/<int:index>/events")
async def battle_events(index: int):
    run_id = get_default_active_run()
    if not run_id:
        return create_error_response("No active run", 404)

    data = await get_battle_events(run_id, index)
    if data is None:
        return create_error_response("Battle events not found", 404)

    return jsonify(data)


@bp.post("/run/start")
async def start_run_endpoint() -> tuple[str, int, dict[str, Any]]:
    """Start a new run. Alternative endpoint that matches test expectations."""
    try:
        data = await request.get_json()
        members = data.get("party", ["player"])
        damage_type = data.get("damage_type", "")
        pressure = data.get("pressure", 0)

        try:
            result = await start_run(members, damage_type, pressure)
            return jsonify(result), 200
        except ValueError as exc:
            await log_menu_action(
                "Run",
                "error",
                {"members": members, "damage_type": damage_type, "pressure": pressure, "error": str(exc)},
            )
            return jsonify({"error": str(exc)}), 400

    except Exception as e:
        return jsonify({"error": f"Failed to start run: {str(e)}"}), 500


@bp.delete("/run/<run_id>")
async def end_run(run_id: str) -> tuple[str, int, dict[str, Any]]:
    """End a specific run by deleting it from the database."""

    try:
        run_ended = await shutdown_run(run_id)
        if not run_ended:
            return jsonify({"error": "Run not found"}), 404

        return jsonify({"message": "Run ended successfully"}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to end run: {str(e)}"}), 500


@bp.delete("/runs")
async def end_all_runs() -> tuple[str, int, dict[str, Any]]:
    """End all runs by deleting them from the database."""
    def delete_all_runs():
        with get_save_manager().connection() as conn:
            # Get count of runs before deletion
            cur = conn.execute("SELECT id FROM runs")
            rows = cur.fetchall()
            count = len(rows)

            # Delete all runs
            conn.execute("DELETE FROM runs")
            return count, [row[0] for row in rows]

    try:
        # End run logging
        end_run_logging()

        await emit_battle_end_for_runs()

        # Cancel all active battle tasks and clear per-run state
        purge_all_run_state()

        # Delete from database
        deleted_count, run_ids = await asyncio.to_thread(delete_all_runs)

        for run_id in run_ids:
            purge_run_state(run_id, cancel_task=False)

        # Ensure no lingering state after bulk deletion
        battle_snapshots.clear()
        battle_locks.clear()
        battle_tasks.clear()

        for run_id in run_ids:
            await log_run_end(run_id, "aborted")
            await log_play_session_end(run_id)
        await log_menu_action("Run", "ended_all", {"deleted_count": deleted_count})

        return jsonify({
            "message": f"Ended {deleted_count} run(s) successfully",
            "deleted_count": deleted_count
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to end runs: {str(e)}"}), 500


@bp.get("/save/backup")
async def backup_save_endpoint() -> tuple[str, int, dict[str, Any]]:
    """Export save data as an encrypted backup."""
    try:
        backup_data = await backup_save()
        return backup_data, 200, {"Content-Type": "application/octet-stream"}
    except Exception as e:
        return jsonify({"error": f"Failed to backup save: {str(e)}"}), 500


@bp.post("/save/restore")
async def restore_save_endpoint() -> tuple[str, int, dict[str, Any]]:
    """Restore save data from an encrypted backup."""
    try:
        blob = await request.get_data()
        await restore_save(blob)
        return jsonify({"message": "Save restored successfully"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to restore save: {str(e)}"}), 500


@bp.post("/save/wipe")
async def wipe_save_endpoint() -> tuple[str, int, dict[str, Any]]:
    """Wipe all save data and recreate the database."""
    try:
        await wipe_save()
        return jsonify({"message": "Save wiped successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to wipe save: {str(e)}"}), 500
