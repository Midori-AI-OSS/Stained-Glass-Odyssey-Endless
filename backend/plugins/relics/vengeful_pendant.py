from dataclasses import dataclass, field

from autofighter.stats import BUS
from plugins.relics._base import RelicBase, safe_async_task


@dataclass
class VengefulPendant(RelicBase):
    """Reflects 15% of damage taken back to the attacker."""

    id: str = "vengeful_pendant"
    name: str = "Vengeful Pendant"
    stars: int = 2
    effects: dict[str, float] = field(default_factory=dict)
    full_about: str = (
        "Whenever a party member takes damage, 15% of that damage per stack is reflected back "
        "to the attacker. The reflected damage is applied immediately after the original damage "
        "and is guaranteed to deal at least 1 damage. Multiple stacks multiply the reflection "
        "(e.g., 2 stacks = 30%, 3 stacks = 45%)."
    )
    summarized_about: str = (
        "Reflects a portion of damage taken back to attackers"
    )

    async def apply(self, party) -> None:
        await super().apply(party)

        stacks = party.relics.count(self.id)
        state = getattr(party, "_vengeful_pendant_state", None)

        if state is None:
            state = {"stacks": stacks}
            party._vengeful_pendant_state = state
        else:
            state["stacks"] = stacks

        async def _reflect(target, attacker, amount, *_: object) -> None:
            if attacker is None or target not in party.members:
                return
            current_state = getattr(party, "_vengeful_pendant_state", {})
            current_stacks = current_state.get("stacks", 0)
            if current_stacks <= 0:
                return
            dmg = max(1, int(amount * 0.15 * current_stacks))

            # Emit relic effect event for damage reflection
            await BUS.emit_async(
                "relic_effect",
                "vengeful_pendant",
                target,
                "damage_reflection",
                dmg,
                {
                    "original_damage": amount,
                    "reflection_percentage": 15 * current_stacks,
                    "reflected_to": getattr(attacker, "id", str(attacker)),
                    "stacks": current_stacks,
                },
            )

            safe_async_task(attacker.apply_damage(dmg, attacker=target))

        def _cleanup(*_args) -> None:
            self.clear_subscriptions(party)
            if getattr(party, "_vengeful_pendant_state", None) is state:
                delattr(party, "_vengeful_pendant_state")

        self.subscribe(party, "damage_taken", _reflect)
        self.subscribe(party, "battle_end", _cleanup)

    def full_about_stacks(self, stacks: int) -> str:
        """Provide stack-aware description by reusing existing describe logic."""
        return self.describe(stacks)

    def describe(self, stacks: int) -> str:
        pct = 15 * stacks
        return f"Reflects {pct}% of damage taken back to the attacker."
