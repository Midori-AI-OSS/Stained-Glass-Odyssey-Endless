from dataclasses import dataclass
from dataclasses import field

from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class RejuvenatingTonic(CardBase):
    id: str = "rejuvenating_tonic"
    name: str = "Rejuvenating Tonic"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"regain": 0.04})
    about: str = "+4% Regain; When using a heal, heal an additional +1% HP"

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        async def _on_heal(healer, target, heal_amount, source_type, source_name):
            # Check if healer is one of our party members and this is a heal action
            if healer in party.members and source_type in ["heal", "ability_heal"]:
                # Heal an additional +1% HP
                max_hp = getattr(target, 'max_hp', 1)
                bonus_heal = int(max_hp * 0.01)
                if bonus_heal > 0:
                    import asyncio
                    import logging
                    log = logging.getLogger(__name__)
                    try:
                        asyncio.create_task(target.apply_healing(bonus_heal, healer, source_type="rejuvenating_tonic", source_name="rejuvenating_tonic"))
                        log.debug("Rejuvenating Tonic bonus heal: +%d HP to %s", bonus_heal, target.id)
                        await BUS.emit_async("card_effect", self.id, healer, "bonus_heal", bonus_heal, {
                            "bonus_heal": bonus_heal,
                            "heal_percentage": 1,
                            "trigger_event": "heal_used"
                        })
                    except Exception as e:
                        log.warning("Error applying Rejuvenating Tonic bonus heal: %s", e)

        self.subscribe("heal", _on_heal)
