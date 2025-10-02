from __future__ import annotations

from collections.abc import Iterable
from typing import Any
from typing import Callable
from typing import Optional

from autofighter.cards import _registry as _card_registry
from autofighter.relics import _registry as _relic_registry
from autofighter.stats import BUS

from ...stats import Stats
from . import snapshots as _snapshots
from .pacing import YIELD_MULTIPLIER
from .pacing import pace_sleep

mutate_snapshot_overlay = _snapshots.mutate_snapshot_overlay

__all__ = [
    "handle_battle_start",
    "handle_battle_end",
    "register_event_handlers",
]

_CARD_NAME_CACHE: dict[str, Optional[str]] = {}
_RELIC_NAME_CACHE: dict[str, Optional[str]] = {}
_REGISTERED = False


async def handle_battle_start(
    foes: Iterable[Any],
    party_members: Iterable[Any],
    registry: Any,
) -> None:
    """Emit battle start events for all combatants."""

    foes = tuple(foes)
    members = tuple(party_members)

    for foe_obj in foes:
        await BUS.emit_async("battle_start", foe_obj)
        await registry.trigger(
            "battle_start",
            foe_obj,
            party=members,
            foes=foes,
        )

    for member in members:
        await BUS.emit_async("battle_start", member)
        await registry.trigger(
            "battle_start",
            member,
            party=members,
            foes=foes,
        )


async def handle_battle_end(
    foes: Iterable[Any],
    party_members: Iterable[Any],
) -> None:
    """Emit defeat and battle end events for combatants."""

    foes = tuple(foes)
    members = tuple(party_members)

    try:
        for foe_obj in foes:
            if getattr(foe_obj, "hp", 1) <= 0:
                await BUS.emit_async("entity_defeat", foe_obj)
        for member in members:
            if getattr(member, "hp", 1) <= 0:
                await BUS.emit_async("entity_defeat", member)
    except Exception:
        pass

    try:
        for foe_obj in foes:
            await BUS.emit_async("battle_end", foe_obj)
    except Exception:
        pass

    run_id = _resolve_run_id(*members, *foes)
    if run_id:
        _snapshots.clear_effect_charges(run_id)


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


def _normalize_metadata(metadata: dict[str, Any] | None) -> dict[str, Any] | None:
    if not metadata:
        return None

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
                item for item in (_convert(member) for member in value)
                if item is not None
            ]
            return converted_list or None
        return value

    normalized = {key: _convert(val) for key, val in metadata.items()}
    return {key: val for key, val in normalized.items() if val is not None}


def _lookup_card_name(card_id: str | None) -> str | None:
    if not card_id:
        return None
    if card_id in _CARD_NAME_CACHE:
        return _CARD_NAME_CACHE[card_id]
    try:
        registry = _card_registry()
    except Exception:
        _CARD_NAME_CACHE[card_id] = None
        return None
    card_cls = registry.get(card_id)
    if card_cls is None:
        _CARD_NAME_CACHE[card_id] = None
        return None
    try:
        instance = card_cls()
    except Exception:
        friendly = getattr(card_cls, "name", None)
    else:
        friendly = getattr(instance, "name", None)
    friendly_name = friendly if friendly else None
    _CARD_NAME_CACHE[card_id] = friendly_name
    return friendly_name


def _lookup_relic_name(relic_id: str | None) -> str | None:
    if not relic_id:
        return None
    if relic_id in _RELIC_NAME_CACHE:
        return _RELIC_NAME_CACHE[relic_id]
    try:
        registry = _relic_registry()
    except Exception:
        _RELIC_NAME_CACHE[relic_id] = None
        return None
    relic_cls = registry.get(relic_id)
    if relic_cls is None:
        _RELIC_NAME_CACHE[relic_id] = None
        return None
    try:
        instance = relic_cls()
    except Exception:
        friendly = getattr(relic_cls, "name", None)
    else:
        friendly = getattr(instance, "name", None)
    friendly_name = friendly if friendly else None
    _RELIC_NAME_CACHE[relic_id] = friendly_name
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
    attacker: Stats | None = None,
    *_: Any,
) -> None:
    run_id = _resolve_run_id(recipient, attacker)
    if not run_id:
        return
    metadata = {
        "relic_id": relic_id,
        "relic_name": _lookup_relic_name(relic_id),
        "effect": effect_type,
        "details": details,
    }
    target = recipient if isinstance(recipient, Stats) else None
    source = attacker if isinstance(attacker, Stats) else None
    _record_event(
        run_id,
        event_type="relic_effect",
        source=source,
        target=target,
        amount=amount,
        metadata=metadata,
    )
    kwargs: dict[str, Any] = {}
    if source is not None:
        kwargs["active_id"] = getattr(source, "id", None)
    if target is not None:
        kwargs["active_target_id"] = getattr(target, "id", None)
        if "active_id" not in kwargs:
            kwargs["active_id"] = getattr(target, "id", None)
    if kwargs:
        mutate_snapshot_overlay(run_id, **kwargs)
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


def _subscribe(event: str, handler: Callable[..., Any]) -> None:
    BUS.subscribe(event, handler)


def register_event_handlers() -> None:
    global _REGISTERED
    if _REGISTERED:
        return
    _REGISTERED = True

    _subscribe("status_phase_start", _on_status_phase_start)
    _subscribe("status_phase_end", _on_status_phase_end)
    _subscribe("hit_landed", _on_hit_landed)
    _subscribe("damage_taken", _on_damage_taken)
    _subscribe("heal_received", _on_heal_received)
    _subscribe("target_acquired", _on_target_acquired)
    _subscribe("dot_tick", _on_dot_tick)
    _subscribe("hot_tick", _on_hot_tick)
    _subscribe("card_effect", _on_card_effect)
    _subscribe("relic_effect", _on_relic_effect)
    _subscribe("effect_applied", _on_effect_applied)
    _subscribe("effect_resisted", _on_effect_resisted)
    _subscribe("effect_expired", _on_effect_expired)
