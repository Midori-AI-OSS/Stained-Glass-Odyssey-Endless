from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass
import logging
from typing import TYPE_CHECKING
from typing import Any
from typing import Awaitable
from typing import Callable
from typing import Iterable
from typing import MutableMapping
from typing import Sequence
import weakref

from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from autofighter.summons.base import Summon
from autofighter.summons.manager import SummonManager

from ...stats import Stats
from ...stats import set_enrage_percent
from ..utils import _serialize

if TYPE_CHECKING:
    from autofighter.effects import EffectManager

log = logging.getLogger(__name__)

_MISSING = object()
_RECENT_EVENT_LIMIT = 6

_entity_run_ids: dict[int, str] = {}
_entity_refs: dict[int, weakref.ref[Stats]] = {}
_recent_events: dict[str, deque[dict[str, Any]]] = {}
_status_phases: dict[str, dict[str, Any] | None] = {}

def _resolve_run_id(*entities: Any) -> str | None:
    for entity in entities:
        if isinstance(entity, Stats):
            run_id = _entity_run_ids.get(id(entity))
            if run_id:
                return run_id
    return None


def register_snapshot_entities(run_id: str | None, entities: Iterable[Any]) -> None:
    """Associate combatants with a run for incremental snapshot updates."""

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


def prepare_snapshot_overlay(run_id: str | None, entities: Iterable[Any]) -> None:
    """Reset incremental snapshot state and register the supplied combatants."""

    if not run_id:
        return
    register_snapshot_entities(run_id, entities)
    queue = _recent_events.get(run_id)
    if queue is None:
        queue = deque(maxlen=_RECENT_EVENT_LIMIT)
        _recent_events[run_id] = queue
    else:
        queue.clear()
    _status_phases.pop(run_id, None)
    snapshot = _get_snapshot(run_id)
    snapshot.setdefault("recent_events", [])
    snapshot.pop("status_phase", None)


def _ensure_event_queue(run_id: str) -> deque[dict[str, Any]]:
    queue = _recent_events.get(run_id)
    if queue is None:
        queue = deque(maxlen=_RECENT_EVENT_LIMIT)
        _recent_events[run_id] = queue
    return queue


def _get_snapshot(run_id: str) -> dict[str, Any]:
    from runs.lifecycle import battle_snapshots

    snap = battle_snapshots.get(run_id)
    if snap is None:
        snap = {"result": "battle"}
        battle_snapshots[run_id] = snap
    return snap


def mutate_snapshot_overlay(
    run_id: str | None,
    *,
    active_id: str | None | object = _MISSING,
    active_target_id: str | None | object = _MISSING,
    status_phase: dict[str, Any] | None | object = _MISSING,
    event: dict[str, Any] | None = None,
) -> None:
    """Mutate the stored battle snapshot for incremental UI feedback."""

    if not run_id:
        return
    snapshot = _get_snapshot(run_id)
    if active_id is not _MISSING:
        snapshot["active_id"] = active_id
    if active_target_id is not _MISSING:
        snapshot["active_target_id"] = active_target_id
    if status_phase is not _MISSING:
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


def _status_payload(
    phase: str,
    stats: Stats,
    payload: dict[str, Any],
    state: str,
) -> dict[str, Any]:
    data = dict(payload)
    data["phase"] = phase
    data["state"] = state
    data.setdefault("target_id", getattr(stats, "id", None))
    return data


def _resolve_damage_type_id(entity: Stats | None) -> str | None:
    damage_type = getattr(entity, "damage_type", None)
    ident = getattr(damage_type, "id", None)
    if ident is None:
        return None
    try:
        return str(ident)
    except Exception:
        return None


def _normalize_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    def _convert(value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, dict):
            converted = {
                key: _convert(sub_value) for key, sub_value in value.items()
            }
            return {key: val for key, val in converted.items() if val is not None}
        if isinstance(value, (list, tuple, set)):
            converted_list = [
                item for item in (_convert(member) for member in value) if item is not None
            ]
            return converted_list or None
        return value

    normalized = {key: _convert(val) for key, val in (metadata or {}).items()}
    return {key: val for key, val in normalized.items() if val is not None}


def _record_event(
    run_id: str,
    *,
    event_type: str,
    source: Stats | None,
    target: Stats | None,
    amount: int | None,
    metadata: dict[str, Any] | None = None,
) -> None:
    event_payload: dict[str, Any] = {
        "type": event_type,
        "source_id": getattr(source, "id", None),
        "target_id": getattr(target, "id", None),
    }
    if amount is not None:
        event_payload["amount"] = int(amount)
    if metadata:
        normalized = _normalize_metadata(metadata)
        if normalized:
            event_payload["metadata"] = normalized
    mutate_snapshot_overlay(run_id, event=event_payload)


def _on_status_phase_start(phase: str, stats: Stats, payload: dict[str, Any]) -> None:
    run_id = _resolve_run_id(stats)
    if not run_id:
        return
    mutate_snapshot_overlay(
        run_id,
        status_phase=_status_payload(phase, stats, payload, state="start"),
    )


def _on_status_phase_end(phase: str, stats: Stats, payload: dict[str, Any]) -> None:
    run_id = _resolve_run_id(stats)
    if not run_id:
        return
    mutate_snapshot_overlay(
        run_id,
        status_phase=_status_payload(phase, stats, payload, state="end"),
    )


def _on_hit_landed(
    attacker: Stats | None,
    target: Stats | None,
    amount: int | None = None,
    event_kind: str | None = None,
    identifier: str | None = None,
    *_: Any,
) -> None:
    run_id = _resolve_run_id(attacker, target)
    if not run_id:
        return
    metadata = {"event_kind": event_kind, "identifier": identifier}
    _record_event(
        run_id,
        event_type="hit_landed",
        source=attacker,
        target=target,
        amount=amount,
        metadata={k: v for k, v in metadata.items() if v is not None},
    )
    if attacker is not None or target is not None:
        mutate_snapshot_overlay(
            run_id,
            active_id=getattr(attacker, "id", None) if attacker else _MISSING,
            active_target_id=getattr(target, "id", None) if target else _MISSING,
        )


def _on_damage_taken(
    target: Stats | None,
    attacker: Stats | None = None,
    amount: int | None = None,
    *_: Any,
) -> None:
    run_id = _resolve_run_id(target, attacker)
    if not run_id:
        return
    metadata: dict[str, Any] | None = None
    damage_type_id = _resolve_damage_type_id(attacker)
    if damage_type_id:
        metadata = {"damage_type_id": damage_type_id}
    _record_event(
        run_id,
        event_type="damage_taken",
        source=attacker,
        target=target,
        amount=amount,
        metadata=metadata,
    )
    kwargs: dict[str, Any] = {}
    if attacker is not None:
        kwargs["active_id"] = getattr(attacker, "id", None)
    if target is not None:
        kwargs["active_target_id"] = getattr(target, "id", None)
    if kwargs:
        mutate_snapshot_overlay(run_id, **kwargs)


def _on_heal_received(
    target: Stats | None,
    healer: Stats | None = None,
    amount: int | None = None,
    *_: Any,
) -> None:
    run_id = _resolve_run_id(target, healer)
    if not run_id:
        return
    metadata: dict[str, Any] | None = None
    damage_type_id = _resolve_damage_type_id(healer)
    if damage_type_id:
        metadata = {"damage_type_id": damage_type_id}
    _record_event(
        run_id,
        event_type="heal_received",
        source=healer,
        target=target,
        amount=amount,
        metadata=metadata,
    )
    kwargs: dict[str, Any] = {}
    if healer is not None:
        kwargs["active_id"] = getattr(healer, "id", None)
    if target is not None:
        kwargs["active_target_id"] = getattr(target, "id", None)
    if kwargs:
        mutate_snapshot_overlay(run_id, **kwargs)


async def _on_target_acquired(
    attacker: Stats | None,
    target: Stats | None,
    *_: Any,
) -> None:
    run_id = _resolve_run_id(attacker, target)
    if not run_id:
        return
    metadata: dict[str, Any] | None = None
    damage_type_id = _resolve_damage_type_id(attacker)
    if damage_type_id:
        metadata = {"damage_type_id": damage_type_id}
    _record_event(
        run_id,
        event_type="target_acquired",
        source=attacker,
        target=target,
        amount=None,
        metadata=metadata,
    )


async def _on_dot_tick(
    attacker: Stats | None,
    target: Stats | None,
    amount: int | None = None,
    effect_name: str | None = None,
    effect_details: dict[str, Any] | None = None,
    *_: Any,
) -> None:
    run_id = _resolve_run_id(attacker, target)
    if not run_id:
        return
    effect_id = None
    remaining_turns = None
    original_amount = None
    if isinstance(effect_details, dict):
        effect_id = effect_details.get("dot_id") or effect_details.get("id")
        remaining_turns = effect_details.get("remaining_turns")
        original_amount = effect_details.get("original_damage")
    metadata: dict[str, Any] = {
        "damage_type_id": _resolve_damage_type_id(attacker),
        "effect_ids": [effect_id] if effect_id else None,
        "remaining_turns": remaining_turns,
        "effects": [
            {
                "id": effect_id,
                "name": effect_name,
                "remaining_turns": remaining_turns,
                "original_amount": original_amount,
                "type": "dot",
            }
        ],
    }
    _record_event(
        run_id,
        event_type="dot_tick",
        source=attacker,
        target=target,
        amount=amount,
        metadata=metadata,
    )


async def _on_hot_tick(
    healer: Stats | None,
    target: Stats | None,
    amount: int | None = None,
    effect_name: str | None = None,
    effect_details: dict[str, Any] | None = None,
    *_: Any,
) -> None:
    run_id = _resolve_run_id(target, healer)
    if not run_id:
        return
    effect_id = None
    remaining_turns = None
    original_amount = None
    if isinstance(effect_details, dict):
        effect_id = effect_details.get("hot_id") or effect_details.get("id")
        remaining_turns = effect_details.get("remaining_turns")
        original_amount = effect_details.get("original_healing")
    metadata: dict[str, Any] = {
        "damage_type_id": _resolve_damage_type_id(healer),
        "effect_ids": [effect_id] if effect_id else None,
        "remaining_turns": remaining_turns,
        "effects": [
            {
                "id": effect_id,
                "name": effect_name,
                "remaining_turns": remaining_turns,
                "original_amount": original_amount,
                "type": "hot",
            }
        ],
    }
    _record_event(
        run_id,
        event_type="hot_tick",
        source=healer,
        target=target,
        amount=amount,
        metadata=metadata,
    )


BUS.subscribe("status_phase_start", _on_status_phase_start)
BUS.subscribe("status_phase_end", _on_status_phase_end)
BUS.subscribe("hit_landed", _on_hit_landed)
BUS.subscribe("damage_taken", _on_damage_taken)
BUS.subscribe("heal_received", _on_heal_received)
BUS.subscribe("target_acquired", _on_target_acquired)
BUS.subscribe("dot_tick", _on_dot_tick)
BUS.subscribe("hot_tick", _on_hot_tick)


@dataclass(slots=True)
class EnrageState:
    """Track enrage progression for a battle."""

    threshold: int
    active: bool = False
    stacks: int = 0
    bleed_applies: int = 0

    def as_payload(self) -> dict[str, Any]:
        """Return a JSON-serializable snapshot of the current enrage state."""

        return {
            "active": self.active,
            "stacks": self.stacks,
            "turns": self.stacks,
        }


async def collect_summon_snapshots(
    entities: Iterable[Stats],
) -> dict[str, list[dict[str, Any]]]:
    """Serialize active summons for the provided combatants."""

    def _collect() -> dict[str, list[dict[str, Any]]]:
        snapshots: dict[str, list[dict[str, Any]]] = {}
        for ent in entities:
            if isinstance(ent, Summon):
                continue
            sid = getattr(ent, "id", str(id(ent)))
            for summon in SummonManager.get_summons(sid):
                snap = _serialize(summon)
                snap["owner_id"] = sid
                snapshots.setdefault(sid, []).append(snap)
        return snapshots

    return await asyncio.to_thread(_collect)


async def build_action_queue_snapshot(
    party_members: Sequence[Stats],
    foes: Sequence[Stats],
    extra_turns: MutableMapping[int, int],
) -> list[dict[str, Any]]:
    """Capture the current visual action queue ordering."""

    def _build() -> list[dict[str, Any]]:
        ordered = sorted(
            list(party_members) + list(foes),
            key=lambda c: getattr(c, "action_value", 0.0),
        )
        extras: list[dict[str, Any]] = []
        for ent in ordered:
            turns = extra_turns.get(id(ent), 0)
            for _ in range(turns):
                extras.append(
                    {
                        "id": getattr(ent, "id", ""),
                        "action_gauge": getattr(ent, "action_gauge", 0),
                        "action_value": getattr(ent, "action_value", 0.0),
                        "base_action_value": getattr(ent, "base_action_value", 0.0),
                        "bonus": True,
                    }
                )
        base_entries = [
            {
                "id": getattr(c, "id", ""),
                "action_gauge": getattr(c, "action_gauge", 0),
                "action_value": getattr(c, "action_value", 0.0),
                "base_action_value": getattr(c, "base_action_value", 0.0),
            }
            for c in ordered
        ]
        return extras + base_entries

    return await asyncio.to_thread(_build)


async def build_battle_progress_payload(
    party_members: Sequence[Stats],
    foes: Sequence[Stats],
    enrage_state: EnrageState,
    rdr: float,
    extra_turns: MutableMapping[int, int],
    *,
    run_id: str | None,
    active_id: str | None,
    active_target_id: str | None,
    include_summon_foes: bool = False,
    ended: bool | None = None,
) -> dict[str, Any]:
    """Assemble the payload dispatched to progress callbacks."""

    party_data = await asyncio.to_thread(
        lambda: [
            _serialize(member)
            for member in party_members
            if not isinstance(member, Summon)
        ]
    )

    def _serialize_foes() -> list[dict[str, Any]]:
        serialized: list[dict[str, Any]] = []
        for foe in foes:
            if not include_summon_foes and isinstance(foe, Summon):
                continue
            serialized.append(_serialize(foe))
        return serialized

    foes_data = await asyncio.to_thread(_serialize_foes)
    party_summons, foe_summons = await asyncio.gather(
        collect_summon_snapshots(party_members),
        collect_summon_snapshots(foes),
    )
    action_queue = await build_action_queue_snapshot(
        party_members,
        foes,
        extra_turns,
    )
    payload: dict[str, Any] = {
        "result": "battle",
        "party": party_data,
        "foes": foes_data,
        "party_summons": party_summons,
        "foe_summons": foe_summons,
        "enrage": enrage_state.as_payload(),
        "rdr": rdr,
        "action_queue": action_queue,
        "active_id": active_id,
        "active_target_id": active_target_id,
    }
    if run_id:
        if run_id in _recent_events:
            payload["recent_events"] = list(_recent_events[run_id])
        if run_id in _status_phases:
            payload["status_phase"] = _status_phases[run_id]
    if ended is not None:
        payload["ended"] = ended
    return payload


async def push_progress_update(
    progress: Callable[[dict[str, Any]], Awaitable[None]] | None,
    party_members: Sequence[Stats],
    foes: Sequence[Stats],
    enrage_state: EnrageState,
    rdr: float,
    extra_turns: MutableMapping[int, int],
    *,
    run_id: str | None,
    active_id: str | None,
    active_target_id: str | None = None,
    include_summon_foes: bool = False,
    ended: bool | None = None,
) -> None:
    """Send a progress update if a callback is available."""

    if progress is None:
        return
    payload = await build_battle_progress_payload(
        party_members,
        foes,
        enrage_state,
        rdr,
        extra_turns,
        run_id=run_id,
        active_id=active_id,
        active_target_id=active_target_id,
        include_summon_foes=include_summon_foes,
        ended=ended,
    )
    await progress(payload)


async def _advance_visual_queue(
    visual_queue: Any,
    actor: Stats | None,
) -> None:
    if visual_queue is None or actor is None:
        return
    try:
        await asyncio.to_thread(visual_queue.advance_with_actor, actor)
    except Exception:
        log.debug("Failed to advance visual queue", exc_info=True)


async def dispatch_turn_end_snapshot(
    visual_queue: Any,
    progress: Callable[[dict[str, Any]], Awaitable[None]] | None,
    party_members: Sequence[Stats],
    foes: Sequence[Stats],
    enrage_state: EnrageState,
    rdr: float,
    extra_turns: MutableMapping[int, int],
    actor: Stats,
    run_id: str | None,
) -> None:
    """Advance the visual queue and emit an updated snapshot."""

    await _advance_visual_queue(visual_queue, actor)
    await push_progress_update(
        progress,
        party_members,
        foes,
        enrage_state,
        rdr,
        extra_turns,
        run_id=run_id,
        active_id=getattr(actor, "id", None),
        active_target_id=None,
    )


async def update_enrage_state(
    turn: int,
    state: EnrageState,
    foes: Sequence[Stats],
    foe_effects: Sequence["EffectManager"],
    enrage_mods: list[Any],
    party_members: Sequence[Stats],
) -> None:
    """Update enrage modifiers and catastrophic damage thresholds."""

    if turn > state.threshold:
        if not state.active:
            state.active = True
            for foe in foes:
                try:
                    foe.passives.append("Enraged")
                except Exception:
                    pass
            log.info("Enrage activated")
        new_stacks = turn - state.threshold
        await asyncio.to_thread(set_enrage_percent, 1.35 * max(new_stacks, 0))
        mult = 1 + 2.0 * new_stacks
        for idx, (foe_obj, mgr) in enumerate(zip(foes, foe_effects, strict=False)):
            existing = enrage_mods[idx]
            if existing is not None:
                existing.remove()
                try:
                    mgr.mods.remove(existing)
                    if existing.id in foe_obj.mods:
                        foe_obj.mods.remove(existing.id)
                except ValueError:
                    pass
            mod = create_stat_buff(
                foe_obj,
                name="enrage_atk",
                atk_mult=mult,
                turns=9999,
            )
            mgr.add_modifier(mod)
            enrage_mods[idx] = mod
        state.stacks = new_stacks
        if turn > 1000:
            extra_damage = 100 * max(state.stacks, 0)
            if extra_damage > 0:
                for member in party_members:
                    if getattr(member, "hp", 0) > 0:
                        await member.apply_damage(extra_damage)
                for foe_obj in foes:
                    if getattr(foe_obj, "hp", 0) > 0:
                        await foe_obj.apply_damage(extra_damage)
    else:
        await asyncio.to_thread(set_enrage_percent, 0.0)


async def apply_enrage_bleed(
    state: EnrageState,
    party_members: Sequence[Stats],
    foes: Sequence[Stats],
    foe_effects: Sequence["EffectManager"],
) -> None:
    """Apply stacking bleed to both sides while enrage remains active."""

    if not state.active:
        return
    turns_since_enrage = max(state.stacks, 0)
    next_trigger = (state.bleed_applies + 1) * 10
    if turns_since_enrage < next_trigger:
        return
    stacks_to_add = 1 + state.bleed_applies
    from autofighter.effects import DamageOverTime

    for member in party_members:
        mgr = member.effect_manager
        for _ in range(stacks_to_add):
            dmg_per_tick = int(max(getattr(mgr.stats, "max_hp", 1), 1) * 0.5)
            mgr.add_dot(
                DamageOverTime("Enrage Bleed", dmg_per_tick, 10, "enrage_bleed")
            )
    for mgr, foe_obj in zip(foe_effects, foes, strict=False):
        for _ in range(stacks_to_add):
            dmg_per_tick = int(max(getattr(foe_obj, "max_hp", 1), 1) * 0.25)
            mgr.add_dot(
                DamageOverTime("Enrage Bleed", dmg_per_tick, 10, "enrage_bleed")
            )
    state.bleed_applies += 1
