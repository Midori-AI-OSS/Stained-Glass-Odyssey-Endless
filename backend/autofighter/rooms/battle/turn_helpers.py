"""Helper functions shared by the battle turn loop."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

from autofighter.stats import BUS

from .pacing import clear_extra_turns_for

if TYPE_CHECKING:
    from ...party import Party
    from .core import BattleRoom


async def credit_if_dead(
    *,
    foe_obj: Any,
    credited_foe_ids: set[str],
    combat_party: Party,
    party: Party,
    room: BattleRoom,
    exp_reward: int,
    temp_rdr: float,
) -> tuple[int, float]:
    """Credit experience and rewards if the foe has been defeated."""

    updated_exp_reward = exp_reward
    updated_temp_rdr = temp_rdr

    try:
        foe_id = getattr(foe_obj, "id", None)
        if getattr(foe_obj, "hp", 1) <= 0 and foe_id and foe_id not in credited_foe_ids:
            await BUS.emit_async(
                "entity_killed",
                foe_obj,
                None,
                0,
                "death",
                {"victim_type": "foe", "killer_type": "party"},
            )
            updated_exp_reward += foe_obj.level * 12 + 5 * room.node.index
            updated_temp_rdr += 0.55
            credited_foe_ids.add(foe_id)
            try:
                label = (
                    getattr(foe_obj, "name", None)
                    or getattr(foe_obj, "id", "")
                ).lower()
                if "slime" in label:
                    for member in combat_party.members:
                        member.exp_multiplier += 0.025
                    for member in party.members:
                        member.exp_multiplier += 0.025
            except Exception:
                pass
    except Exception:
        pass

    return updated_exp_reward, updated_temp_rdr


def remove_dead_foes(
    *,
    foes: list[Any],
    foe_effects: list[Any],
    enrage_mods: list[Any],
) -> None:
    """Prune defeated foes and their associated state."""

    for index in range(len(foes) - 1, -1, -1):
        if getattr(foes[index], "hp", 1) <= 0:
            foe = foes.pop(index)
            foe_effects.pop(index)
            enrage_mods.pop(index)
            clear_extra_turns_for(foe)
