"""UI action handling endpoint."""

from __future__ import annotations

import asyncio
from typing import Any

from quart import jsonify
from quart import request
from runs.lifecycle import REWARD_STEP_BATTLE_REVIEW
from runs.lifecycle import REWARD_STEP_CARDS
from runs.lifecycle import REWARD_STEP_DROPS
from runs.lifecycle import REWARD_STEP_RELICS
from runs.lifecycle import ensure_reward_progression
from runs.lifecycle import load_map
from runs.lifecycle import save_map
from services.reward_service import cancel_reward
from services.reward_service import confirm_reward
from services.reward_service import select_card
from services.reward_service import select_relic
from services.room_service import room_action
from services.run_service import advance_room
from services.run_service import shutdown_run
from services.run_service import start_run
from services.run_service import update_party
from tracking import log_game_action
from tracking import log_menu_action

from . import bp
from .utils import create_error_response
from .utils import get_default_active_run


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
            pressure = params.get("pressure")
            run_type = params.get("run_type")
            modifiers = params.get("modifiers")
            metadata_version = params.get("metadata_version")

            if not isinstance(members, list):
                return create_error_response("Party must be a list of member IDs", 400)

            if modifiers is not None and not isinstance(modifiers, dict):
                return create_error_response("Modifiers must be an object keyed by modifier id", 400)

            try:
                result = await start_run(
                    members,
                    damage_type,
                    pressure,
                    run_type=run_type,
                    modifiers=modifiers,
                    metadata_version=metadata_version,
                )
                return jsonify(result)
            except ValueError as exc:
                await log_menu_action(
                    "Run",
                    "error",
                    {
                        "members": members,
                        "damage_type": damage_type,
                        "pressure": pressure,
                        "run_type": run_type,
                        "modifiers": modifiers,
                        "metadata_version": metadata_version,
                        "error": str(exc),
                    },
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

        elif action == "log_menu_action":
            menu = params.get("menu") or params.get("category") or "Run"
            event_name = params.get("event") or params.get("name")
            details = params.get("details") or params.get("data") or {}
            if not event_name:
                return jsonify({"status": "ignored"}), 200

            payload = details if isinstance(details, Mapping) else {"details": details}
            try:
                await log_menu_action(str(menu), str(event_name), payload)
            except Exception:
                pass
            return jsonify({"ok": True}), 200

        elif action == "advance_room":
            if not run_id:
                return create_error_response("No active run", 400)

            # Load current map state to ensure rewards are resolved
            state, rooms = await asyncio.to_thread(load_map, run_id)
            staging_raw = state.get("reward_staging")
            staging = staging_raw if isinstance(staging_raw, Mapping) else None
            staged_cards = []
            pending_response: dict[str, Any] | None = None
            pending_card_choices: list[dict[str, Any]] = []
            pending_relic_choices: list[dict[str, Any]] = []
            if isinstance(staging, Mapping):
                bucket = staging.get("cards")
                if isinstance(bucket, list):
                    staged_cards = bucket
            if state.get("awaiting_card"):
                if not staged_cards:
                    # Check if card selection is still pending (user hasn't chosen yet)
                    # vs already handled (staged card was confirmed by another process)
                    card_choice_options = state.get("card_choice_options")
                    has_card_choices = isinstance(card_choice_options, list) and bool(card_choice_options)
                    if has_card_choices:
                        pending_card_choices = list(card_choice_options)
                    progression = state.get("reward_progression")
                    current_step = None
                    if isinstance(progression, Mapping):
                        current_step = normalise_reward_step(progression.get("current_step"))

                    # If we're in the cards phase and awaiting, user must select
                    if current_step == REWARD_STEP_CARDS and has_card_choices:
                        pending_response = {
                            "progression_advanced": False,
                            "pending_rewards": True,
                            "pending_type": "card",
                            "message": "pending rewards must be collected before advancing",
                            "reward_progression": progression,
                            "awaiting_card": True,
                            "awaiting_relic": bool(state.get("awaiting_relic")),
                            "awaiting_loot": bool(state.get("awaiting_loot")),
                            "awaiting_next": bool(state.get("awaiting_next")),
                            "card_choice_options": pending_card_choices,
                        }
                    elif not has_card_choices:
                        # No staged card and no choices means reward was already handled
                        # Clear the flag and continue
                        state["awaiting_card"] = False
                        await asyncio.to_thread(save_map, run_id, state)
                else:
                    try:
                        await confirm_reward(run_id, "card")
                    except ValueError as exc:
                        return create_error_response(str(exc), 400)
                    state, rooms = await asyncio.to_thread(load_map, run_id)
                    staging_raw = state.get("reward_staging")
                    staging = staging_raw if isinstance(staging_raw, Mapping) else None

            if pending_response:
                return jsonify(pending_response)

            staged_relics = []
            staged_items = []
            if isinstance(staging, Mapping):
                relic_bucket = staging.get("relics")
                if isinstance(relic_bucket, list):
                    staged_relics = relic_bucket
                item_bucket = staging.get("items")
                if isinstance(item_bucket, list):
                    staged_items = item_bucket

            if state.get("awaiting_relic"):
                if not staged_relics:
                    # Check if relic selection is still pending (user hasn't chosen yet)
                    # vs already handled (staged relic was confirmed by another process)
                    snap = battle_snapshots.get(run_id)
                    has_relic_choices = False
                    if isinstance(snap, dict):
                        relic_bucket = snap.get("relic_choices")
                        if isinstance(relic_bucket, list) and relic_bucket:
                            has_relic_choices = True
                            pending_relic_choices = list(relic_bucket)

                    progression = state.get("reward_progression")
                    current_step = None
                    if isinstance(progression, Mapping):
                        current_step = normalise_reward_step(progression.get("current_step"))

                    # If we're in the relics phase and awaiting, user must select
                    if current_step == REWARD_STEP_RELICS and has_relic_choices:
                        pending_response = {
                            "progression_advanced": False,
                            "pending_rewards": True,
                            "pending_type": "relic",
                            "message": "pending rewards must be collected before advancing",
                            "reward_progression": progression,
                            "awaiting_card": bool(state.get("awaiting_card")),
                            "awaiting_relic": True,
                            "awaiting_loot": bool(state.get("awaiting_loot")),
                            "awaiting_next": bool(state.get("awaiting_next")),
                            "relic_choice_options": pending_relic_choices,
                        }
                    elif not has_relic_choices:
                        # No staged relic and no choices means reward was already handled
                        # Clear the flag and continue
                        state["awaiting_relic"] = False
                        await asyncio.to_thread(save_map, run_id, state)
                else:
                    try:
                        await confirm_reward(run_id, "relic")
                    except ValueError as exc:
                        return create_error_response(str(exc), 400)

                    state, rooms = await asyncio.to_thread(load_map, run_id)
                    staging_raw = state.get("reward_staging")
                    staging = staging_raw if isinstance(staging_raw, Mapping) else None

                    staged_relics = []
                    staged_items = []
                    if isinstance(staging, Mapping):
                        relic_bucket = staging.get("relics")
                        if isinstance(relic_bucket, list):
                            staged_relics = relic_bucket
                        item_bucket = staging.get("items")
                        if isinstance(item_bucket, list):
                            staged_items = item_bucket

            if pending_response:
                return jsonify(pending_response)

            # Handle awaiting_loot and staged items
            # Loot items are informational only and cleared when acknowledged
            # Auto-acknowledge when advancing through phases
            if state.get("awaiting_loot") or staged_items:
                print(f"DEBUG: Before loot auto-ack: awaiting_card={state.get('awaiting_card')}, awaiting_relic={state.get('awaiting_relic')}")
                state["awaiting_loot"] = False
                if isinstance(staging, dict):
                    staging["items"] = []
                await asyncio.to_thread(save_map, run_id, state)
                print(f"DEBUG: After loot auto-ack: awaiting_card={state.get('awaiting_card')}, awaiting_relic={state.get('awaiting_relic')}")

            refreshed_progression = None
            progression, _ = ensure_reward_progression(state)

            if progression and progression.get("current_step"):
                current_step = normalise_reward_step(progression.get("current_step"))

                # Special handling for battle_review step - it's informational only
                if current_step == REWARD_STEP_BATTLE_REVIEW:
                    # Complete battle_review and any remaining steps automatically
                    state["awaiting_next"] = True
                    state["awaiting_card"] = False
                    state["awaiting_relic"] = False
                    state["awaiting_loot"] = False
                    del state["reward_progression"]
                else:
                    # Complete the current step and advance progression
                    completed_steps = progression.setdefault("completed", [])
                    if current_step and current_step not in completed_steps:
                        completed_steps.append(current_step)
                        # Clear awaiting flags for the completed step
                        if current_step == REWARD_STEP_DROPS:
                            state["awaiting_loot"] = False
                            if isinstance(staging, dict):
                                staging["items"] = []
                        elif current_step == REWARD_STEP_CARDS:
                            state["awaiting_card"] = False
                        elif current_step == REWARD_STEP_RELICS:
                            state["awaiting_relic"] = False

                        # Manually advance to next uncompleted step
                        available_steps = progression.get("available", [])
                        next_step = None
                        for step in available_steps:
                            if step not in completed_steps:
                                next_step = step
                                break
                        if next_step:
                            progression["current_step"] = next_step

                    # Update progression to advance to next step
                    state["reward_progression"] = progression

                    refreshed_progression, _ = ensure_reward_progression(state)

                    if refreshed_progression:
                        state["awaiting_next"] = False
                    else:
                        # All progression steps completed, ready to advance room
                        state["awaiting_next"] = True
                        state["awaiting_card"] = False
                        state["awaiting_relic"] = False
                        state["awaiting_loot"] = False

                await asyncio.to_thread(save_map, run_id, state)

                # If we still have progression steps, return the updated state
                if (
                    current_step != REWARD_STEP_BATTLE_REVIEW
                    and refreshed_progression
                    and refreshed_progression.get("current_step")
                ):
                    return jsonify({
                        "progression_advanced": True,
                        "current_step": refreshed_progression["current_step"],
                        "reward_progression": refreshed_progression,
                        "awaiting_card": bool(state.get("awaiting_card")),
                        "awaiting_relic": bool(state.get("awaiting_relic")),
                        "awaiting_loot": bool(state.get("awaiting_loot")),
                        "awaiting_next": bool(state.get("awaiting_next")),
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

        elif action == "confirm_card":
            if not run_id:
                return create_error_response("No active run", 400)

            try:
                result = await confirm_reward(run_id, "card")
                return jsonify(result)
            except ValueError as exc:
                return create_error_response(str(exc), 400)

        elif action == "confirm_relic":
            if not run_id:
                return create_error_response("No active run", 400)

            try:
                result = await confirm_reward(run_id, "relic")
                return jsonify(result)
            except ValueError as exc:
                return create_error_response(str(exc), 400)

        elif action == "cancel_card":
            if not run_id:
                return create_error_response("No active run", 400)

            try:
                result = await cancel_reward(run_id, "card")
                return jsonify(result)
            except ValueError as exc:
                return create_error_response(str(exc), 400)

        elif action == "cancel_relic":
            if not run_id:
                return create_error_response("No active run", 400)

            try:
                result = await cancel_reward(run_id, "relic")
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
        return create_error_response(
            f"Action failed: {str(e)}",
            500,
            include_traceback=True,
            exc=e,
        )


