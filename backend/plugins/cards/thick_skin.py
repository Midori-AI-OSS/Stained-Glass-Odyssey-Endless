from dataclasses import dataclass
from dataclasses import field
import random

from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class ThickSkin(CardBase):
    id: str = "thick_skin"
    name: str = "Thick Skin"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"bleed_resist": 0.03})
    about: str = "+3% Bleed Resist; When afflicted by Bleed, 50% chance to reduce its duration by 1"

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        async def _on_effect_applied(target, effect_name, duration, source):
            # Check if target is one of our party members and effect is bleed
            if target in party.members and "bleed" in effect_name.lower():
                # 50% chance to reduce bleed duration by 1
                if random.random() < 0.50:
                    # Try to reduce the effect duration if it exists
                    effect_manager = getattr(target, 'effect_manager', None)
                    if effect_manager and hasattr(effect_manager, 'modifiers'):
                        for modifier in effect_manager.modifiers:
                            if hasattr(modifier, 'name') and "bleed" in modifier.name.lower():
                                if hasattr(modifier, 'turns') and modifier.turns > 1:
                                    modifier.turns -= 1
                                    import logging
                                    log = logging.getLogger(__name__)
                                    log.debug("Thick Skin reduced bleed duration by 1 turn for %s", target.id)
                                    await BUS.emit_async("card_effect", self.id, target, "duration_reduction", 1, {
                                        "effect_reduced": effect_name,
                                        "turns_reduced": 1,
                                        "trigger_chance": 0.50
                                    })
                                    break

        BUS.subscribe("effect_applied", _on_effect_applied)

        def _on_battle_end(entity) -> None:
            BUS.unsubscribe("effect_applied", _on_effect_applied)
            BUS.unsubscribe("battle_end", _on_battle_end)

        BUS.subscribe("battle_end", _on_battle_end)
