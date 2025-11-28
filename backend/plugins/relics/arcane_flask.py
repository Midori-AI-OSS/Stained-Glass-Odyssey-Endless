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
    full_about: str = "After an Ultimate, grant a shield equal to 20% Max HP. Stacks additively (20% per stack)."
    summarized_about: str = "Grants shield based on max hp after using ultimate"

    async def apply(self, party, *, stacks: int | None = None) -> None:
        await super().apply(party, stacks=stacks)

        # Use passed stacks if available, otherwise count (for backward compat)
        if stacks is None:
            stacks = party.relics.count(self.id)
        state = getattr(party, "_arcane_flask_state", None)

        if state is None:
            state = {"stacks": stacks}
            party._arcane_flask_state = state
        else:
            state["stacks"] = stacks

        async def _ultimate(user) -> None:
            if user is None or user not in getattr(party, "members", ()):  # type: ignore[arg-type]
                return
            current_state = getattr(party, "_arcane_flask_state", {})
            current_stacks = current_state.get("stacks", 0)
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
            self.clear_subscriptions(party)
            if getattr(party, "_arcane_flask_state", None) is state:
                delattr(party, "_arcane_flask_state")

        self.subscribe(party, "ultimate_used", _ultimate)
        self.subscribe(party, "battle_end", _cleanup)

    def full_about_stacks(self, stacks: int) -> str:
        """Provide stack-aware description."""
        return self.describe(stacks)

    def describe(self, stacks: int) -> str:
        pct = 20 * stacks
        return f"After an Ultimate, grant a shield equal to {pct}% Max HP."
