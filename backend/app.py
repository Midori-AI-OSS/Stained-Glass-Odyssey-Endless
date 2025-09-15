from __future__ import annotations

import asyncio
import logging
import os
import traceback

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
from routes.performance import perf_bp as performance_bp
from routes.players import bp as players_bp
from routes.rewards import bp as rewards_bp
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
app.register_blueprint(performance_bp, url_prefix='/performance')
app.register_blueprint(guidebook_bp, url_prefix='/guidebook')

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
        tb = traceback.format_exc()
        response = jsonify({"error": str(e), "traceback": tb})
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
async def start_background_tasks() -> None:
    asyncio.create_task(_cleanup_loop())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=59002)
