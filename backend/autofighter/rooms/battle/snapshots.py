from __future__ import annotations

from collections import deque
from typing import Any
from typing import Iterable
import weakref

from autofighter.party import Party

from ...stats import Stats

__all__ = [
    "register_snapshot_entities",
    "prepare_snapshot_overlay",
    "mutate_snapshot_overlay",
    "canonical_entity_id",
    "canonical_entity_pair",
    "resolve_run_id",
    "set_effect_charges",
    "get_effect_charges",
    "clear_effect_charges",
    "get_recent_events",
    "get_status_phase",
    "get_registered_entities",
    "get_registered_run_ids",
]

_MISSING = object()
# Retain enough combat log entries to cover large bursts between
# frontend polls. Forty events captures multiple turns of activity while
# keeping payload sizes small enough for websocket updates.
_RECENT_EVENT_LIMIT = 40

_entity_run_ids: dict[int, str] = {}
_entity_refs: dict[int, weakref.ref[Stats]] = {}
_party_run_ids: dict[int, str] = {}
_party_refs: dict[int, weakref.ref[Party]] = {}
_recent_events: dict[str, deque[dict[str, Any]]] = {}
_status_phases: dict[str, dict[str, Any] | None] = {}
_effect_charges: dict[str, list[dict[str, Any]]] = {}


def canonical_entity_id(entity: Any) -> str | None:
    """Return a canonical identifier for a combatant.

    Prefers ``instance_id`` to disambiguate duplicate summons while falling
    back to the legacy ``id`` attribute for non-summoned entities. All values
    are normalised to strings to simplify downstream comparisons.
    """

    if entity is None:
        return None

    identifier = getattr(entity, "instance_id", None)
    if identifier is None:
        identifier = getattr(entity, "id", None)
    if identifier is None:
        return None

    try:
        return str(identifier)
    except Exception:
        return None


def canonical_entity_pair(entity: Any) -> tuple[str | None, str | None]:
    """Return canonical and legacy identifiers for a combatant."""

    canonical = canonical_entity_id(entity)

    legacy: str | None
    if entity is None:
        legacy = None
    else:
        raw_legacy = getattr(entity, "id", None)
        if raw_legacy is None:
            legacy = None
        else:
            try:
                legacy = str(raw_legacy)
            except Exception:
                legacy = None

    if legacy == canonical:
        legacy = None

    return canonical, legacy


def resolve_run_id(*entities: Any) -> str | None:
    for entity in entities:
        if isinstance(entity, Stats):
            run_id = _entity_run_ids.get(id(entity))
            if run_id:
                return run_id
        if isinstance(entity, Party):
            run_id = _party_run_ids.get(id(entity))
            if run_id:
                return run_id
    return None


def register_snapshot_entities(run_id: str | None, entities: Iterable[Any]) -> None:
    if not run_id:
        return
    for entity in entities:
        if isinstance(entity, Stats):
            ident = id(entity)

            def _cleanup(_ref: weakref.ref[Stats], *, key: int = ident) -> None:
                _entity_run_ids.pop(key, None)
                _entity_refs.pop(key, None)

            _entity_run_ids[ident] = run_id
            _entity_refs[ident] = weakref.ref(entity, _cleanup)
        elif isinstance(entity, Party):
            ident = id(entity)

            def _cleanup(_ref: weakref.ref[Party], *, key: int = ident) -> None:
                _party_run_ids.pop(key, None)
                _party_refs.pop(key, None)

            _party_run_ids[ident] = run_id
            _party_refs[ident] = weakref.ref(entity, _cleanup)


def get_registered_entities(run_id: str | None) -> list[Any]:
    """Return active entities registered for a given run id."""

    if not run_id:
        return []

    seen: set[int] = set()
    entities: list[Any] = []

    for mapping, refs in (
        (_party_run_ids, _party_refs),
        (_entity_run_ids, _entity_refs),
    ):
        for ident, stored_run_id in list(mapping.items()):
            if stored_run_id != run_id:
                continue

            ref = refs.get(ident)
            obj = ref() if ref else None
            if obj is None:
                mapping.pop(ident, None)
                refs.pop(ident, None)
                continue

            key = id(obj)
            if key in seen:
                continue
            seen.add(key)
            entities.append(obj)

    return entities


def get_registered_run_ids() -> set[str]:
    """Return all run ids tracked by snapshot registries."""

    run_ids: set[str] = set()

    run_ids.update(rid for rid in _entity_run_ids.values() if rid)
    run_ids.update(rid for rid in _party_run_ids.values() if rid)
    run_ids.update(rid for rid in _recent_events if rid)
    run_ids.update(rid for rid in _status_phases if rid)
    run_ids.update(rid for rid in _effect_charges if rid)

    return run_ids


def prepare_snapshot_overlay(run_id: str | None, entities: Iterable[Any]) -> None:
    if not run_id:
        return
    register_snapshot_entities(run_id, entities)
    queue = _recent_events.get(run_id)
    if queue is None or queue.maxlen != _RECENT_EVENT_LIMIT:
        queue = deque(maxlen=_RECENT_EVENT_LIMIT)
        _recent_events[run_id] = queue
    else:
        queue.clear()
    _status_phases.pop(run_id, None)
    clear_effect_charges(run_id)
    snapshot = _get_snapshot(run_id)
    snapshot.setdefault("recent_events", [])
    snapshot.pop("status_phase", None)


def mutate_snapshot_overlay(
    run_id: str | None,
    *,
    active_id: str | None | object = _MISSING,
    active_target_id: str | None | object = _MISSING,
    legacy_active_id: str | None | object = _MISSING,
    legacy_active_target_id: str | None | object = _MISSING,
    status_phase: dict[str, Any] | None | object = _MISSING,
    event: dict[str, Any] | None = None,
) -> None:
    if not run_id:
        return
    snapshot = _get_snapshot(run_id)
    if active_id is not _MISSING:
        snapshot["active_id"] = active_id
    if active_target_id is not _MISSING:
        snapshot["active_target_id"] = active_target_id
    if legacy_active_id is not _MISSING:
        snapshot["legacy_active_id"] = legacy_active_id
    if legacy_active_target_id is not _MISSING:
        snapshot["legacy_active_target_id"] = legacy_active_target_id
    if status_phase is not _MISSING and (
        status_phase is None or isinstance(status_phase, dict)
    ):
        _status_phases[run_id] = status_phase
        snapshot["status_phase"] = status_phase
    elif run_id in _status_phases:
        snapshot["status_phase"] = _status_phases[run_id]
    if event is not None:
        queue = _ensure_event_queue(run_id)
        queue.append(event)
    queue = _recent_events.get(run_id)
    if queue is not None:
        snapshot["recent_events"] = list(queue)


def get_recent_events(run_id: str | None) -> list[dict[str, Any]] | None:
    if not run_id:
        return None
    queue = _recent_events.get(run_id)
    if queue is None:
        return None
    return list(queue)


def get_status_phase(run_id: str | None) -> dict[str, Any] | None:
    if not run_id:
        return None
    return _status_phases.get(run_id)


def set_effect_charges(
    run_id: str | None,
    payload: Iterable[dict[str, Any]] | dict[str, Any] | None,
) -> None:
    if not run_id:
        return
    if not payload:
        clear_effect_charges(run_id)
        return
    if isinstance(payload, dict):
        entries = [dict(payload)]
    else:
        entries = [dict(entry) for entry in payload if entry]
    if not entries:
        clear_effect_charges(run_id)
        return
    _effect_charges[run_id] = [dict(entry) for entry in entries]
    snapshot = _get_snapshot(run_id)
    snapshot["effects_charge"] = [dict(entry) for entry in entries]


def get_effect_charges(run_id: str | None) -> list[dict[str, Any]] | None:
    if not run_id:
        return None
    payload = _effect_charges.get(run_id)
    if payload is None:
        return None
    return [dict(entry) for entry in payload]


def clear_effect_charges(run_id: str | None) -> None:
    if not run_id:
        return
    _effect_charges.pop(run_id, None)
    snapshot = _get_snapshot(run_id)
    snapshot.pop("effects_charge", None)


def _ensure_event_queue(run_id: str) -> deque[dict[str, Any]]:
    queue = _recent_events.get(run_id)
    if queue is None or queue.maxlen != _RECENT_EVENT_LIMIT:
        queue = deque(queue or (), maxlen=_RECENT_EVENT_LIMIT)
        _recent_events[run_id] = queue
    return queue


def _get_snapshot(run_id: str) -> dict[str, Any]:
    from runs.lifecycle import battle_snapshots

    snap = battle_snapshots.get(run_id)
    if snap is None:
        snap = {"result": "battle"}
        battle_snapshots[run_id] = snap
    return snap
