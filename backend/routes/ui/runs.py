"""Run management endpoints."""

from __future__ import annotations

import asyncio
from typing import Any

from quart import jsonify
from quart import request
from runs.encryption import get_save_manager
from services.run_configuration import get_run_configuration_metadata
from services.run_service import shutdown_run
from services.run_service import start_run
from tracking import log_menu_action

from . import bp


@bp.get("/run/config")
async def run_configuration_metadata() -> tuple[str, int, dict[str, Any]]:
    """Get run configuration metadata.

    Returns:
        JSON with configuration metadata
    """
    metadata = get_run_configuration_metadata()
    try:
        await log_menu_action("Run", "view_config", {"version": metadata.get("version")})
    except Exception:
        pass
    return jsonify(metadata), 200


@bp.post("/run/start")
async def start_run_endpoint() -> tuple[str, int, dict[str, Any]]:
    """Start a new run.

    Request JSON:
        party: List of party member IDs (default: ["player"])
        damage_type: Damage type string
        pressure: Pressure level (int)
        run_type: Run type identifier
        modifiers: Run modifiers
        metadata_version: Configuration metadata version

    Returns:
        JSON with run start result or error
    """
    try:
        data = await request.get_json()
        members = data.get("party", ["player"])
        damage_type = data.get("damage_type", "")
        pressure = data.get("pressure", 0)
        run_type = data.get("run_type")
        modifiers = data.get("modifiers")
        metadata_version = data.get("metadata_version")

        try:
            result = await start_run(
                members,
                damage_type,
                pressure,
                run_type=run_type,
                modifiers=modifiers,
                metadata_version=metadata_version,
            )
            return jsonify(result), 200
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
            return jsonify({"error": str(exc)}), 400

    except Exception as e:
        return jsonify({"error": f"Failed to start run: {str(e)}"}), 500


@bp.delete("/run/<run_id>")
async def end_run(run_id: str) -> tuple[str, int, dict[str, Any]]:
    """End a specific run by deleting it from the database.

    Args:
        run_id: Run identifier

    Returns:
        JSON with success message or error
    """
    try:
        run_ended = await shutdown_run(run_id)
        if not run_ended:
            return jsonify({"error": "Run not found"}), 404

        return jsonify({"message": "Run ended successfully"}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to end run: {str(e)}"}), 500


@bp.delete("/runs")
async def end_all_runs() -> tuple[str, int, dict[str, Any]]:
    """End all runs by deleting them from the database.

    Returns:
        JSON with deleted count and any failures
    """
    def collect_run_ids() -> list[str]:
        with get_save_manager().connection() as conn:
            cur = conn.execute("SELECT id FROM runs")
            return [row[0] for row in cur.fetchall() if row and row[0]]

    try:
        run_ids = await asyncio.to_thread(collect_run_ids)
        deleted = 0
        failed: list[str] = []

        for run_id in run_ids:
            try:
                removed = await shutdown_run(run_id)
            except Exception:  # pragma: no cover - defensive cleanup guardrail
                failed.append(run_id)
                continue

            if removed:
                deleted += 1
            else:
                failed.append(run_id)

        await log_menu_action(
            "Run",
            "ended_all",
            {"deleted_count": deleted, "requested_count": len(run_ids), "failed": failed},
        )

        status = 200 if not failed else 207
        payload: dict[str, Any] = {
            "message": f"Ended {deleted} run(s) successfully",
            "deleted_count": deleted,
            "requested_count": len(run_ids),
        }
        if failed:
            payload["failed"] = failed

        return jsonify(payload), status

    except Exception as e:
        return jsonify({"error": f"Failed to end runs: {str(e)}"}), 500
