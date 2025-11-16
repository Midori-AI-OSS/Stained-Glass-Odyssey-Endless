from __future__ import annotations

import asyncio
import logging
import os

from error_context import format_exception_with_context

# Import torch checker early to perform the one-time check
from llms.torch_checker import is_torch_available
from logging_config import configure_logging
from quart import Quart
from quart import Response
from quart import jsonify
from quart import request
from routes.assets import bp as assets_bp
from routes.catalog import bp as catalog_bp
from routes.config import bp as config_bp
from routes.gacha import bp as gacha_bp
from routes.guidebook import bp as guidebook_bp
from routes.logs import bp as logs_bp
from routes.performance import perf_bp as performance_bp
from routes.players import bp as players_bp
from routes.rewards import bp as rewards_bp
from routes.tracking import bp as tracking_bp
from routes.ui import bp as ui_bp
from runs.encryption import get_fernet  # noqa: F401
from runs.encryption import get_save_manager  # noqa: F401
from runs.lifecycle import _run_battle  # noqa: F401
from runs.lifecycle import battle_snapshots  # noqa: F401
from runs.lifecycle import battle_tasks  # noqa: F401
from runs.lifecycle import cleanup_battle_state
from runs.lifecycle import load_map  # noqa: F401
from runs.lifecycle import save_map  # noqa: F401
from runs.party_manager import _apply_player_customization  # noqa: F401
from runs.party_manager import _assign_damage_type  # noqa: F401
from runs.party_manager import _describe_passives  # noqa: F401
from runs.party_manager import _load_player_customization  # noqa: F401
from runs.party_manager import load_party  # noqa: F401
from runs.party_manager import save_party  # noqa: F401
from services.run_service import prune_runs_on_startup
from werkzeug.exceptions import HTTPException

from autofighter.gacha import GachaManager  # noqa: F401  # re-export for tests
from autofighter.rooms import _scale_stats  # noqa: F401

configure_logging()

log = logging.getLogger(__name__)

# Log torch availability status on startup
log.info("Torch availability check: %s", "available" if is_torch_available() else "not available")

app = Quart(__name__)
app.register_blueprint(assets_bp)
app.register_blueprint(gacha_bp)
app.register_blueprint(players_bp)
app.register_blueprint(rewards_bp)
app.register_blueprint(config_bp)
app.register_blueprint(catalog_bp)
app.register_blueprint(ui_bp)
app.register_blueprint(tracking_bp)
app.register_blueprint(performance_bp, url_prefix='/performance')
app.register_blueprint(guidebook_bp, url_prefix='/guidebook')
app.register_blueprint(logs_bp)

BACKEND_FLAVOR = os.getenv("UV_EXTRA", "default")


async def request_shutdown() -> None:
    """Cancel tasks, flush logs, and stop the event loop."""
    loop = asyncio.get_running_loop()
    tasks = [t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)

    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        try:
            handler.flush()
        except Exception:
            pass

    await app.shutdown()
    loop.stop()


@app.get("/")
async def status() -> Response:
    return jsonify({"status": "ok", "flavor": BACKEND_FLAVOR})


@app.after_request
async def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return response


@app.before_request
async def handle_cors_preflight():
    if request.method == "OPTIONS":
        return "", 204


@app.errorhandler(Exception)
async def handle_exception(e: Exception):
    log.exception(e)
    response: Response
    if isinstance(e, HTTPException):
        response = jsonify({"error": str(e)})
        response.status_code = e.code or 500
    else:
        traceback_text, context = format_exception_with_context(e)
        payload = {"error": str(e), "traceback": traceback_text}
        if context:
            payload["context"] = context
        response = jsonify(payload)
        response.status_code = 500
        await request_shutdown()

    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return response


async def _cleanup_loop() -> None:
    while True:
        await asyncio.sleep(300)
        await cleanup_battle_state()


@app.before_serving
async def prune_runs_before_serving() -> None:
    await prune_runs_on_startup()


@app.before_serving
async def validate_lrm_on_startup() -> None:
    """Validate the configured LRM on startup to ensure it's ready and capable of reasoning."""
    try:
        # Check if torch is available for local models
        torch_available = is_torch_available()

        # Check if remote OpenAI is configured
        openai_url = os.getenv("OPENAI_API_URL", "unset")

        # Skip validation if neither remote nor local LRM is available
        if openai_url == "unset" and not torch_available:
            log.info("No LRM available - neither remote (OPENAI_API_URL) nor local (torch). Skipping startup validation.")
            return

        # Import here to avoid circular dependencies
        from llms.loader import ModelName
        from llms.loader import load_llm
        from llms.loader import validate_lrm
        from options import OptionKey
        from options import get_option

        # Get configured model or use default
        model = get_option(OptionKey.LRM_MODEL, ModelName.OPENAI_20B.value)

        # Log which type of LRM we're testing
        if openai_url != "unset":
            log.info("Remote LRM configured (OPENAI_API_URL=%s). Testing connection...", openai_url)
        elif torch_available:
            log.info("Local LRM configured (torch available). Testing model: %s...", model)

        # Load and validate the LRM
        llm = await asyncio.to_thread(load_llm, model, validate=False)
        is_valid = await validate_lrm(llm)

        if is_valid:
            log.info("✓ LRM validation passed - model is ready for reasoning tasks")
        else:
            log.warning("✗ LRM validation failed - model may not support reasoning properly")
    except Exception as e:
        log.warning("LRM validation failed with error: %s", e)
        log.info("Server will continue starting. LRM may not be available.")



@app.before_serving
async def start_background_tasks() -> None:
    asyncio.create_task(_cleanup_loop())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=59002)
