from dataclasses import dataclass
from dataclasses import field

from autofighter.stats import BUS
from plugins.relics._base import RelicBase
from plugins.relics._base import safe_async_task


@dataclass
class ArcaneFlask(RelicBase):
    """After an Ultimate, grant a shield equal to 20% Max HP per stack."""

    id: str = "arcane_flask"
    name: str = "Arcane Flask"
    stars: int = 2
    effects: dict[str, float] = field(default_factory=dict)
    about: str = "After an Ultimate, grant a shield equal to 20% Max HP."

    async def apply(self, party) -> None:
        await super().apply(party)

        stacks = party.relics.count(self.id)
        state = getattr(party, "_arcane_flask_state", None)

        if state is None:
            state = {"stacks": stacks}

            async def _ultimate(user) -> None:
                current_stacks = state.get("stacks", 0)
                if current_stacks <= 0:
                    return

                user.enable_overheal()  # Enable shields for the user
                shield = int(user.max_hp * 0.2 * current_stacks)

                # Track the shield generation
                await BUS.emit_async("relic_effect", "arcane_flask", user, "shield_granted", shield, {
                    "shield_percentage": 20 * current_stacks,
                    "max_hp": user.max_hp,
                    "trigger": "ultimate_used",
                    "stacks": current_stacks
                })

                safe_async_task(user.apply_healing(shield))

            def _cleanup(*_: object) -> None:
                BUS.unsubscribe("ultimate_used", state["ultimate_handler"])
                BUS.unsubscribe("battle_end", state["cleanup_handler"])
                if getattr(party, "_arcane_flask_state", None) is state:
                    delattr(party, "_arcane_flask_state")

            state["ultimate_handler"] = _ultimate
            state["cleanup_handler"] = _cleanup
            party._arcane_flask_state = state

            BUS.subscribe("ultimate_used", _ultimate)
            BUS.subscribe("battle_end", _cleanup)
        else:
            state["stacks"] = stacks

    def describe(self, stacks: int) -> str:
        pct = 20 * stacks
        return f"After an Ultimate, grant a shield equal to {pct}% Max HP."