"""Save management endpoints."""

from __future__ import annotations

from typing import Any

from quart import jsonify
from quart import request
from services.run_service import backup_save
from services.run_service import restore_save
from services.run_service import wipe_save

from . import bp


@bp.get("/save/backup")
async def backup_save_endpoint() -> tuple[str, int, dict[str, Any]]:
    """Export save data as an encrypted backup.

    Returns:
        Encrypted backup data as binary
    """
    try:
        backup_data = await backup_save()
        return backup_data, 200, {"Content-Type": "application/octet-stream"}
    except Exception as e:
        return jsonify({"error": f"Failed to backup save: {str(e)}"}), 500


@bp.post("/save/restore")
async def restore_save_endpoint() -> tuple[str, int, dict[str, Any]]:
    """Restore save data from an encrypted backup.

    Request Body:
        Binary encrypted backup data

    Returns:
        JSON with success message or error
    """
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
    """Wipe all save data and recreate the database.

    Returns:
        JSON with success message or error
    """
    try:
        await wipe_save()
        return jsonify({"message": "Save wiped successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to wipe save: {str(e)}"}), 500
