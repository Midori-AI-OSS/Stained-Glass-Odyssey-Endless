from dataclasses import dataclass
from dataclasses import field
import logging
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

        log = logging.getLogger(__name__)

        async def _on_effect_applied(effect_name, entity, details=None):
            if entity not in party.members:
                return

            if not details or details.get("effect_type") != "dot":
                return

            effect_id = (details.get("effect_id") or "").lower()
            if "bleed" not in effect_name.lower() and "bleed" not in effect_id:
                return

            if random.random() >= 0.50:
                return

            effect_manager = getattr(entity, "effect_manager", None)
            if effect_manager is None:
                return

            bleed_effect = next(
                (
                    eff
                    for eff in reversed(getattr(effect_manager, "dots", []))
                    if "bleed" in getattr(eff, "id", "").lower()
                    or "bleed" in getattr(eff, "name", "").lower()
                ),
                None,
            )

            if bleed_effect is None or getattr(bleed_effect, "turns", 0) <= 0:
                return

            bleed_effect.turns = max(bleed_effect.turns - 1, 0)

            log.debug(
                "Thick Skin reduced bleed duration by 1 turn for %s", getattr(entity, "id", None)
            )
            await BUS.emit_async(
                "card_effect",
                self.id,
                entity,
                "duration_reduction",
                1,
                {
                    "effect_reduced": effect_name,
                    "turns_reduced": 1,
                    "trigger_chance": 0.50,
                },
            )

        self.subscribe("effect_applied", _on_effect_applied)

        def _on_battle_end(entity) -> None:
            self.cleanup_subscriptions()

        self.subscribe("battle_end", _on_battle_end)
