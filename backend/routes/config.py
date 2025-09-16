from __future__ import annotations

import math

from llms.loader import ModelName
from options import OptionKey
from options import get_option
from options import set_option
from quart import Blueprint
from quart import jsonify
from quart import request

from autofighter.rooms.battle.pacing import refresh_turn_pacing
from autofighter.rooms.battle.pacing import set_turn_pacing

bp = Blueprint("config", __name__, url_prefix="/config")

_TURN_PACING_DEFAULT = 0.5


@bp.get("/lrm")
async def get_lrm_config() -> tuple[str, int, dict[str, object]]:
    current = get_option(OptionKey.LRM_MODEL, ModelName.DEEPSEEK.value)
    models = [m.value for m in ModelName]
    return jsonify({"current_model": current, "available_models": models})


@bp.post("/lrm")
async def set_lrm_model() -> tuple[str, int, dict[str, str]]:
    data = await request.get_json()
    model = data.get("model", "")
    if model not in [m.value for m in ModelName]:
        return jsonify({"error": "invalid model"}), 400
    set_option(OptionKey.LRM_MODEL, model)
    return jsonify({"current_model": model})


@bp.post("/lrm/test")
async def test_lrm_model() -> tuple[str, int, dict[str, str]]:
    import asyncio

    from llms.loader import load_llm

    data = await request.get_json()
    prompt = data.get("prompt", "")
    model = get_option(OptionKey.LRM_MODEL, ModelName.DEEPSEEK.value)

    # Load LLM in thread pool to avoid blocking the event loop
    llm = await asyncio.to_thread(load_llm, model)
    reply = ""
    async for chunk in llm.generate_stream(prompt):
        reply += chunk
    return jsonify({"response": reply})


@bp.get("/turn_pacing")
async def get_turn_pacing() -> tuple[str, int, dict[str, float]]:
    value = refresh_turn_pacing()
    return jsonify({"turn_pacing": value, "default": _TURN_PACING_DEFAULT})


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

    value = set_turn_pacing(requested)
    set_option(OptionKey.TURN_PACING, f"{value}")
    return jsonify({"turn_pacing": value, "default": _TURN_PACING_DEFAULT})
