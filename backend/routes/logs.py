from __future__ import annotations

import asyncio
from pathlib import Path

from quart import Blueprint
from quart import jsonify
from quart import send_file
from services.run_service import get_battle_summary

bp = Blueprint("logs", __name__, url_prefix="/logs")


def _resolve_battles_root(run_id: str) -> Path | None:
    base = Path(__file__).resolve().parents[1]
    primary = base / "logs" / "runs" / run_id / "battles"
    if primary.exists():
        return primary
    fallback = base / "battle_logging" / "logs" / "runs" / run_id / "battles"
    if fallback.exists():
        return fallback
    return None


def _resolve_summary_file(run_id: str, index: int, filename: str) -> Path | None:
    base = Path(__file__).resolve().parents[1]
    primary = base / "logs" / "runs" / run_id / "battles" / str(index) / "summary" / filename
    if primary.exists():
        return primary
    fallback = base / "battle_logging" / "logs" / "runs" / run_id / "battles" / str(index) / "summary" / filename
    if fallback.exists():
        return fallback
    return None


async def _collect_battle_indexes(root: Path) -> list[int]:
    def gather() -> list[int]:
        indexes: list[int] = []
        for entry in root.iterdir():
            if entry.is_dir() and entry.name.isdigit():
                indexes.append(int(entry.name))
        return sorted(indexes)

    return await asyncio.to_thread(gather)


@bp.get("/<run_id>")
async def run_logs(run_id: str):
    battles_root = _resolve_battles_root(run_id)
    if battles_root is None:
        return jsonify({"error": "run logs not found"}), 404

    indexes = await _collect_battle_indexes(battles_root)
    battles: list[dict[str, object]] = []
    for index in indexes:
        summary = await get_battle_summary(run_id, index)
        if summary is None:
            continue
        battles.append(
            {
                "index": index,
                "summary": summary,
                "summary_url": f"/logs/{run_id}/battles/{index}/summary",
                "events_url": f"/logs/{run_id}/battles/{index}/events",
            }
        )

    payload = {
        "run_id": run_id,
        "battle_count": len(battles),
        "available_battles": indexes,
        "battles": battles,
    }
    return jsonify(payload)


@bp.get("/<run_id>/battles/<int:index>/summary")
async def run_battle_summary(run_id: str, index: int):
    summary = await get_battle_summary(run_id, index)
    if summary is None:
        return jsonify({"error": "battle summary not found"}), 404
    return jsonify(summary)


@bp.get("/<run_id>/battles/<int:index>/events")
async def run_battle_events(run_id: str, index: int):
    events_path = _resolve_summary_file(run_id, index, "events.json")
    if events_path is None:
        return jsonify({"error": "battle events not found"}), 404
    return await send_file(events_path, mimetype="application/json")
