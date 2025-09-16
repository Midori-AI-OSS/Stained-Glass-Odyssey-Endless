from __future__ import annotations

from ..turn_helpers import remove_dead_foes
from .initialization import TurnLoopContext


def foes_standing(context: TurnLoopContext) -> bool:
    return any(getattr(foe, "hp", 0) > 0 for foe in context.foes)


def party_standing(context: TurnLoopContext) -> bool:
    return any(member.hp > 0 for member in context.combat_party.members)


def battle_active(context: TurnLoopContext) -> bool:
    return foes_standing(context) and party_standing(context)


def cleanup_after_round(context: TurnLoopContext) -> bool:
    remove_dead_foes(
        foes=context.foes,
        foe_effects=context.foe_effects,
        enrage_mods=context.enrage_mods,
    )
    return battle_active(context)
