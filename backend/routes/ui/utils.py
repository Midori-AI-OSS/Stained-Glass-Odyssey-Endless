"""Shared utility functions for UI routes."""

from __future__ import annotations

import sys
from typing import Any

from error_context import format_exception_with_context
from quart import jsonify
from runs.encryption import get_save_manager
from runs.lifecycle import normalise_reward_step


def create_error_response(
    message: str,
    status_code: int = 400,
    include_traceback: bool = False,
    exc: BaseException | None = None,
) -> tuple[str, int, dict[str, Any]]:
    """Create a consistent error response format.

    Args:
        message: Error message
        status_code: HTTP status code (default: 400)
        include_traceback: Whether to include traceback in response
        exc: Exception to format

    Returns:
        Tuple of (response, status_code)
    """
    error_data = {
        "error": message,
        "status": "error"
    }

    if include_traceback:
        exception = exc or sys.exc_info()[1]
        if exception is not None:
            traceback_text, context = format_exception_with_context(exception)
            error_data["traceback"] = traceback_text
            if context:
                error_data["context"] = context
        else:
            error_data["traceback"] = ""

    return jsonify(error_data), status_code


def validate_action_params(action: str, params: dict, required_fields: list[str]) -> str | None:
    """Validate that required parameters are present for an action.

    Args:
        action: Action name
        params: Parameters dictionary
        required_fields: List of required field names

    Returns:
        None if validation passes, or error message if validation fails
    """
    missing_fields = [field for field in required_fields if not params.get(field)]
    if missing_fields:
        return f"Action '{action}' missing required parameters: {', '.join(missing_fields)}"
    return None


def get_default_active_run() -> str | None:
    """Get the most recent active run, or None if no runs exist.

    Returns:
        Run ID or None
    """
    try:
        with get_save_manager().connection() as conn:
            # Get the first run (most recently created)
            cur = conn.execute("SELECT id FROM runs LIMIT 1")
            row = cur.fetchone()
            return row[0] if row else None
    except Exception:
        return None


def determine_ui_mode(game_state: dict[str, Any]) -> str:
    """Determine the current UI mode based on game state.

    Args:
        game_state: Current game state dictionary

    Returns:
        UI mode string (menu/playing/battle/card_selection/relic_selection/loot/battle_review)
    """
    if not game_state:
        return "menu"

    current_state = game_state.get("current_state", {})
    room_data = current_state.get("room_data")

    # Check for reward progression sequence first
    progression = current_state.get("reward_progression")
    if progression and progression.get("current_step"):
        step = normalise_reward_step(progression.get("current_step"))
        if step == "cards":
            return "card_selection"
        elif step == "relics":
            return "relic_selection"
        elif step == "drops":
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
    """Get list of available actions for the current UI mode.

    Args:
        mode: UI mode string
        game_state: Current game state dictionary

    Returns:
        List of available action names
    """
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
