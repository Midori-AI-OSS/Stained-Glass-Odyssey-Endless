"""Helpers for assembling battle progress payloads."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from typing import Any
from typing import Iterable
from typing import MutableMapping
from typing import NotRequired
from typing import Protocol
from typing import Sequence
from typing import TypedDict

from autofighter.action_queue import TURN_COUNTER_ID
from autofighter.summons.base import Summon
from autofighter.summons.manager import SummonManager

from ...stats import Stats
from ..utils import _serialize
from . import snapshots as _snapshots

if TYPE_CHECKING:
    from autofighter.action_queue import ActionQueue


class SupportsEnrageSnapshot(Protocol):
    """Protocol describing the enrage payload interface."""

    def as_payload(self) -> dict[str, Any]:
        """Return a JSON serialisable enrage snapshot."""


class ActionQueueEntry(TypedDict, total=False):
    """Representation of a combatant in the visual action queue."""

    id: str
    action_gauge: int
    action_value: float
    base_action_value: float
    bonus: NotRequired[bool]


BattleEntityPayload = dict[str, Any]
SummonSnapshotMap = dict[str, list[BattleEntityPayload]]


class BattleProgressPayload(TypedDict, total=False):
    """Payload broadcast to battle progress subscribers."""

    result: str
    turn: int
    turn_phase: str
    party: list[BattleEntityPayload]
    foes: list[BattleEntityPayload]
    party_summons: SummonSnapshotMap
    foe_summons: SummonSnapshotMap
    enrage: dict[str, Any]
    rdr: float
    action_queue: list[ActionQueueEntry]
    active_id: str | None
    active_target_id: str | None
    recent_events: list[dict[str, Any]]
    status_phase: dict[str, Any]
    ended: bool


async def collect_summon_snapshots(entities: Iterable[Stats]) -> SummonSnapshotMap:
    """Serialize active summons for the provided combatants."""

    def _collect() -> SummonSnapshotMap:
        snapshots: SummonSnapshotMap = {}
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
    *,
    visual_queue: "ActionQueue" | None = None,
) -> list[ActionQueueEntry]:
    """Capture the current visual action queue ordering."""

    def _build() -> list[ActionQueueEntry]:
        combined_entities = list(party_members) + list(foes)

        def _sort_key(combatant: Stats) -> tuple[float, float, str]:
            try:
                value = float(getattr(combatant, "action_value", 0.0))
            except Exception:
                value = 0.0
            if value < 0.0:
                value = 0.0

            try:
                offset = float(getattr(combatant, "_action_sort_offset"))
            except Exception:
                try:
                    offset = float(combined_entities.index(combatant))
                except ValueError:
                    offset = 0.0

            identifier = getattr(combatant, "id", "")
            return (value, offset, identifier)

        def _entry_from_snapshot(raw: MutableMapping[str, Any]) -> ActionQueueEntry:
            identifier = str(raw.get("id", ""))

            try:
                action_value = float(raw.get("action_value", 0.0) or 0.0)
            except Exception:
                action_value = 0.0
            if action_value < 0.0:
                action_value = 0.0

            try:
                base_value = float(
                    raw.get("base_action_value", raw.get("action_value", 0.0) or 0.0)
                )
            except Exception:
                base_value = action_value
            if base_value < 0.0:
                base_value = 0.0

            entry: ActionQueueEntry = {
                "id": identifier,
                "action_gauge": raw.get("action_gauge", 0),
                "action_value": action_value,
                "base_action_value": base_value,
            }
            if raw.get("bonus"):
                entry["bonus"] = True
            return entry

        def _entry_from_combatant(combatant: Stats) -> ActionQueueEntry:
            try:
                action_value = float(getattr(combatant, "action_value", 0.0))
            except Exception:
                action_value = 0.0
            if action_value < 0.0:
                action_value = 0.0

            try:
                base_value = float(
                    getattr(
                        combatant,
                        "base_action_value",
                        getattr(combatant, "action_value", 0.0),
                    )
                )
            except Exception:
                base_value = action_value
            if base_value < 0.0:
                base_value = 0.0

            return {
                "id": getattr(combatant, "id", ""),
                "action_gauge": getattr(combatant, "action_gauge", 0),
                "action_value": action_value,
                "base_action_value": base_value,
            }

        visible_entities = [
            entity for entity in combined_entities if not getattr(entity, "despawned", False)
        ]

        if visual_queue is not None:
            try:
                queue_snapshot = list(getattr(visual_queue, "snapshot", lambda: [])())
            except Exception:
                queue_snapshot = []

            if queue_snapshot:
                visible_by_id: dict[str, Stats] = {}
                for entity in visible_entities:
                    identifier = getattr(entity, "id", None)
                    if identifier:
                        visible_by_id.setdefault(str(identifier), entity)

                entries: list[ActionQueueEntry] = []
                for raw in queue_snapshot:
                    identifier = str(raw.get("id", ""))
                    if not identifier:
                        continue
                    if identifier != TURN_COUNTER_ID:
                        entity = visible_by_id.get(identifier)
                        if entity is None:
                            continue
                        if getattr(entity, "despawned", False):
                            continue
                    entries.append(_entry_from_snapshot(raw))

                if entries:
                    return entries

        ordered = sorted(visible_entities, key=_sort_key)
        extras: list[ActionQueueEntry] = []
        for ent in ordered:
            if getattr(ent, "id", None) == TURN_COUNTER_ID:
                continue
            turns = max(int(extra_turns.get(id(ent), 0)), 0)
            for _ in range(turns):
                entry = _entry_from_combatant(ent)
                entry["bonus"] = True
                extras.append(entry)

        base_entries: list[ActionQueueEntry] = [
            _entry_from_combatant(combatant) for combatant in ordered
        ]
        return extras + base_entries

    return await asyncio.to_thread(_build)


async def build_battle_progress_payload(
    party_members: Sequence[Stats],
    foes: Sequence[Stats],
    enrage_state: SupportsEnrageSnapshot,
    rdr: float,
    extra_turns: MutableMapping[int, int],
    turn: int,
    *,
    run_id: str | None,
    active_id: str | None,
    active_target_id: str | None,
    include_summon_foes: bool = False,
    visual_queue: "ActionQueue" | None = None,
    ended: bool | None = None,
    turn_phase: str | None = None,
) -> BattleProgressPayload:
    """Assemble the payload dispatched to progress callbacks."""

    party_data = await asyncio.to_thread(
        lambda: [
            _serialize(member)
            for member in party_members
            if not isinstance(member, Summon)
        ]
    )

    def _serialize_foes() -> list[BattleEntityPayload]:
        serialized: list[BattleEntityPayload] = []
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
        visual_queue=visual_queue,
    )

    payload: BattleProgressPayload = {
        "result": "battle",
        "turn": int(turn),
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

    if turn_phase is not None:
        payload["turn_phase"] = turn_phase

    if run_id:
        events = _snapshots.get_recent_events(run_id)
        if events is not None:
            payload["recent_events"] = events
        status_phase = _snapshots.get_status_phase(run_id)
        if status_phase is not None:
            payload["status_phase"] = status_phase
        charges = _snapshots.get_effect_charges(run_id)
        if charges is not None:
            payload["effects_charge"] = charges

    if ended is not None:
        payload["ended"] = ended

    return payload
