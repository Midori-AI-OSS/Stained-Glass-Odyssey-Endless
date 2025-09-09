from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import ClassVar

from autofighter.stats import StatEffect

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class LadyDarknessEclipsingVeil:
    """Lady Darkness's Eclipsing Veil passive - DoT enhancement and siphoning."""

    plugin_type = "passive"
    id = "lady_darkness_eclipsing_veil"
    name = "Eclipsing Veil"
    trigger = "turn_start"  # Triggers at start of turn for DoT management
    max_stacks = 1  # Only one instance per character
    stack_display = "spinner"

    # Class-level tracking of attack bonuses from debuff resistance
    _attack_bonuses: ClassVar[dict[int, int]] = {}

    async def apply(self, target: "Stats") -> None:
        """Apply Lady Darkness's DoT enhancement and siphoning mechanics."""
        entity_id = id(target)

        # Initialize attack bonus tracking if not present
        if entity_id not in self._attack_bonuses:
            self._attack_bonuses[entity_id] = 0

        # Extend DoT durations by one turn (would need DoT system integration)
        # For now, apply this as a passive effect that the DoT system can check
        dot_extension_effect = StatEffect(
            name=f"{self.id}_dot_extension",
            stat_modifiers={"dot_duration_bonus": 1},  # Extend DoTs by 1 turn
            duration=-1,  # Permanent passive effect
            source=self.id,
        )
        target.add_effect(dot_extension_effect)

        # Apply current attack bonus from previous debuff resistances
        if self._attack_bonuses[entity_id] > 0:
            attack_bonus_effect = StatEffect(
                name=f"{self.id}_debuff_resistance_bonus",
                stat_modifiers={"atk": self._attack_bonuses[entity_id]},
                duration=-1,  # Permanent for rest of battle
                source=self.id,
            )
            target.add_effect(attack_bonus_effect)

    async def on_dot_tick(self, target: "Stats", dot_damage: int) -> None:
        """Siphon 1% of DoT damage as HoT when any DoT ticks on the battlefield."""
        # Siphon 1% of the DoT damage as healing
        siphoned_healing = max(1, int(dot_damage * 0.01))

        # Apply immediate healing using proper healing system
        await target.apply_healing(siphoned_healing)

    async def on_debuff_resist(self, target: "Stats") -> None:
        """Grant +5% attack when resisting a debuff."""
        entity_id = id(target)

        # Increase permanent attack bonus by 5%
        attack_increase = int(target.atk * 0.05)
        self._attack_bonuses[entity_id] += attack_increase

        # Apply the bonus immediately
        resist_bonus_effect = StatEffect(
            name=f"{self.id}_resist_bonus_{entity_id}",
            stat_modifiers={"atk": attack_increase},
            duration=-1,  # Permanent for rest of battle
            source=self.id,
        )
        target.add_effect(resist_bonus_effect)

    @classmethod
    def get_attack_bonus(cls, target: "Stats") -> int:
        """Get current attack bonus from debuff resistances."""
        return cls._attack_bonuses.get(id(target), 0)

    @classmethod
    def get_description(cls) -> str:
        return (
            "Extends DoTs by one turn and siphons 1% of each DoT tick as healing. "
            "Resisting a debuff grants +5% attack, stacking indefinitely."
        )
