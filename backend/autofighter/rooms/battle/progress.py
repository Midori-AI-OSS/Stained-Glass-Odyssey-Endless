"""Helpers for assembling battle progress payloads."""

from __future__ import annotations

import asyncio
from typing import Any
from typing import Iterable
from typing import MutableMapping
from typing import NotRequired
from typing import Protocol
from typing import Sequence
from typing import TypedDict

from autofighter.summons.base import Summon
from autofighter.summons.manager import SummonManager

from ...stats import Stats
from ..utils import _serialize
from . import snapshots as _snapshots


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
) -> list[ActionQueueEntry]:
    """Capture the current visual action queue ordering."""

    def _build() -> list[ActionQueueEntry]:
        ordered = sorted(
            list(party_members) + list(foes),
            key=lambda combatant: getattr(combatant, "action_value", 0.0),
        )
        extras: list[ActionQueueEntry] = []
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
        base_entries: list[ActionQueueEntry] = [
            {
                "id": getattr(combatant, "id", ""),
                "action_gauge": getattr(combatant, "action_gauge", 0),
                "action_value": getattr(combatant, "action_value", 0.0),
                "base_action_value": getattr(combatant, "base_action_value", 0.0),
            }
            for combatant in ordered
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
    ended: bool | None = None,
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
