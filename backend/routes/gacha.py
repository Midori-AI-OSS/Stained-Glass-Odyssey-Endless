from __future__ import annotations

import asyncio
from dataclasses import asdict

from quart import Blueprint
from quart import jsonify
from quart import request
from runs.encryption import get_save_manager

from autofighter.gacha import GachaManager

bp = Blueprint("gacha", __name__)


@bp.get("/gacha")
async def gacha_state() -> tuple[str, int, dict[str, object]]:
    def get_gacha_state():
        manager = GachaManager(get_save_manager())
        return manager.get_state()

    state = await asyncio.to_thread(get_gacha_state)
    return jsonify(state)


@bp.post("/gacha/pull")
async def gacha_pull() -> tuple[str, int, dict[str, object]]:
    data = await request.get_json(silent=True) or {}
    count = int(data.get("count", 1))
    banner_id = str(data.get("banner_id", "standard"))

    def do_pull():
        manager = GachaManager(get_save_manager())
        try:
            results = manager.pull(count, banner_id)
            state = manager.get_state()
            state["results"] = [asdict(r) for r in results]
            return state, None
        except ValueError as e:
            return None, str(e)
        except PermissionError:
            return None, "insufficient tickets"

    result, error = await asyncio.to_thread(do_pull)
    if error == "invalid count":
        return jsonify({"error": "invalid count"}), 400
    if error == "banner not available":
        return jsonify({"error": "banner not available"}), 400
    if error == "insufficient tickets":
        return jsonify({"error": "insufficient tickets"}), 403
    return jsonify(result)
