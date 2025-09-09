from dataclasses import dataclass
from dataclasses import field

from autofighter.stats import BUS
from plugins.relics._base import RelicBase


@dataclass
class OldCoin(RelicBase):
    """+3% gold earned; first shop purchase refunded 3% of cost."""

    id: str = "old_coin"
    name: str = "Old Coin"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=dict)
    about: str = "+3% gold earned; first shop purchase refunded 3% of cost."

    def apply(self, party) -> None:
        super().apply(party)

        first_purchase = {"done": False}

        def _gold(amount: int) -> None:
            stacks = party.relics.count(self.id)
            bonus = int(amount * 0.03 * stacks)
            party.gold += bonus

            # Emit relic effect event for gold bonus
            BUS.emit(
                "relic_effect",
                "old_coin",
                party,
                "gold_bonus",
                bonus,
                {
                    "original_amount": amount,
                    "bonus_percentage": 3 * stacks,
                    "stacks": stacks,
                },
            )

        def _purchase(cost: int) -> None:
            if first_purchase["done"]:
                return
            stacks = party.relics.count(self.id)
            refund = int(cost * 0.03 * stacks)
            party.gold += refund
            first_purchase["done"] = True

            # Emit relic effect event for purchase refund
            BUS.emit(
                "relic_effect",
                "old_coin",
                party,
                "purchase_refund",
                refund,
                {
                    "original_cost": cost,
                    "refund_percentage": 3 * stacks,
                    "stacks": stacks,
                    "first_purchase": True,
                },
            )

        BUS.subscribe("gold_earned", _gold)
        BUS.subscribe("shop_purchase", _purchase)

    def describe(self, stacks: int) -> str:
        rate = 3 * stacks
        return f"+{rate}% gold earned; first shop purchase refunded {rate}% of cost."
