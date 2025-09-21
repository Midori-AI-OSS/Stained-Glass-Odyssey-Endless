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

    async def apply(self, party) -> None:
        await super().apply(party)

        stacks = party.relics.count(self.id)
        state = getattr(party, "_old_coin_state", None)

        if state is None:
            state = {
                "stacks": stacks,
                "first_purchase_done": getattr(party, "_old_coin_first_purchase", False),
            }
            party._old_coin_state = state
        else:
            state["stacks"] = stacks

        async def _gold(amount: int) -> None:
            current_state = getattr(party, "_old_coin_state", {})
            current_stacks = current_state.get("stacks", 0)
            if current_stacks <= 0:
                return
            bonus = int(amount * 0.03 * current_stacks)
            party.gold += bonus

            # Emit relic effect event for gold bonus
            await BUS.emit_async("relic_effect", "old_coin", party, "gold_bonus", bonus, {
                "original_amount": amount,
                "bonus_percentage": 3 * current_stacks,
                "stacks": current_stacks
            })

        async def _purchase(cost: int) -> None:
            current_state = getattr(party, "_old_coin_state", {})
            if current_state.get("first_purchase_done", False):
                return
            current_stacks = current_state.get("stacks", 0)
            if current_stacks <= 0:
                return
            refund = int(cost * 0.03 * current_stacks)
            party.gold += refund
            current_state["first_purchase_done"] = True
            party._old_coin_first_purchase = True

            # Emit relic effect event for purchase refund
            await BUS.emit_async("relic_effect", "old_coin", party, "purchase_refund", refund, {
                "original_cost": cost,
                "refund_percentage": 3 * current_stacks,
                "stacks": current_stacks,
                "first_purchase": True
            })

        def _cleanup(*_args) -> None:
            self.clear_subscriptions(party)
            if getattr(party, "_old_coin_state", None) is state:
                delattr(party, "_old_coin_state")

        self.subscribe(party, "gold_earned", _gold)
        self.subscribe(party, "shop_purchase", _purchase)
        self.subscribe(party, "battle_end", _cleanup)

    def describe(self, stacks: int) -> str:
        rate = 3 * stacks
        return f"+{rate}% gold earned; first shop purchase refunded {rate}% of cost."
