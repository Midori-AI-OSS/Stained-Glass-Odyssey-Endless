from dataclasses import dataclass
from dataclasses import field
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

        async def _on_effect_applied(target, effect_name, duration, source):
            # Check if target is one of our party members and effect is a long debuff
            if target in party.members and duration >= 3:  # Long debuff (3+ turns)
                effect_lower = effect_name.lower()
                is_debuff = any(keyword in effect_lower for keyword in
                               ['bleed', 'poison', 'burn', 'freeze', 'stun', 'silence', 'slow', 'weakness', 'curse'])

                if is_debuff and random.random() < 0.30:
                    # Reduce duration by 1 (30% chance)
                    # Try to find and modify the effect duration
                    effect_manager = getattr(target, 'effect_manager', None)
                    if effect_manager and hasattr(effect_manager, 'modifiers'):
                        for modifier in effect_manager.modifiers:
                            if hasattr(modifier, 'name') and effect_name.lower() in modifier.name.lower():
                                if hasattr(modifier, 'turns') and modifier.turns > 1:
                                    modifier.turns -= 1
                                    import logging
                                    log = logging.getLogger(__name__)
                                    log.debug("Reinforced Cloak reduced long debuff duration by 1 for %s (%s)", target.id, effect_name)
                                    await BUS.emit_async("card_effect", self.id, target, "debuff_duration_reduction", 1, {
                                        "effect_reduced": effect_name,
                                        "turns_reduced": 1,
                                        "trigger_chance": 0.30,
                                        "original_duration": duration
                                    })
                                    break

        BUS.subscribe("effect_applied", _on_effect_applied)