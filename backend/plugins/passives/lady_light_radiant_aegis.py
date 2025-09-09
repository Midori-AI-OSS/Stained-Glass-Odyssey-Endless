from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import ClassVar

from autofighter.stats import StatEffect

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class LadyLightRadiantAegis:
    """Lady Light's Radiant Aegis passive - HoT enhancements with shields and cleansing."""

    plugin_type = "passive"
    id = "lady_light_radiant_aegis"
    name = "Radiant Aegis"
    trigger = "action_taken"  # Triggers when Lady Light acts (heals)
    max_stacks = 1  # Only one instance per character
    stack_display = "spinner"

    # Class-level tracking of attack bonuses from cleansing DoTs
    _attack_bonuses: ClassVar[dict[int, int]] = {}

    async def apply(self, target: "Stats") -> None:
        """Apply Lady Light's HoT enhancement mechanics."""
        entity_id = id(target)

        # Initialize attack bonus tracking if not present
        if entity_id not in self._attack_bonuses:
            self._attack_bonuses[entity_id] = 0

        # Apply current attack bonus from previous cleanses
        if self._attack_bonuses[entity_id] > 0:
            attack_bonus_effect = StatEffect(
                name=f"{self.id}_cleanse_bonus",
                stat_modifiers={"atk": self._attack_bonuses[entity_id]},
                duration=-1,  # Permanent for rest of battle
                source=self.id,
            )
            target.add_effect(attack_bonus_effect)

    async def on_hot_applied(
        self, target: "Stats", healed_ally: "Stats", hot_amount: int
    ) -> None:
        """Enhance HoTs with shields and effect resistance."""
        # Grant one-turn shield to the healed ally
        shield_amount = int(hot_amount * 0.5)  # Shield equal to 50% of HoT amount

        shield_effect = StatEffect(
            name=f"{self.id}_hot_shield",
            stat_modifiers={"hp": shield_amount},  # Temporary HP boost
            duration=1,  # One turn shield
            source=self.id,
        )
        healed_ally.add_effect(shield_effect)

        # Grant +5% effect resistance for one turn
        resistance_effect = StatEffect(
            name=f"{self.id}_hot_resistance",
            stat_modifiers={
                "effect_resistance": 0.05
            },  # 5% resistance to negative effects
            duration=1,  # One turn
            source=self.id,
        )
        healed_ally.add_effect(resistance_effect)

    async def on_dot_cleanse(self, target: "Stats", cleansed_ally: "Stats") -> None:
        """Grant bonuses when cleansing a DoT."""
        entity_id = id(target)

        # Heal ally for additional 5% of their max HP
        additional_healing = int(cleansed_ally.max_hp * 0.05)
        cleansed_ally.hp = min(
            cleansed_ally.max_hp, cleansed_ally.hp + additional_healing
        )

        # Grant Lady Light +2% attack (stacking with no cap)
        attack_increase = int(target.atk * 0.02)
        self._attack_bonuses[entity_id] += attack_increase

        # Apply the bonus immediately
        cleanse_bonus_effect = StatEffect(
            name=f"{self.id}_cleanse_attack_{entity_id}",
            stat_modifiers={"atk": attack_increase},
            duration=-1,  # Permanent for rest of battle
            source=self.id,
        )
        target.add_effect(cleanse_bonus_effect)

    @classmethod
    def get_attack_bonus(cls, target: "Stats") -> int:
        """Get current attack bonus from DoT cleanses."""
        return cls._attack_bonuses.get(id(target), 0)

    @classmethod
    def get_description(cls) -> str:
        return (
            "HoTs grant shields equal to 50% of the heal and +5% effect resistance for one turn. "
            "Cleansing a DoT heals 5% of max HP and gives Lady Light +2% attack per cleanse."
        )
