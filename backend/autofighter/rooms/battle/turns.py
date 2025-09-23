from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
from typing import TYPE_CHECKING
from typing import Any
from typing import Awaitable
from typing import Callable
from typing import Iterable
from typing import MutableMapping
from typing import Sequence

from autofighter.cards import _registry as _card_registry
from autofighter.effects import create_stat_buff
from autofighter.relics import _registry as _relic_registry
from autofighter.stats import BUS
from autofighter.summons.base import Summon
from autofighter.summons.manager import SummonManager

from ...stats import Stats
from ...stats import set_enrage_percent
from ..utils import _serialize
from . import snapshots as _snapshots
from .pacing import YIELD_MULTIPLIER
from .pacing import pace_sleep

if TYPE_CHECKING:
    from autofighter.effects import EffectManager

log = logging.getLogger(__name__)

register_snapshot_entities = _snapshots.register_snapshot_entities
prepare_snapshot_overlay = _snapshots.prepare_snapshot_overlay
mutate_snapshot_overlay = _snapshots.mutate_snapshot_overlay

_card_name_cache: dict[str, str | None] = {}
_relic_name_cache: dict[str, str | None] = {}


def _resolve_run_id(*entities: Any) -> str | None:
    return _snapshots.resolve_run_id(*entities)


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


def _lookup_card_name(card_id: str | None) -> str | None:
    if not card_id:
        return None
    if card_id in _card_name_cache:
        return _card_name_cache[card_id]
    try:
        registry = _card_registry()
    except Exception:
        _card_name_cache[card_id] = None
        return None
    card_cls = registry.get(card_id)
    if card_cls is None:
        _card_name_cache[card_id] = None
        return None
    try:
        instance = card_cls()
    except Exception:
        friendly = getattr(card_cls, "name", None)
    else:
        friendly = getattr(instance, "name", None)
    friendly_name = friendly if friendly else None
    _card_name_cache[card_id] = friendly_name
    return friendly_name


def _lookup_relic_name(relic_id: str | None) -> str | None:
    if not relic_id:
        return None
    if relic_id in _relic_name_cache:
        return _relic_name_cache[relic_id]
    try:
        registry = _relic_registry()
    except Exception:
        _relic_name_cache[relic_id] = None
        return None
    relic_cls = registry.get(relic_id)
    if relic_cls is None:
        _relic_name_cache[relic_id] = None
        return None
    try:
        instance = relic_cls()
    except Exception:
        friendly = getattr(relic_cls, "name", None)
    else:
        friendly = getattr(instance, "name", None)
    friendly_name = friendly if friendly else None
    _relic_name_cache[relic_id] = friendly_name
    return friendly_name


def _effect_metadata(
    effect_name: str | None,
    details: dict[str, Any] | None,
) -> dict[str, Any] | None:
    metadata: dict[str, Any] = {}
    if isinstance(details, dict):
        metadata.update(details)
    if effect_name:
        metadata.setdefault("effect_name", effect_name)
    return metadata or None


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
        kwargs: dict[str, Any] = {}
        if attacker is not None:
            kwargs["active_id"] = getattr(attacker, "id", None)
        if target is not None:
            kwargs["active_target_id"] = getattr(target, "id", None)
        if kwargs:
            mutate_snapshot_overlay(run_id, **kwargs)


def _on_damage_taken(
    target: Stats | None,
    attacker: Stats | None = None,
    amount: int | None = None,
    pre_damage_hp: int | None = None,
    post_damage_hp: int | None = None,
    is_critical: bool | None = None,
    action_name: str | None = None,
    details: dict[str, Any] | None = None,
    *_: Any,
) -> None:
    run_id = _resolve_run_id(target, attacker)
    if not run_id:
        return
    metadata: dict[str, Any] = dict(details) if isinstance(details, dict) else {}
    damage_type_id = _resolve_damage_type_id(attacker)
    if damage_type_id and "damage_type_id" not in metadata:
        metadata["damage_type_id"] = damage_type_id
    if is_critical is not None and "is_critical" not in metadata:
        metadata["is_critical"] = bool(is_critical)
    if action_name and "action_name" not in metadata:
        metadata["action_name"] = str(action_name)
    metadata_payload = metadata or None
    _record_event(
        run_id,
        event_type="damage_taken",
        source=attacker,
        target=target,
        amount=amount,
        metadata=metadata_payload,
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
    source_type: str | None = None,
    source_name: str | None = None,
    *_: Any,
) -> None:
    run_id = _resolve_run_id(target, healer)
    if not run_id:
        return
    metadata: dict[str, Any] = {}
    damage_type_id = _resolve_damage_type_id(healer)
    if damage_type_id:
        metadata["damage_type_id"] = damage_type_id
    if source_type:
        metadata["source_type"] = str(source_type)
    if source_name:
        metadata["source_name"] = str(source_name)
    metadata_payload = metadata or None
    _record_event(
        run_id,
        event_type="heal_received",
        source=healer,
        target=target,
        amount=amount,
        metadata=metadata_payload,
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
    await pace_sleep(YIELD_MULTIPLIER)


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
    await pace_sleep(YIELD_MULTIPLIER)


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
    await pace_sleep(YIELD_MULTIPLIER)


async def _on_card_effect(
    card_id: str | None,
    recipient: Any,
    effect_type: str | None = None,
    amount: int | float | None = None,
    details: dict[str, Any] | None = None,
    *_: Any,
) -> None:
    run_id = _resolve_run_id(recipient)
    if not run_id:
        return
    metadata = {
        "card_id": card_id,
        "card_name": _lookup_card_name(card_id),
        "effect": effect_type,
        "details": details,
    }
    target = recipient if isinstance(recipient, Stats) else None
    _record_event(
        run_id,
        event_type="card_effect",
        source=None,
        target=target,
        amount=amount,
        metadata=metadata,
    )
    if target is not None:
        ident = getattr(target, "id", None)
        mutate_snapshot_overlay(
            run_id,
            active_id=ident,
            active_target_id=ident,
        )
    await pace_sleep(YIELD_MULTIPLIER)


async def _on_relic_effect(
    relic_id: str | None,
    recipient: Any,
    effect_type: str | None = None,
    amount: int | float | None = None,
    details: dict[str, Any] | None = None,
    *_: Any,
) -> None:
    run_id = _resolve_run_id(recipient)
    if not run_id:
        return
    metadata = {
        "relic_id": relic_id,
        "relic_name": _lookup_relic_name(relic_id),
        "effect": effect_type,
        "details": details,
    }
    target = recipient if isinstance(recipient, Stats) else None
    _record_event(
        run_id,
        event_type="relic_effect",
        source=None,
        target=target,
        amount=amount,
        metadata=metadata,
    )
    if target is not None:
        ident = getattr(target, "id", None)
        mutate_snapshot_overlay(
            run_id,
            active_id=ident,
            active_target_id=ident,
        )
    await pace_sleep(YIELD_MULTIPLIER)


def _on_effect_applied(
    effect_name: str | None,
    entity: Stats | None,
    details: dict[str, Any] | None = None,
) -> None:
    run_id = _resolve_run_id(entity)
    if not run_id:
        return
    metadata = _effect_metadata(effect_name, details)
    _record_event(
        run_id,
        event_type="effect_applied",
        source=None,
        target=entity,
        amount=None,
        metadata=metadata,
    )
    if entity is not None:
        mutate_snapshot_overlay(
            run_id,
            active_target_id=getattr(entity, "id", None),
        )


def _on_effect_resisted(
    effect_name: str | None,
    target: Stats | None,
    source: Stats | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    run_id = _resolve_run_id(target, source)
    if not run_id:
        return
    metadata = _effect_metadata(effect_name, details)
    _record_event(
        run_id,
        event_type="effect_resisted",
        source=source,
        target=target,
        amount=None,
        metadata=metadata,
    )
    kwargs: dict[str, Any] = {}
    if source is not None:
        kwargs["active_id"] = getattr(source, "id", None)
    if target is not None:
        kwargs["active_target_id"] = getattr(target, "id", None)
    if kwargs:
        mutate_snapshot_overlay(run_id, **kwargs)


def _on_effect_expired(
    effect_name: str | None,
    entity: Stats | None,
    details: dict[str, Any] | None = None,
) -> None:
    run_id = _resolve_run_id(entity)
    if not run_id:
        return
    metadata = _effect_metadata(effect_name, details)
    _record_event(
        run_id,
        event_type="effect_expired",
        source=None,
        target=entity,
        amount=None,
        metadata=metadata,
    )
    if entity is not None:
        mutate_snapshot_overlay(
            run_id,
            active_target_id=getattr(entity, "id", None),
        )


BUS.subscribe("status_phase_start", _on_status_phase_start)
BUS.subscribe("status_phase_end", _on_status_phase_end)
BUS.subscribe("hit_landed", _on_hit_landed)
BUS.subscribe("damage_taken", _on_damage_taken)
BUS.subscribe("heal_received", _on_heal_received)
BUS.subscribe("target_acquired", _on_target_acquired)
BUS.subscribe("dot_tick", _on_dot_tick)
BUS.subscribe("hot_tick", _on_hot_tick)
BUS.subscribe("card_effect", _on_card_effect)
BUS.subscribe("relic_effect", _on_relic_effect)
BUS.subscribe("effect_applied", _on_effect_applied)
BUS.subscribe("effect_resisted", _on_effect_resisted)
BUS.subscribe("effect_expired", _on_effect_expired)


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
                snap.setdefault(
                    "instance_id",
                    getattr(summon, "instance_id", getattr(summon, "id", None)),
                )
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
        events = _snapshots.get_recent_events(run_id)
        if events is not None:
            payload["recent_events"] = events
        status_phase = _snapshots.get_status_phase(run_id)
        if status_phase is not None:
            payload["status_phase"] = status_phase
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
) -> dict[str, Any] | None:
    """Update enrage modifiers and catastrophic damage thresholds."""

    previous_active = state.active
    previous_stacks = state.stacks

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

    if state.active != previous_active or state.stacks != previous_stacks:
        return state.as_payload()
    return None


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
