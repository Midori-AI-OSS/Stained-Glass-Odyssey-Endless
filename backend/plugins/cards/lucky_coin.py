from dataclasses import dataclass
from dataclasses import field
import random

from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class LuckyCoin(CardBase):
    id: str = "lucky_coin"
    name: str = "Lucky Coin"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"crit_rate": 0.03})
    about: str = "+3% Crit Rate; On critical hit, 20% chance to refund a tiny ultimate charge to the attacker"

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        async def _on_critical_hit(attacker, target, damage, action_name):
            # Check if attacker is one of our party members
            if attacker in party.members:
                # 20% chance to refund tiny ultimate charge
                if random.random() < 0.20:
                    # Refund 1 ultimate charge (tiny amount)
                    charge_refund = 1
                    attacker.add_ultimate_charge(charge_refund)
                    import logging
                    log = logging.getLogger(__name__)
                    log.debug("Lucky Coin ultimate charge refund: +%d charge to %s", charge_refund, attacker.id)
                    await BUS.emit_async("card_effect", self.id, attacker, "charge_refund", charge_refund, {
                        "charge_refund": charge_refund,
                        "trigger_chance": 0.20,
                        "trigger_event": "critical_hit"
                    })

        self.subscribe("critical_hit", _on_critical_hit)
