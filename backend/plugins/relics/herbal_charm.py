from dataclasses import dataclass
from dataclasses import field

from autofighter.stats import BUS
from plugins.relics._base import RelicBase
from plugins.relics._base import safe_async_task


@dataclass
class HerbalCharm(RelicBase):
    """Heals all allies for 0.5% Max HP at the start of each turn."""

    id: str = "herbal_charm"
    name: str = "Herbal Charm"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=dict)
    about: str = "Heals all allies for 0.5% Max HP at the start of each turn per stack."

    async def apply(self, party) -> None:
        await super().apply(party)

        state = getattr(party, "_herbal_charm_state", None)
        stacks = party.relics.count(self.id)

        if state is None:
            state = {"stacks": stacks}
            party._herbal_charm_state = state
        else:
            state["stacks"] = stacks

        async def _heal(*_) -> None:
            current_state = getattr(party, "_herbal_charm_state", {})
            current_stacks = current_state.get("stacks", 0)
            if current_stacks <= 0:
                return
            for member in party.members:
                heal = int(member.max_hp * 0.005 * current_stacks)

                # Emit relic effect event for healing
                await BUS.emit_async("relic_effect", "herbal_charm", member, "turn_start_healing", heal, {
                    "healing_percentage": 0.5 * current_stacks,
                    "max_hp": member.max_hp,
                    "stacks": current_stacks
                })

                safe_async_task(member.apply_healing(heal))

        def _cleanup(*_args) -> None:
            self.clear_subscriptions(party)
            if getattr(party, "_herbal_charm_state", None) is state:
                delattr(party, "_herbal_charm_state")

        self.subscribe(party, "turn_start", _heal)
        self.subscribe(party, "battle_end", _cleanup)

    def describe(self, stacks: int) -> str:
        pct = 0.5 * stacks
        return f"Heals all allies for {pct}% Max HP at the start of each turn."
