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

        stacks = party.relics.count(self.id)
        state = getattr(party, "_old_coin_state", None)

        if state is None:
            first_purchase_done = getattr(party, "_old_coin_first_purchase", False)

            def _gold(amount: int) -> None:
                current_stacks = state.get("stacks", 0)
                if current_stacks <= 0:
                    return
                bonus = int(amount * 0.03 * current_stacks)
                party.gold += bonus

                # Emit relic effect event for gold bonus
                BUS.emit("relic_effect", "old_coin", party, "gold_bonus", bonus, {
                    "original_amount": amount,
                    "bonus_percentage": 3 * current_stacks,
                    "stacks": current_stacks
                })

            def _purchase(cost: int) -> None:
                if state.get("first_purchase_done", False):
                    return
                current_stacks = state.get("stacks", 0)
                if current_stacks <= 0:
                    return
                refund = int(cost * 0.03 * current_stacks)
                party.gold += refund
                state["first_purchase_done"] = True
                party._old_coin_first_purchase = True

                # Emit relic effect event for purchase refund
                BUS.emit("relic_effect", "old_coin", party, "purchase_refund", refund, {
                    "original_cost": cost,
                    "refund_percentage": 3 * current_stacks,
                    "stacks": current_stacks,
                    "first_purchase": True
                })

            def _cleanup(*_args) -> None:
                BUS.unsubscribe("gold_earned", state["gold_handler"])
                BUS.unsubscribe("shop_purchase", state["purchase_handler"])
                BUS.unsubscribe("battle_end", state["cleanup_handler"])
                if getattr(party, "_old_coin_state", None) is state:
                    delattr(party, "_old_coin_state")

            state = {
                "stacks": stacks,
                "first_purchase_done": first_purchase_done,
                "gold_handler": _gold,
                "purchase_handler": _purchase,
                "cleanup_handler": _cleanup,
            }
            party._old_coin_state = state

            BUS.subscribe("gold_earned", _gold)
            BUS.subscribe("shop_purchase", _purchase)
            BUS.subscribe("battle_end", _cleanup)
        else:
            state["stacks"] = stacks

    def describe(self, stacks: int) -> str:
        rate = 3 * stacks
        return f"+{rate}% gold earned; first shop purchase refunded {rate}% of cost."
