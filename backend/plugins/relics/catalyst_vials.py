from dataclasses import dataclass
from dataclasses import field

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.relics._base import RelicBase
from plugins.relics._base import safe_async_task


@dataclass
class CatalystVials(RelicBase):
    """DoT ticks heal attacker for 5% of damage per stack and grant +5% Effect Hit Rate for 1 turn."""

    id: str = "catalyst_vials"
    name: str = "Catalyst Vials"
    stars: int = 2
    effects: dict[str, float] = field(default_factory=dict)
    about: str = "When an ally's DoT ticks, heal them for 5% of damage per stack and grant +5% Effect Hit Rate for 1 turn"

    async def apply(self, party) -> None:
        await super().apply(party)

        state = getattr(party, "_catalyst_vials_state", None)
        stacks = party.relics.count(self.id)

        if state is None:
            state = {"stacks": stacks}
            party._catalyst_vials_state = state
        else:
            state["stacks"] = stacks

        async def _on_dot_tick(attacker, target, amount, *_args) -> None:
            """Convert DoT damage to healing and grant effect hit rate buff."""
            # Check if attacker is a party member
            if attacker is None or attacker not in getattr(party, "members", ()):  # type: ignore[arg-type]
                return

            # Only trigger on positive damage
            if amount is None or amount <= 0:
                return

            current_state = getattr(party, "_catalyst_vials_state", {})
            current_stacks = current_state.get("stacks", 0)
            if current_stacks <= 0:
                return

            # Calculate healing (5% per stack)
            heal_amount = max(1, int(amount * 0.05 * current_stacks))

            # Apply healing
            safe_async_task(attacker.apply_healing(heal_amount))

            # Get or create effect manager
            effect_manager = getattr(attacker, "effect_manager", None)
            if effect_manager is None:
                effect_manager = EffectManager(attacker)
                attacker.effect_manager = effect_manager

            # Grant +5% Effect Hit Rate per stack for 1 turn
            effect_hit_bonus = 0.05 * current_stacks
            effect_mod = create_stat_buff(
                attacker,
                name=f"{self.id}_effect_hit",
                turns=1,
                effect_hit_rate_mult=1 + effect_hit_bonus,
            )
            await effect_manager.add_modifier(effect_mod)

            # Emit telemetry
            await BUS.emit_async(
                "relic_effect",
                self.id,
                attacker,
                "dot_siphon",
                heal_amount,
                {
                    "dot_damage": amount,
                    "heal_percentage": 5 * current_stacks,
                    "effect_hit_bonus_percentage": effect_hit_bonus * 100,
                    "stacks": current_stacks,
                },
            )

        def _cleanup(*_args) -> None:
            """Clean up subscriptions at battle end."""
            self.clear_subscriptions(party)
            if getattr(party, "_catalyst_vials_state", None) is state:
                delattr(party, "_catalyst_vials_state")

        self.subscribe(party, "dot_tick", _on_dot_tick)
        self.subscribe(party, "battle_end", _cleanup)

    def describe(self, stacks: int) -> str:
        heal_pct = 5 * stacks
        effect_pct = 5 * stacks
        return f"When allies' DoTs tick, heal them for {heal_pct}% of damage and grant +{effect_pct}% Effect Hit Rate for 1 turn."
