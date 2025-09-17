from dataclasses import dataclass
from dataclasses import field
import logging
import math

from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class AdamantineBand(CardBase):
    id: str = "adamantine_band"
    name: str = "Adamantine Band"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"max_hp": 0.04})
    about: str = "+4% HP; If lethal damage would reduce you below 1 HP, reduce that damage by 10%"

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        async def _on_damage_taken(target, attacker, damage):
            # Check if target is one of our party members
            if target in party.members:
                current_hp = getattr(target, "hp", 0)
                pre_hp = current_hp + damage
                # Check if this damage would be lethal (reduce to 0 HP or below)
                if pre_hp > 0 and damage >= pre_hp:
                    damage_reduction = math.ceil(damage * 0.10)
                    max_hp = getattr(target, "max_hp", pre_hp)
                    restored_hp = current_hp + damage_reduction
                    target.hp = min(max(1, restored_hp), max_hp)
                    log = logging.getLogger(__name__)
                    log.debug(
                        "Adamantine Band lethal protection: +%d HP restored to %s",
                        target.hp - current_hp,
                        target.id,
                    )
                    await BUS.emit_async(
                        "card_effect",
                        self.id,
                        target,
                        "lethal_protection",
                        target.hp - current_hp,
                        {
                            "damage_reduction": damage_reduction,
                            "original_damage": damage,
                            "trigger_event": "lethal_damage",
                            "pre_damage_hp": pre_hp,
                        },
                    )

        BUS.subscribe("damage_taken", _on_damage_taken)
