from dataclasses import dataclass
from dataclasses import field
import logging
import random

from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class ReinforcedCloak(CardBase):
    id: str = "reinforced_cloak"
    name: str = "Reinforced Cloak"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"defense": 0.03, "effect_resistance": 0.03})
    about: str = "+3% DEF & +3% Effect Res; 30% chance to reduce the starting duration of long debuffs by 1"

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        async def _on_effect_applied(effect_name, entity, details=None):
            if entity not in party.members or not details:
                return

            starting_turns = details.get("turns")
            if starting_turns is None or starting_turns < 3:
                return

            effect_type = details.get("effect_type")
            if effect_type not in {"stat_modifier", "dot"}:
                return

            effect_id = details.get("effect_id")
            if not effect_id:
                return

            effect_manager = getattr(entity, "effect_manager", None)
            pool_name = "mods" if effect_type == "stat_modifier" else "dots"
            if effect_manager is None or not hasattr(effect_manager, pool_name):
                self.cleanup_subscriptions()
                return

            pool = getattr(effect_manager, pool_name)
            modifier = next(
                (
                    mod
                    for mod in reversed(pool)
                    if getattr(mod, "id", None) == effect_id
                ),
                None,
            )

            if modifier is None or not hasattr(modifier, "turns"):
                return

            if effect_type == "stat_modifier":
                deltas = getattr(modifier, "deltas", None) or {}
                multipliers = getattr(modifier, "multipliers", None) or {}
                has_negative_delta = any(value < 0 for value in deltas.values())
                has_negative_multiplier = any(value < 1 for value in multipliers.values())

                if not has_negative_delta and not has_negative_multiplier:
                    return
            else:
                damage = getattr(modifier, "damage", None)
                if damage is not None and damage <= 0:
                    return

            if random.random() >= 0.30:
                return

            if modifier.turns <= 1:
                return

            modifier.turns -= 1

            log = logging.getLogger(__name__)
            log.debug(
                "Reinforced Cloak reduced long debuff duration by 1 for %s (%s)",
                getattr(entity, "id", entity),
                effect_name,
            )
            await BUS.emit_async(
                "card_effect",
                self.id,
                entity,
                "debuff_duration_reduction",
                1,
                {
                    "effect_reduced": effect_name,
                    "turns_reduced": 1,
                    "trigger_chance": 0.30,
                    "original_duration": starting_turns,
                },
            )

        def _on_battle_end(actor) -> None:
            if actor in party.members:
                self.cleanup_subscriptions()

        self.subscribe("effect_applied", _on_effect_applied)
        self.subscribe("battle_end", _on_battle_end)
