"""Utilities for recording battle turn timeout details."""

from __future__ import annotations

import asyncio
from dataclasses import asdict
from datetime import datetime
from datetime import timezone
import json
import logging
from pathlib import Path
from typing import Any
from typing import Iterable

from battle_logging.writers import get_current_run_logger

TURN_TIMEOUT_SECONDS = 35


class TurnTimeoutError(RuntimeError):
    """Raised when a battle turn iteration exceeds the allowed duration."""

    def __init__(self, actor_id: str, file_path: str):
        message = (
            f"Turn processing timed out for actor '{actor_id}'. "
            f"Details written to: {file_path}"
        )
        super().__init__(message)
        self.actor_id = actor_id
        self.file_path = file_path

log = logging.getLogger("autofighter.rooms.battle.turn_loop")


async def write_timeout_log(
    *,
    actor: Any,
    role: str,
    turn: int,
    run_id: str | None,
) -> Path:
    """Persist a JSON summary of the most recent events for a timed-out actor."""

    actor_id = identify_actor(actor)

    summary_path: Path | None = None
    events: Iterable[Any] = []
    try:
        run_logger = get_current_run_logger()
        if run_logger is not None:
            battle_logger = getattr(run_logger, "current_battle_logger", None)
            if battle_logger is not None:
                summary_path = Path(getattr(battle_logger, "summary_path"))
                events = list(getattr(battle_logger.summary, "events", []))
    except Exception as exc:  # pragma: no cover - defensive logging
        try:
            log.debug("Failed to read battle logger for timeout dump: %s", exc)
        except Exception:  # pragma: no cover - logging fallback
            pass
        summary_path = None

    if summary_path is None:
        summary_path = _fallback_summary_path(run_id)

    file_path = summary_path / f"{_sanitize_for_filename(actor_id)}_timeout_actions.json"

    payload = {
        "actor_id": actor_id,
        "role": role,
        "turn": turn,
        "run_id": run_id,
        "timeout_seconds": TURN_TIMEOUT_SECONDS,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "events": [_serialize_event(event) for event in _filter_events(events, actor_id)],
    }

    await asyncio.to_thread(_write_json, file_path, payload)
    return file_path


def identify_actor(actor: Any) -> str:
    """Return a stable identifier for an actor, falling back to its memory id."""

    for attr in ("id", "name"):
        value = getattr(actor, attr, None)
        if value:
            return str(value)
    return f"actor_{id(actor)}"


def _filter_events(events: Iterable[Any], actor_id: str) -> list[Any]:
    related: list[Any] = []
    for event in events:
        try:
            if _event_involves_actor(event, actor_id):
                related.append(event)
        except Exception:  # pragma: no cover - defensive filtering
            continue
    return related


def _event_involves_actor(event: Any, actor_id: str) -> bool:
    actor_id_str = str(actor_id)
    if actor_id_str in {str(getattr(event, "attacker_id", None)), str(getattr(event, "target_id", None))}:
        return True
    for mapping_name in ("details", "effect_details"):
        mapping = getattr(event, mapping_name, None)
        if isinstance(mapping, dict) and _mapping_contains_actor(mapping, actor_id_str):
            return True
    return False


def _mapping_contains_actor(mapping: dict[str, Any], actor_id: str) -> bool:
    for key in ("actor_id", "attacker_id", "target_id", "source_id", "owner_id"):
        value = mapping.get(key)
        if value is not None and str(value) == actor_id:
            return True
    return False


def _serialize_event(event: Any) -> dict[str, Any]:
    data = asdict(event)
    timestamp = getattr(event, "timestamp", None)
    if timestamp is not None:
        data["timestamp"] = timestamp.isoformat()
    data["details"] = _stringify(data.get("details", {}))
    data["effect_details"] = _stringify(data.get("effect_details", {}))
    return data


def _stringify(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _stringify(sub_value) for key, sub_value in value.items()}
    if isinstance(value, list):
        return [_stringify(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _fallback_summary_path(run_id: str | None) -> Path:
    base = Path(__file__).resolve().parents[4] / "logs" / "timeouts"
    if run_id:
        return base / run_id
    return base


def _sanitize_for_filename(value: str) -> str:
    safe_chars = [ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value]
    sanitized = "".join(safe_chars).strip("_")
    return sanitized or "actor"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, indent=2, ensure_ascii=False)


__all__ = [
    "TurnTimeoutError",
    "TURN_TIMEOUT_SECONDS",
    "identify_actor",
    "write_timeout_log",
]

