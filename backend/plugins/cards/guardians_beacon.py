from dataclasses import dataclass, field

from autofighter.effects import EffectManager, create_stat_buff
from autofighter.stats import BUS
from plugins.cards._base import CardBase, safe_async_task


@dataclass
class GuardiansBeacon(CardBase):
    """+55% DEF; at turn end, heal lowest-HP ally for 8% Max HP (+ 10% mitigation if Light)."""

    id: str = "guardians_beacon"
    name: str = "Guardian's Beacon"
    stars: int = 2
    effects: dict[str, float] = field(default_factory=lambda: {"defense": 0.55})
    full_about: str = (
        "+55% DEF; at turn end, heal lowest-HP ally for 8% Max HP. "
        "If the healed ally is Light type, also grant them +10% mitigation for 1 turn."
    )
    summarized_about: str = (
        "Boosts def; heals lowest-HP ally at turn end with bonus mitigation for Light allies"
    )

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        async def _on_turn_end(*_args) -> None:
            """Heal lowest-HP ally at end of turn."""
            # Find lowest-HP ally
            lowest_hp_ally = None
            lowest_hp_pct = float("inf")

            for member in party.members:
                if member.hp <= 0:
                    # Skip dead allies
                    continue

                hp_pct = member.hp / member.max_hp if member.max_hp > 0 else 0
                if hp_pct < lowest_hp_pct:
                    lowest_hp_pct = hp_pct
                    lowest_hp_ally = member

            if lowest_hp_ally is None:
                return

            # Calculate healing (8% of Max HP)
            heal_amount = int(lowest_hp_ally.max_hp * 0.08)

            # Apply healing
            safe_async_task(lowest_hp_ally.apply_healing(heal_amount))

            # Check if ally is Light type
            damage_type = getattr(lowest_hp_ally, "damage_type", None)
            damage_type_id = getattr(damage_type, "id", str(damage_type)) if damage_type else None
            is_light = damage_type_id == "Light"

            # Grant mitigation bonus if Light
            mitigation_bonus = 0
            if is_light:
                mitigation_bonus = 0.10

                # Get or create effect manager
                effect_manager = getattr(lowest_hp_ally, "effect_manager", None)
                if effect_manager is None:
                    effect_manager = EffectManager(lowest_hp_ally)
                    lowest_hp_ally.effect_manager = effect_manager

                # Grant +10% mitigation for 1 turn
                mitigation_mod = create_stat_buff(
                    lowest_hp_ally,
                    name=f"{self.id}_light_mitigation",
                    turns=1,
                    mitigation_mult=1.10,
                )
                await effect_manager.add_modifier(mitigation_mod)

            # Emit telemetry
            await BUS.emit_async(
                "card_effect",
                self.id,
                lowest_hp_ally,
                "turn_end_heal",
                heal_amount,
                {
                    "heal_percentage": 8,
                    "hp_percentage": lowest_hp_pct * 100,
                    "is_light": is_light,
                    "mitigation_bonus": mitigation_bonus * 100 if mitigation_bonus > 0 else 0,
                },
            )

        self.subscribe("turn_end", _on_turn_end)
