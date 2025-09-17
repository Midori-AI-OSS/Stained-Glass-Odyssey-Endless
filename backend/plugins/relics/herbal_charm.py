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

    def apply(self, party) -> None:
        state = getattr(party, "_herbal_charm_state", None)
        stacks = party.relics.count(self.id)

        if state is None:
            def _heal(*_) -> None:
                current_stacks = state.get("stacks", 0)
                if current_stacks <= 0:
                    return
                for member in party.members:
                    heal = int(member.max_hp * 0.005 * current_stacks)

                    # Emit relic effect event for healing
                    BUS.emit("relic_effect", "herbal_charm", member, "turn_start_healing", heal, {
                        "healing_percentage": 0.5 * current_stacks,
                        "max_hp": member.max_hp,
                        "stacks": current_stacks
                    })

                    safe_async_task(member.apply_healing(heal))

            def _cleanup(*_args) -> None:
                BUS.unsubscribe("turn_start", state["heal_handler"])
                BUS.unsubscribe("battle_end", state["cleanup_handler"])
                if getattr(party, "_herbal_charm_state", None) is state:
                    delattr(party, "_herbal_charm_state")

            state = {
                "stacks": stacks,
                "heal_handler": _heal,
                "cleanup_handler": _cleanup,
            }
            party._herbal_charm_state = state

            BUS.subscribe("turn_start", _heal)
            BUS.subscribe("battle_end", _cleanup)
        else:
            state["stacks"] = stacks

    def describe(self, stacks: int) -> str:
        pct = 0.5 * stacks
        return f"Heals all allies for {pct}% Max HP at the start of each turn."
