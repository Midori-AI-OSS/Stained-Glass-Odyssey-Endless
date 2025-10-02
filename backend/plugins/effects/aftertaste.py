from dataclasses import dataclass
from dataclasses import field
import random

from autofighter.stats import Stats
from plugins.damage_types.dark import Dark
from plugins.damage_types.fire import Fire
from plugins.damage_types.ice import Ice
from plugins.damage_types.light import Light
from plugins.damage_types.lightning import Lightning
from plugins.damage_types.wind import Wind


@dataclass
class Aftertaste:
    plugin_type = "effect"
    id = "aftertaste"

    hits: int = 1
    base_pot: int = 25
    rng: random.Random = field(default_factory=random.Random)
    use_weighted_random: bool = True  # Favor attacker's damage type

    # Available damage types for random selection
    _damage_types = [Fire, Ice, Wind, Lightning, Light, Dark]

    @classmethod
    def get_description(cls) -> str:
        """Get the description of this effect for display purposes."""
        return (
            "Deals a hit with random damage type (10% to 150% damage) while respecting "
            "TURN_PACING between echoes."
        )

    def _get_random_damage_type(self, attacker: Stats = None):
        """Get a random damage type, optionally weighted toward attacker's type."""
        if not self.use_weighted_random or attacker is None:
            # Pure random selection
            damage_type_class = self.rng.choice(self._damage_types)
            return damage_type_class()

        # Weighted selection favoring attacker's damage type
        attacker_type_id = getattr(attacker.damage_type, 'id', 'Light')

        # Find the attacker's damage type class
        attacker_damage_class = None
        for dt_class in self._damage_types:
            if dt_class().id == attacker_type_id:
                attacker_damage_class = dt_class
                break

        if attacker_damage_class is None:
            attacker_damage_class = Light

        # Create weighted selection: 25% chance for attacker's type, 50% for others
        if self.rng.random() < 0.25:
            return attacker_damage_class()
        else:
            # Select from remaining types
            other_types = [dt for dt in self._damage_types if dt != attacker_damage_class]
            damage_type_class = self.rng.choice(other_types)
            return damage_type_class()

    def rolls(self) -> list[int]:
        return [int(self.base_pot * self.rng.uniform(0.1, 1.5)) for _ in range(self.hits)]

    async def apply(self, attacker: Stats, target: Stats) -> list[int]:
        from autofighter.rooms.battle.pacing import YIELD_MULTIPLIER
        from autofighter.rooms.battle.pacing import pace_sleep

        results: list[int] = []
        for amount in self.rolls():
            # Create a temporary attacker with random damage type for this hit
            random_damage_type = self._get_random_damage_type(attacker)

            # Create a temporary Stats object with the random damage type
            temp_attacker = Stats()
            # Copy relevant attributes from original attacker
            if attacker:
                temp_attacker._base_atk = attacker._base_atk
                temp_attacker._base_crit_rate = attacker._base_crit_rate
                temp_attacker._base_crit_damage = attacker._base_crit_damage
                temp_attacker._base_vitality = attacker._base_vitality
                temp_attacker._active_effects = attacker._active_effects.copy()
                # Copy ID if it exists to prevent logging errors
                if hasattr(attacker, 'id'):
                    temp_attacker.id = attacker.id

            # Set the random damage type
            temp_attacker.damage_type = random_damage_type

            # Emit event before applying damage to track aftertaste as relic effect
            from autofighter.stats import BUS
            await BUS.emit_async(
                "relic_effect",
                "aftertaste",
                attacker,
                "aftertaste",
                amount,
                {
                    "effect_label": "aftertaste",
                    "effect_type": "aftertaste",
                    "base_damage": self.base_pot,
                    "random_damage_type": (
                        random_damage_type.id
                        if hasattr(random_damage_type, "id")
                        else str(random_damage_type)
                    ),
                    "actual_damage": amount,
                },
            )

            dmg = await target.apply_damage(amount, temp_attacker, action_name="Aftertaste")
            results.append(dmg)
            await pace_sleep(YIELD_MULTIPLIER)
        return results
