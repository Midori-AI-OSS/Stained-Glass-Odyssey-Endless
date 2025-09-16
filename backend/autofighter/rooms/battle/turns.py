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

from autofighter.effects import create_stat_buff
from autofighter.summons.base import Summon
from autofighter.summons.manager import SummonManager

from ...stats import Stats
from ...stats import set_enrage_percent
from ..utils import _serialize

if TYPE_CHECKING:
    from autofighter.effects import EffectManager

log = logging.getLogger(__name__)


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
    active_id: str | None,
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
    }
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
    active_id: str | None,
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
        active_id=active_id,
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
        active_id=getattr(actor, "id", None),
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
