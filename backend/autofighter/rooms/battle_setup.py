"""Battle setup and initialization module for preparing combat entities and state."""

from __future__ import annotations

import asyncio
import copy
import logging
from typing import TYPE_CHECKING
from typing import Any

from battle_logging.writers import start_battle_logging

from autofighter.cards import apply_cards
from autofighter.effects import EffectManager
from autofighter.effects import StatModifier
from autofighter.relics import apply_relics
from autofighter.stats import BUS
from autofighter.stats import set_enrage_percent
from autofighter.summons.base import Summon
from autofighter.summons.manager import SummonManager

from ..action_queue import ActionQueue
from ..party import Party
from ..passives import PassiveRegistry
from ..stats import Stats
from .enrage_system import ENRAGE_TURNS_BOSS
from .enrage_system import ENRAGE_TURNS_NORMAL
from .enrage_system import get_extra_turns
from .enrage_system import set_visual_queue
from .utils import _serialize

if TYPE_CHECKING:
    from . import Room

log = logging.getLogger(__name__)


async def setup_combat_party(party: Party) -> Party:
    """
    Create a combat-ready copy of the party with applied cards and relics.

    Args:
        party: The original party to copy

    Returns:
        Combat-ready party copy
    """
    members = list(
        await asyncio.gather(
            *(asyncio.to_thread(copy.deepcopy, m) for m in party.members)
        )
    )
    combat_party = Party(
        members=members,
        gold=party.gold,
        relics=party.relics,
        cards=party.cards,
        rdr=party.rdr,
    )
    await apply_cards(combat_party)
    await asyncio.to_thread(apply_relics, combat_party)
    return combat_party


def setup_effect_managers(
    combat_party: Party, foes: list[Stats]
) -> tuple[list[EffectManager], list[StatModifier | None]]:
    """
    Setup effect managers for all combat entities.

    Args:
        combat_party: The combat party
        foes: List of foe entities

    Returns:
        Tuple of (foe_effects, enrage_mods)
    """
    # Setup foe effect managers
    foe_effects = []
    for f in foes:
        mgr = EffectManager(f)
        f.effect_manager = mgr
        foe_effects.append(mgr)
    enrage_mods: list[StatModifier | None] = [None for _ in foes]

    # Setup party member effect managers
    for member in combat_party.members:
        mgr = EffectManager(member)
        member.effect_manager = mgr

    return foe_effects, enrage_mods


def setup_battle_state() -> None:
    """Setup global battle state."""
    # Mark battle as active to allow damage/heal processing
    try:
        from autofighter.stats import set_battle_active
        set_battle_active(True)
    except Exception:
        pass


def setup_visual_queue(combat_party: Party, foes: list[Stats]) -> None:
    """
    Initialize the visual action queue for UI snapshots.

    Args:
        combat_party: The combat party
        foes: List of foe entities
    """
    try:
        q_entities = list(combat_party.members) + list(foes)
        visual_queue = ActionQueue(q_entities)
    except Exception:
        visual_queue = None
    set_visual_queue(visual_queue)


def setup_battle_logging(combat_party: Party, foes: list[Stats]):
    """
    Initialize battle logging and capture initial state.

    Args:
        combat_party: The combat party
        foes: List of foe entities

    Returns:
        Battle logger instance
    """
    battle_logger = start_battle_logging()
    try:
        if battle_logger is not None:
            battle_logger.summary.party_members = [m.id for m in combat_party.members]
            battle_logger.summary.foes = [f.id for f in foes]
            # Snapshot party relics present at battle start (id -> count)
            relic_counts: dict[str, int] = {}
            for rid in combat_party.relics:
                relic_counts[rid] = relic_counts.get(rid, 0) + 1
            battle_logger.summary.party_relics = relic_counts
    except Exception:
        pass
    return battle_logger


async def emit_battle_start_events(
    combat_party: Party, foes: list[Stats], registry: PassiveRegistry
) -> None:
    """
    Emit battle start events for all entities.

    Args:
        combat_party: The combat party
        foes: List of foe entities
        registry: Passive registry for triggering passives
    """
    # Emit events for foes first
    for f in foes:
        await BUS.emit_async("battle_start", f)
        await registry.trigger("battle_start", f, party=combat_party.members, foes=foes)

    log.info(
        "Battle start: %s vs %s",
        [f.id for f in foes],
        [m.id for m in combat_party.members],
    )

    # Emit events for party members
    for member in combat_party.members:
        await BUS.emit_async("battle_start", member)
        await registry.trigger("battle_start", member, party=combat_party.members, foes=foes)


def setup_battle_variables(room: Room) -> tuple[bool, int, int, int, int, set[str]]:
    """
    Initialize battle tracking variables.

    Args:
        room: The battle room

    Returns:
        Tuple of (enrage_active, enrage_stacks, enrage_bleed_applies, threshold, exp_reward, credited_foe_ids)
    """
    # Import here to avoid circular imports
    from .boss import BossRoom

    enrage_active = False
    enrage_stacks = 0
    enrage_bleed_applies = 0
    # Ensure enrage percent starts at 0 for this battle
    set_enrage_percent(0.0)
    threshold = ENRAGE_TURNS_BOSS if isinstance(room, BossRoom) else ENRAGE_TURNS_NORMAL
    exp_reward = 0
    credited_foe_ids: set[str] = set()

    return enrage_active, enrage_stacks, enrage_bleed_applies, threshold, exp_reward, credited_foe_ids


def collect_summons(entities: list[Stats]) -> dict[str, list[dict[str, Any]]]:
    """
    Collect summon snapshots for entities.

    Args:
        entities: List of entity stats

    Returns:
        Dictionary mapping owner IDs to summon snapshots
    """
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


def create_queue_snapshot(combat_party: Party, foes: list[Stats]) -> list[dict[str, Any]]:
    """
    Create action queue snapshot for UI.

    Args:
        combat_party: The combat party
        foes: List of foe entities

    Returns:
        List of action queue entries
    """
    ordered = sorted(
        combat_party.members + foes,
        key=lambda c: getattr(c, "action_value", 0.0),
    )
    extras: list[dict[str, Any]] = []
    for ent in ordered:
        turns = get_extra_turns(ent)
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
    return extras + [
        {
            "id": getattr(c, "id", ""),
            "action_gauge": getattr(c, "action_gauge", 0),
            "action_value": getattr(c, "action_value", 0.0),
            "base_action_value": getattr(c, "base_action_value", 0.0),
        }
        for c in ordered
    ]
