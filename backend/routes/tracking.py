from __future__ import annotations

import asyncio
import json
from typing import Any

from quart import Blueprint
from quart import jsonify
from tracking import get_tracking_manager

bp = Blueprint("tracking", __name__, url_prefix="/tracking")


def _rows_to_dict(cursor_description: list[tuple[str, ...]], rows: list[tuple[Any, ...]]) -> list[dict[str, Any]]:
    keys = [col[0] for col in cursor_description]
    return [dict(zip(keys, row, strict=False)) for row in rows]


def _parse_json(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, (bytes, bytearray)):
        value = value.decode()
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _inject_configuration(payload: dict[str, Any]) -> dict[str, Any]:
    run_type = payload.pop("run_type", None)
    modifiers_raw = payload.pop("modifiers_json", None)
    reward_raw = payload.pop("reward_json", None)

    modifiers = _parse_json(modifiers_raw)
    reward_bonuses = _parse_json(reward_raw)

    configuration: dict[str, Any] = {
        "run_type": run_type,
        "modifiers": modifiers if isinstance(modifiers, (dict, list)) else modifiers,
        "reward_bonuses": reward_bonuses if isinstance(reward_bonuses, (dict, list)) else reward_bonuses,
    }

    # Avoid empty configuration payloads when nothing is stored for the run.
    if any(value is not None for value in configuration.values()):
        payload["configuration"] = configuration

    return payload


@bp.get("/runs")
async def list_runs():
    def fetch():
        manager = get_tracking_manager()
        with manager.connection() as conn:
            cur = conn.execute(
                """
                SELECT
                    runs.run_id,
                    runs.start_ts,
                    runs.end_ts,
                    runs.outcome,
                    run_configurations.run_type,
                    run_configurations.modifiers_json,
                    run_configurations.reward_json
                FROM runs
                LEFT JOIN run_configurations ON run_configurations.run_id = runs.run_id
                ORDER BY runs.start_ts DESC
                """
            )
            rows = cur.fetchall()
            payloads = _rows_to_dict(cur.description, rows)
            return [_inject_configuration(payload) for payload in payloads]

    runs = await asyncio.to_thread(fetch)
    return jsonify({"runs": runs})


@bp.get("/runs/<run_id>")
async def run_detail(run_id: str):
    def fetch():
        manager = get_tracking_manager()
        with manager.connection() as conn:
            cur = conn.execute(
                """
                SELECT
                    runs.run_id,
                    runs.start_ts,
                    runs.end_ts,
                    runs.outcome,
                    run_configurations.run_type,
                    run_configurations.modifiers_json,
                    run_configurations.reward_json
                FROM runs
                LEFT JOIN run_configurations ON run_configurations.run_id = runs.run_id
                WHERE runs.run_id = ?
                """,
                (run_id,),
            )
            run_row = cur.fetchone()
            if run_row is None:
                return None
            run_info = dict(zip([col[0] for col in cur.description], run_row, strict=False))
            run_info = _inject_configuration(run_info)
            member_cur = conn.execute(
                "SELECT slot, character_id, stats_json FROM party_members WHERE run_id = ? ORDER BY slot",
                (run_id,),
            )
            members = _rows_to_dict(member_cur.description, member_cur.fetchall())
            battle_cur = conn.execute(
                "SELECT room_id, turns, dmg_dealt, dmg_taken, victory, logs_url, ts FROM battle_summaries WHERE run_id = ? ORDER BY ts",
                (run_id,),
            )
            battles = _rows_to_dict(battle_cur.description, battle_cur.fetchall())
            return {
                "run": run_info,
                "party": members,
                "battles": battles,
            }

    data = await asyncio.to_thread(fetch)
    if data is None:
        return jsonify({"error": "run not found"}), 404
    return jsonify(data)


@bp.get("/aggregates")
async def tracking_aggregates():
    def fetch():
        manager = get_tracking_manager()
        with manager.connection() as conn:
            total_runs = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
            victories = conn.execute(
                "SELECT COUNT(*) FROM runs WHERE outcome = 'victory'"
            ).fetchone()[0]
            defeats = conn.execute(
                "SELECT COUNT(*) FROM runs WHERE outcome = 'defeat'"
            ).fetchone()[0]
            avg_duration = conn.execute(
                "SELECT AVG(duration) FROM play_sessions WHERE duration IS NOT NULL"
            ).fetchone()[0]
            return {
                "total_runs": total_runs,
                "victories": victories,
                "defeats": defeats,
                "average_session_duration": avg_duration or 0,
            }

    data = await asyncio.to_thread(fetch)
    return jsonify(data)
