from dataclasses import dataclass
from dataclasses import field

from autofighter.stats import BUS
from plugins.relics._base import RelicBase
from plugins.relics._base import safe_async_task


@dataclass
class CopperSiphon(RelicBase):
    """2% lifesteal per stack; excess healing converts to shields."""

    id: str = "copper_siphon"
    name: str = "Copper Siphon"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=dict)
    full_about: str = "When an ally deals damage, heal them for 2% of damage per stack (min 1 HP); excess becomes shields."
    summarized_about: str = "Allies gain lifesteal when dealing damage; excess healing becomes shields"

    async def apply(self, party) -> None:
        await super().apply(party)

        state = getattr(party, "_copper_siphon_state", None)
        stacks = party.relics.count(self.id)

        if state is None:
            state = {"stacks": stacks}
            party._copper_siphon_state = state
        else:
            state["stacks"] = stacks

        async def _on_action_used(attacker, target, amount, *_args) -> None:
            """Apply lifesteal when an ally deals damage."""
            # Check if attacker is a party member
            if attacker is None or attacker not in getattr(party, "members", ()):  # type: ignore[arg-type]
                return

            # Only trigger on positive damage
            if amount <= 0:
                return

            current_state = getattr(party, "_copper_siphon_state", {})
            current_stacks = current_state.get("stacks", 0)
            if current_stacks <= 0:
                return

            # Calculate lifesteal (2% per stack, minimum 1 HP)
            lifesteal_amount = max(1, int(amount * 0.02 * current_stacks))

            # Enable overheal so excess healing becomes shields
            attacker.enable_overheal()

            # Apply the healing
            safe_async_task(attacker.apply_healing(lifesteal_amount))

            # Emit telemetry
            await BUS.emit_async(
                "relic_effect",
                self.id,
                attacker,
                "lifesteal",
                lifesteal_amount,
                {
                    "damage_dealt": amount,
                    "lifesteal_percentage": 2 * current_stacks,
                    "stacks": current_stacks,
                    "overheal_enabled": True,
                },
            )

        def _cleanup(*_args) -> None:
            """Clean up subscriptions at battle end."""
            self.clear_subscriptions(party)
            if getattr(party, "_copper_siphon_state", None) is state:
                delattr(party, "_copper_siphon_state")

        self.subscribe(party, "action_used", _on_action_used)
        self.subscribe(party, "attack_used", _on_action_used)
        self.subscribe(party, "battle_end", _cleanup)

    def full_about_stacks(self, stacks: int) -> str:
        """Provide stack-aware description."""
        return self.describe(stacks)

    def describe(self, stacks: int) -> str:
        pct = 2 * stacks
        return f"When allies deal damage, heal them for {pct}% of damage (min 1 HP); excess becomes shields."
