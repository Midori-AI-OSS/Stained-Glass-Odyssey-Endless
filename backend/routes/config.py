from __future__ import annotations

import math

from llms.loader import ModelName
from options import OptionKey
from options import get_option
from options import set_option
from quart import Blueprint
from quart import jsonify
from quart import request
from tracking import log_menu_action
from tracking import log_overlay_action
from tracking import log_settings_change

from autofighter.rooms.battle.pacing import refresh_turn_pacing
from autofighter.rooms.battle.pacing import set_turn_pacing

bp = Blueprint("config", __name__, url_prefix="/config")

_TURN_PACING_DEFAULT = 0.5


@bp.get("/lrm")
async def get_lrm_config() -> tuple[str, int, dict[str, object]]:
    current = get_option(OptionKey.LRM_MODEL, ModelName.OPENAI_20B.value)
    models = [m.value for m in ModelName]
    payload = {"current_model": current, "available_models": models}
    try:
        await log_menu_action("Settings", "view_lrm", {"current": current})
        await log_overlay_action("settings", {"section": "lrm"})
    except Exception:
        pass
    return jsonify(payload)


@bp.post("/lrm")
async def set_lrm_model() -> tuple[str, int, dict[str, str]]:
    data = await request.get_json()
    model = data.get("model", "")
    if model not in [m.value for m in ModelName]:
        return jsonify({"error": "invalid model"}), 400
    old_value = get_option(OptionKey.LRM_MODEL, ModelName.OPENAI_20B.value)
    set_option(OptionKey.LRM_MODEL, model)
    try:
        await log_settings_change("lrm_model", old_value, model)
        await log_menu_action("Settings", "update_lrm", {"old": old_value, "new": model})
    except Exception:
        pass
    return jsonify({"current_model": model})


@bp.post("/lrm/test")
async def test_lrm_model() -> tuple[str, int, dict[str, str]]:
    import asyncio

    from llms.loader import load_llm
    from llms.loader import validate_lrm

    data = await request.get_json()
    prompt = data.get("prompt", "")
    model = get_option(OptionKey.LRM_MODEL, ModelName.OPENAI_20B.value)

    # Load LLM in thread pool to avoid blocking the event loop
    llm = await asyncio.to_thread(load_llm, model, validate=False)

    # Validate it's an LRM if no custom prompt provided
    if not prompt:
        is_valid = await validate_lrm(llm)
        if not is_valid:
            return jsonify({"error": "Model validation failed - may not be an LRM"}), 400
        return jsonify({"response": "Model validation passed", "is_lrm": True})

    # Otherwise, generate response to custom prompt
    reply = ""
    async for chunk in llm.generate_stream(prompt):
        reply += chunk
    return jsonify({"response": reply})


@bp.get("/turn_pacing")
async def get_turn_pacing() -> tuple[str, int, dict[str, float]]:
    value = refresh_turn_pacing()
    payload = {"turn_pacing": value, "default": _TURN_PACING_DEFAULT}
    try:
        await log_menu_action("Settings", "view_turn_pacing", {"value": value})
        await log_overlay_action("settings", {"section": "turn_pacing"})
    except Exception:
        pass
    return jsonify(payload)


@bp.post("/turn_pacing")
async def update_turn_pacing() -> tuple[str, int, dict[str, float]]:
    data = await request.get_json()
    if not isinstance(data, dict) or "turn_pacing" not in data:
        return jsonify({"error": "turn_pacing is required"}), 400

    try:
        requested = float(data["turn_pacing"])
    except (TypeError, ValueError):
        return jsonify({"error": "turn_pacing must be numeric"}), 400

    if not math.isfinite(requested):
        return jsonify({"error": "turn_pacing must be finite"}), 400

    if requested <= 0:
        return jsonify({"error": "turn_pacing must be positive"}), 400

    old = get_option(OptionKey.TURN_PACING, f"{_TURN_PACING_DEFAULT}")
    value = set_turn_pacing(requested)
    set_option(OptionKey.TURN_PACING, f"{value}")
    try:
        await log_settings_change("turn_pacing", old, value)
        await log_menu_action("Settings", "update_turn_pacing", {"old": old, "new": value})
    except Exception:
        pass
    return jsonify({"turn_pacing": value, "default": _TURN_PACING_DEFAULT})


@bp.get("/concise_descriptions")
async def get_concise_descriptions() -> tuple[str, int, dict[str, bool]]:
    value = get_option(OptionKey.CONCISE_DESCRIPTIONS, "false")
    enabled = value.lower() == "true"
    payload = {"enabled": enabled}
    try:
        await log_menu_action("Settings", "view_concise_descriptions", {"enabled": enabled})
        await log_overlay_action("settings", {"section": "concise_descriptions"})
    except Exception:
        pass
    return jsonify(payload)


@bp.post("/concise_descriptions")
async def update_concise_descriptions() -> tuple[str, int, dict[str, bool]]:
    data = await request.get_json()
    if not isinstance(data, dict) or "enabled" not in data:
        return jsonify({"error": "enabled is required"}), 400

    enabled = bool(data["enabled"])
    old = get_option(OptionKey.CONCISE_DESCRIPTIONS, "false")
    set_option(OptionKey.CONCISE_DESCRIPTIONS, "true" if enabled else "false")
    try:
        await log_settings_change("concise_descriptions", old, enabled)
        await log_menu_action("Settings", "update_concise_descriptions", {"old": old, "new": enabled})
    except Exception:
        pass
    return jsonify({"enabled": enabled})
