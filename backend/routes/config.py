from __future__ import annotations

import math

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
    import os

    current_model = get_option(OptionKey.LRM_MODEL, "openai/gpt-oss-20b")
    current_backend = get_option(OptionKey.LRM_BACKEND, "huggingface")
    current_api_url = get_option(OptionKey.LRM_API_URL, os.getenv("OPENAI_API_URL", ""))
    current_api_key = get_option(OptionKey.LRM_API_KEY, os.getenv("OPENAI_API_KEY", ""))

    # Mask the API key for security (only show first 4 and last 4 characters)
    masked_api_key = ""
    if current_api_key and len(current_api_key) > 8:
        masked_api_key = current_api_key[:4] + "..." + current_api_key[-4:]
    elif current_api_key:
        masked_api_key = "***"

    available_backends = ["auto", "openai", "huggingface"]

    # Default HuggingFace models (20b is default unless user requests 120b)
    available_models = [
        "openai/gpt-oss-20b",  # Default for HuggingFace
        "openai/gpt-oss-120b",
        "gpt-oss:20b",
        "gpt-oss:120b",
    ]

    payload = {
        "current_model": current_model,
        "current_backend": current_backend,
        "current_api_url": current_api_url,
        "current_api_key": masked_api_key,
        "available_backends": available_backends,
        "available_models": available_models,
    }
    try:
        await log_menu_action("Settings", "view_lrm", {"current": current_model, "backend": current_backend})
        await log_overlay_action("settings", {"section": "lrm"})
    except Exception:
        pass
    return jsonify(payload)


@bp.post("/lrm")
async def set_lrm_model() -> tuple[str, int, dict[str, str]]:
    import os

    data = await request.get_json()
    model = data.get("model", "")
    backend = data.get("backend", None)
    api_url = data.get("api_url", None)
    api_key = data.get("api_key", None)

    # Get current backend to determine validation rules
    current_backend = backend if backend else get_option(OptionKey.LRM_BACKEND, "huggingface")

    # For OpenAI backend, allow any model (to support newer models like GPT-5+)
    # For HuggingFace, validate against known models
    if current_backend == "huggingface" and model:
        valid_huggingface_models = [
            "openai/gpt-oss-20b",  # Default for HuggingFace
            "openai/gpt-oss-120b",
            "gpt-oss:20b",
            "gpt-oss:120b",
        ]
        if model not in valid_huggingface_models:
            return jsonify({"error": f"invalid model for huggingface backend: {model}"}), 400
    # For OpenAI backend, accept any model string (for flexibility with new models)

    # Validate backend if provided
    if backend and backend not in ["auto", "openai", "huggingface"]:
        return jsonify({"error": "invalid backend"}), 400

    # Update model if provided
    if model:
        old_model = get_option(OptionKey.LRM_MODEL, "openai/gpt-oss-20b")
        set_option(OptionKey.LRM_MODEL, model)
    else:
        model = get_option(OptionKey.LRM_MODEL, "openai/gpt-oss-20b")
        old_model = model

    # Update backend if provided
    if backend:
        old_backend = get_option(OptionKey.LRM_BACKEND, "huggingface")
        set_option(OptionKey.LRM_BACKEND, backend)
    else:
        backend = get_option(OptionKey.LRM_BACKEND, "huggingface")
        old_backend = backend

    # Update API URL if provided
    if api_url is not None:
        old_api_url = get_option(OptionKey.LRM_API_URL, os.getenv("OPENAI_API_URL", ""))
        set_option(OptionKey.LRM_API_URL, api_url)
    else:
        api_url = get_option(OptionKey.LRM_API_URL, os.getenv("OPENAI_API_URL", ""))
        old_api_url = api_url

    # Update API key if provided
    if api_key is not None:
        old_api_key = get_option(OptionKey.LRM_API_KEY, os.getenv("OPENAI_API_KEY", ""))
        set_option(OptionKey.LRM_API_KEY, api_key)
    else:
        api_key = get_option(OptionKey.LRM_API_KEY, os.getenv("OPENAI_API_KEY", ""))
        old_api_key = api_key

    # Mask the API key for security in response
    masked_api_key = ""
    if api_key and len(api_key) > 8:
        masked_api_key = api_key[:4] + "..." + api_key[-4:]
    elif api_key:
        masked_api_key = "***"

    try:
        await log_settings_change("lrm_model", old_model, model)
        if backend != old_backend:
            await log_settings_change("lrm_backend", old_backend, backend)
        if api_url != old_api_url:
            await log_settings_change("lrm_api_url", old_api_url, api_url)
        if api_key != old_api_key:
            await log_settings_change("lrm_api_key", "***", "***")  # Don't log actual keys
        await log_menu_action("Settings", "update_lrm", {
            "old_model": old_model,
            "new_model": model,
            "old_backend": old_backend,
            "new_backend": backend,
        })
    except Exception:
        pass

    return jsonify({
        "current_model": model,
        "current_backend": backend,
        "current_api_url": api_url,
        "current_api_key": masked_api_key,
    })


@bp.post("/lrm/test")
async def test_lrm_model() -> tuple[str, int, dict[str, str]]:
    from llms import load_agent
    from llms import validate_agent

    data = await request.get_json()
    prompt = data.get("prompt", "")
    model = get_option(OptionKey.LRM_MODEL, "openai/gpt-oss-20b")
    backend = get_option(OptionKey.LRM_BACKEND, "auto")

    try:
        # Load agent using the new framework
        agent_backend = None if backend == "auto" else backend
        agent = await load_agent(backend=agent_backend, model=model, validate=False)

        # Validate agent if no custom prompt provided
        if not prompt:
            is_valid = await validate_agent(agent)
            if not is_valid:
                return jsonify({"error": "Agent validation failed"}), 400
            return jsonify({"response": "Agent validation passed", "is_lrm": True})

        # Generate response to custom prompt using agent
        from midori_ai_agent_base import AgentPayload

        payload = AgentPayload(
            user_message=prompt,
            thinking_blob="",
            system_context="You are a helpful assistant for the AutoFighter game.",
            user_profile={},
            tools_available=[],
            session_id="test",
        )

        response = await agent.invoke(payload)
        return jsonify({"response": response.response})
    except ImportError as e:
        # Agent framework not available
        return jsonify({"error": f"Agent framework not available: {e}"}), 503
    except Exception as e:
        # Other errors
        return jsonify({"error": f"Test failed: {e}"}), 500


@bp.post("/lrm/backend")
async def set_lrm_backend() -> tuple[str, int, dict[str, str]]:
    data = await request.get_json()
    backend = data.get("backend", "")

    # Validate backend
    if backend not in ["auto", "openai", "huggingface"]:
        return jsonify({"error": "invalid backend. Must be one of: auto, openai, huggingface"}), 400

    old_backend = get_option(OptionKey.LRM_BACKEND, "auto")
    set_option(OptionKey.LRM_BACKEND, backend)

    try:
        await log_settings_change("lrm_backend", old_backend, backend)
        await log_menu_action("Settings", "update_lrm_backend", {"old": old_backend, "new": backend})
    except Exception:
        pass

    return jsonify({"current_backend": backend})


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
