"""Battle information endpoints."""

from quart import jsonify
from services.run_service import get_battle_events
from services.run_service import get_battle_summary

from . import bp
from .utils import create_error_response
from .utils import get_default_active_run


@bp.get("/battles/<int:index>/summary")
async def battle_summary(index: int):
    """Get battle summary for a specific battle index.

    Args:
        index: Battle index

    Returns:
        JSON with battle summary or 404 error
    """
    run_id = get_default_active_run()
    if not run_id:
        return create_error_response("No active run", 404)

    data = await get_battle_summary(run_id, index)
    if data is None:
        return create_error_response("Battle summary not found", 404)

    return jsonify(data)


@bp.get("/battles/<int:index>/events")
async def battle_events(index: int):
    """Get battle events for a specific battle index.

    Args:
        index: Battle index

    Returns:
        JSON with battle events or 404 error
    """
    run_id = get_default_active_run()
    if not run_id:
        return create_error_response("No active run", 404)

    data = await get_battle_events(run_id, index)
    if data is None:
        return create_error_response("Battle events not found", 404)

    return jsonify(data)
