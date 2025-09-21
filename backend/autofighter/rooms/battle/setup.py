"""Battle setup helpers for :mod:`autofighter.rooms.battle`."""
from __future__ import annotations

import asyncio
import copy
from dataclasses import dataclass
from typing import Sequence

from battle_logging.writers import BattleLogger
from battle_logging.writers import start_battle_logging

from autofighter.action_queue import ActionQueue
from autofighter.cards import apply_cards
from autofighter.effects import EffectManager
from autofighter.effects import StatModifier
from autofighter.mapgen import MapNode
from autofighter.party import Party
from autofighter.passives import PassiveRegistry
from autofighter.relics import apply_relics
from autofighter.stats import Stats
from autofighter.summons.manager import SummonManager

from ..utils import _build_foes
from ..utils import _scale_stats
from .pacing import set_visual_queue


@dataclass(slots=True)
class BattleSetupResult:
    """Container for data produced during battle setup."""

    registry: PassiveRegistry
    combat_party: Party
    foes: list[Stats]
    foe_effects: list[EffectManager]
    enrage_mods: list[StatModifier | None]
    visual_queue: ActionQueue | None
    battle_logger: BattleLogger | None


async def _clone_members(members: Sequence[Stats]) -> list[Stats]:
    """Create deep copies of party members for combat."""

    def _copy_members() -> list[Stats]:
        return [copy.deepcopy(member) for member in members]

    return await asyncio.to_thread(_copy_members)


async def _apply_relics_async(party: Party) -> None:
    """Asynchronously apply relic effects to a party."""

    # `apply_relics` now awaits each relic's async setup directly. Running it on
    # the main loop ensures follow-up emissions (e.g. healing notifications)
    # execute without being cancelled by temporary event loops.
    await apply_relics(party)


async def setup_battle(
    node: MapNode,
    party: Party,
    *,
    foe: Stats | list[Stats] | None = None,
    strength: float = 1.0,
) -> BattleSetupResult:
    """Prepare combatants and battle state before a fight begins."""

    registry = PassiveRegistry()
    SummonManager.reset_all()

    if foe is None:
        foes = _build_foes(node, party)
    else:
        foes = foe if isinstance(foe, list) else [foe]

    for stats in foes:
        _scale_stats(stats, node, strength)
        rank = getattr(stats, "rank", "")
        if isinstance(rank, str) and "boss" in rank.lower():
            boss_scaling = getattr(stats, "apply_boss_scaling", None)
            if callable(boss_scaling):
                boss_scaling()
        prepare = getattr(stats, "prepare_for_battle", None)
        if callable(prepare):
            prepare(node, registry)

    members = await _clone_members(party.members)
    combat_party = Party(
        members=members,
        gold=party.gold,
        relics=party.relics,
        cards=party.cards,
        rdr=party.rdr,
    )

    await apply_cards(combat_party)
    await _apply_relics_async(combat_party)
    party.rdr = combat_party.rdr

    foe_effects: list[EffectManager] = []
    for stats in foes:
        manager = EffectManager(stats)
        stats.effect_manager = manager
        foe_effects.append(manager)

    enrage_mods: list[StatModifier | None] = [None for _ in foes]

    try:
        from autofighter.stats import set_battle_active

        set_battle_active(True)
    except Exception:
        pass

    for member in combat_party.members:
        manager = EffectManager(member)
        member.effect_manager = manager
        prepare = getattr(member, "prepare_for_battle", None)
        if callable(prepare):
            prepare(node, registry)

    try:
        entities = list(combat_party.members) + list(foes)
        visual_queue: ActionQueue | None = ActionQueue(entities)
    except Exception:
        visual_queue = None

    set_visual_queue(visual_queue)

    battle_logger = start_battle_logging()
    try:
        if battle_logger is not None:
            battle_logger.summary.party_members = [m.id for m in combat_party.members]
            battle_logger.summary.foes = [f.id for f in foes]
            relic_counts: dict[str, int] = {}
            for relic_id in combat_party.relics:
                relic_counts[relic_id] = relic_counts.get(relic_id, 0) + 1
            battle_logger.summary.party_relics = relic_counts
    except Exception:
        pass

    return BattleSetupResult(
        registry=registry,
        combat_party=combat_party,
        foes=foes,
        foe_effects=foe_effects,
        enrage_mods=enrage_mods,
        visual_queue=visual_queue,
        battle_logger=battle_logger,
    )
