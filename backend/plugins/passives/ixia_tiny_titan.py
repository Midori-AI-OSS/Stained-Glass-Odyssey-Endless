from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import ClassVar

from autofighter.stat_effect import StatEffect

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class IxiaTinyTitan:
    """Ixia's Tiny Titan passive - 4x Vitality HP gain and 500% Vitality to attack conversion."""
    plugin_type = "passive"
    id = "ixia_tiny_titan"
    name = "Tiny Titan"
    trigger = "damage_taken"  # Triggers when Ixia takes damage to increase Vitality
    max_stacks = 1  # Only one instance per character
    stack_display = "spinner"

    # Class-level tracking of accumulated Vitality bonuses
    _vitality_bonuses: ClassVar[dict[int, float]] = {}

    async def apply(self, target: "Stats") -> None:
        """Apply Ixia's Tiny Titan mechanics."""
        entity_id = id(target)

        # Initialize vitality bonus tracking if not present
        if entity_id not in self._vitality_bonuses:
            self._vitality_bonuses[entity_id] = 0.0

        # When hit, increase Vitality by 0.01 for the rest of battle
        self._vitality_bonuses[entity_id] += 0.01

        # Compute effective stacks from accumulated vitality bonus (each +0.01 = 1 stack)
        stacks = int(round(self._vitality_bonuses[entity_id] * 100))

        # Apply 4x HP gain from Vitality based on BASE max_hp to avoid compounding
        try:
            base_max_hp = int(getattr(target, 'get_base_stat')('max_hp'))
        except Exception:
            base_max_hp = int(getattr(target, 'max_hp', 0))
        vitality_hp_bonus = int(self._vitality_bonuses[entity_id] * 4 * base_max_hp)

        hp_effect = StatEffect(
            name=f"{self.id}_vitality_hp",
            stat_modifiers={"max_hp": vitality_hp_bonus},
            duration=-1,  # Permanent for rest of battle
            source=self.id,
        )
        target.add_effect(hp_effect)

        # Convert 500% of current Vitality into attack based on BASE atk to avoid compounding
        try:
            base_atk = int(getattr(target, 'get_base_stat')('atk'))
        except Exception:
            base_atk = int(getattr(target, 'atk', 0))
        vitality_attack_bonus = int(self._vitality_bonuses[entity_id] * 5 * base_atk)

        attack_effect = StatEffect(
            name=f"{self.id}_vitality_attack",
            stat_modifiers={"atk": vitality_attack_bonus},
            duration=-1,  # Permanent for rest of battle
            source=self.id,
        )
        target.add_effect(attack_effect)

        # Apply damage reduction from Vitality bonus
        damage_reduction = self._vitality_bonuses[entity_id] * 0.05  # 5% per 0.01 Vitality
        mitigation_effect = StatEffect(
            name=f"{self.id}_vitality_mitigation",
            stat_modifiers={"mitigation": damage_reduction},
            duration=-1,  # Permanent for rest of battle
            source=self.id,
        )
        target.add_effect(mitigation_effect)

        # Per-stack defense penalty: -25 DEF per stack, clamped so DEF never goes below 10
        try:
            base_def = int(getattr(target, 'get_base_stat')('defense'))
        except Exception:
            base_def = int(getattr(target, 'defense', 0))
        max_penalty = max(base_def - 10, 0)
        desired_penalty = 25 * max(stacks, 0)
        penalty = min(desired_penalty, max_penalty)
        defense_effect = StatEffect(
            name=f"{self.id}_defense_penalty",
            stat_modifiers={"defense": -int(penalty)},
            duration=-1,
            source=self.id,
        )
        target.add_effect(defense_effect)

    async def on_turn_end(self, target: "Stats") -> None:
        """Apply minor HoT each turn while Vitality bonus is active."""
        entity_id = id(target)
        vitality_bonus = self._vitality_bonuses.get(entity_id, 0.0)

        if vitality_bonus > 0:
            # Minor HoT based on Vitality bonus
            hot_amount = int(vitality_bonus * target.max_hp * 0.02)  # 2% of max HP per 0.01 Vitality
            if hot_amount > 0:
                target.hp = min(target.max_hp, target.hp + hot_amount)

    @classmethod
    def get_vitality_bonus(cls, target: "Stats") -> float:
        """Get current Vitality bonus for an entity."""
        return cls._vitality_bonuses.get(id(target), 0.0)

    @classmethod
    def get_description(cls) -> str:
        return (
            "Taking damage increases Vitality by 0.01 permanently. "
            "Each 0.01 Vitality grants 4x HP gain, converts 500% of Vitality to attack, "
            "adds 5% mitigation, and reduces defense by 25."
        )
