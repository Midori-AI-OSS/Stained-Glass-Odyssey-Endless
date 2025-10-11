"""Enrage helpers for battle rooms."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
from types import ModuleType
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from typing import MutableSequence
from typing import Sequence

ENRAGE_TURNS_NORMAL = 100
ENRAGE_TURNS_BOSS = 500

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from autofighter.effects import EffectManager

    from ...stats import Stats
    from .. import Room


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


def _resolve_overrides(
    rooms_module: ModuleType,
    default_normal: int,
    default_boss: int,
) -> tuple[int, int]:
    """Extract enrage overrides from the rooms module."""

    normal = getattr(rooms_module, "ENRAGE_TURNS_NORMAL", default_normal)
    boss = getattr(rooms_module, "ENRAGE_TURNS_BOSS", default_boss)
    return normal, boss


async def compute_enrage_threshold(room: Room) -> int:
    """Compute the enrage threshold for the given room."""

    base_normal = ENRAGE_TURNS_NORMAL
    base_boss = ENRAGE_TURNS_BOSS

    try:
        from autofighter import rooms as rooms_module
    except Exception:  # pragma: no cover - defensive against dynamic loaders
        rooms_module = None

    if rooms_module is not None:
        base_normal, base_boss = await asyncio.to_thread(
            _resolve_overrides,
            rooms_module,
            base_normal,
            base_boss,
        )

    boss_type = None
    if rooms_module is not None:
        boss_type = getattr(rooms_module, "BossRoom", None)

    if boss_type is None:
        from ..boss import BossRoom  # imported lazily to avoid circular imports

        boss_type = BossRoom

    return base_boss if isinstance(room, boss_type) else base_normal


async def update_enrage_state(
    turn: int,
    state: EnrageState,
    foes: Sequence[Stats],
    foe_effects: Sequence["EffectManager"],
    enrage_mods: MutableSequence[Any],
    party_members: Sequence[Stats],
    *,
    set_enrage_percent: Callable[[float], Any],
    create_stat_buff: Callable[..., Any],
    catastrophic_turn_threshold: int = 1000,
    catastrophic_damage: int = 100,
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
            await asyncio.to_thread(mgr.add_modifier, mod)
            enrage_mods[idx] = mod
        state.stacks = new_stacks
        if turn > catastrophic_turn_threshold:
            extra_damage = catastrophic_damage * max(state.stacks, 0)
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
    *,
    damage_over_time_factory: Callable[[str, int, int, str], Any],
    party_bleed_ratio: float = 0.5,
    foe_bleed_ratio: float = 0.25,
) -> None:
    """Apply stacking bleed to both sides while enrage remains active."""

    if not state.active:
        return
    turns_since_enrage = max(state.stacks, 0)
    next_trigger = (state.bleed_applies + 1) * 10
    if turns_since_enrage < next_trigger:
        return
    stacks_to_add = 1 + state.bleed_applies

    for member in party_members:
        mgr = member.effect_manager
        max_hp = max(getattr(mgr.stats, "max_hp", 1), 1)
        for _ in range(stacks_to_add):
            dmg_per_tick = int(max_hp * party_bleed_ratio)
            await asyncio.to_thread(
                mgr.add_dot,
                damage_over_time_factory(
                    "Enrage Bleed",
                    dmg_per_tick,
                    10,
                    "enrage_bleed",
                ),
            )
    for mgr, foe_obj in zip(foe_effects, foes, strict=False):
        max_hp = max(getattr(foe_obj, "max_hp", 1), 1)
        for _ in range(stacks_to_add):
            dmg_per_tick = int(max_hp * foe_bleed_ratio)
            await asyncio.to_thread(
                mgr.add_dot,
                damage_over_time_factory(
                    "Enrage Bleed",
                    dmg_per_tick,
                    10,
                    "enrage_bleed",
                ),
            )
    state.bleed_applies += 1


__all__ = [
    "ENRAGE_TURNS_NORMAL",
    "ENRAGE_TURNS_BOSS",
    "EnrageState",
    "apply_enrage_bleed",
    "compute_enrage_threshold",
    "update_enrage_state",
]
