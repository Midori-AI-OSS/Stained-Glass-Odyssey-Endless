from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from autofighter.stat_effect import StatEffect

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class IxiaTinyTitanBoss:
    """Boss variant of Ixia's Tiny Titan with enhanced multipliers.

    Boss Ixia has higher conversion rates and reduced defense penalty,
    making her a more formidable opponent with better scaling.
    """
    plugin_type = "passive"
    id = "ixia_tiny_titan_boss"
    name = "Tiny Titan (Boss)"
    trigger = "damage_taken"
    max_stacks = 1
    stack_display = "spinner"

    # Class-level tracking of accumulated Vitality bonuses
    _vitality_bonuses: ClassVar[dict[int, float]] = {}

    async def apply(self, target: "Stats") -> None:
        """Apply boss-tier Tiny Titan mechanics."""
        entity_id = id(target)

        if entity_id not in self._vitality_bonuses:
            self._vitality_bonuses[entity_id] = 0.0

        # Standard Vitality gain
        self._vitality_bonuses[entity_id] += 0.01

        stacks = int(round(self._vitality_bonuses[entity_id] * 100))

        # Boss: Enhanced HP multiplier (6x instead of 4x)
        try:
            base_max_hp = int(getattr(target, 'get_base_stat')('max_hp'))
        except Exception:
            base_max_hp = int(getattr(target, 'max_hp', 0))
        vitality_hp_bonus = int(self._vitality_bonuses[entity_id] * 6 * base_max_hp)

        hp_effect = StatEffect(
            name=f"{self.id}_vitality_hp",
            stat_modifiers={"max_hp": vitality_hp_bonus},
            duration=-1,
            source=self.id,
        )
        target.add_effect(hp_effect)

        # Boss: Enhanced attack conversion (750% instead of 500%)
        try:
            base_atk = int(getattr(target, 'get_base_stat')('atk'))
        except Exception:
            base_atk = int(getattr(target, 'atk', 0))
        vitality_attack_bonus = int(self._vitality_bonuses[entity_id] * 7.5 * base_atk)

        attack_effect = StatEffect(
            name=f"{self.id}_vitality_attack",
            stat_modifiers={"atk": vitality_attack_bonus},
            duration=-1,
            source=self.id,
        )
        target.add_effect(attack_effect)

        # Same mitigation as base
        damage_reduction = self._vitality_bonuses[entity_id] * 0.05
        mitigation_effect = StatEffect(
            name=f"{self.id}_vitality_mitigation",
            stat_modifiers={"mitigation": damage_reduction},
            duration=-1,
            source=self.id,
        )
        target.add_effect(mitigation_effect)

        # Boss: Reduced defense penalty (-15 instead of -25)
        try:
            base_def = int(getattr(target, 'get_base_stat')('defense'))
        except Exception:
            base_def = int(getattr(target, 'defense', 0))
        max_penalty = max(base_def - 10, 0)
        desired_penalty = 15 * max(stacks, 0)
        penalty = min(desired_penalty, max_penalty)
        defense_effect = StatEffect(
            name=f"{self.id}_defense_penalty",
            stat_modifiers={"defense": -int(penalty)},
            duration=-1,
            source=self.id,
        )
        target.add_effect(defense_effect)

    async def on_turn_end(self, target: "Stats") -> None:
        """Apply minor HoT each turn."""
        entity_id = id(target)
        vitality_bonus = self._vitality_bonuses.get(entity_id, 0.0)

        if vitality_bonus > 0:
            hot_amount = int(vitality_bonus * target.max_hp * 0.02)
            if hot_amount > 0:
                await target.apply_healing(
                    hot_amount,
                    healer=target,
                    source_type="hot",
                    source_name=self.id,
                )

    @classmethod
    def get_vitality_bonus(cls, target: "Stats") -> float:
        """Get current Vitality bonus for an entity."""
        return cls._vitality_bonuses.get(id(target), 0.0)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[BOSS] Taking damage increases Vitality by 0.01 permanently. "
            "Each 0.01 Vitality grants 6x HP gain, converts 750% of Vitality to attack, "
            "adds 5% mitigation, and reduces defense by 15 (reduced penalty)."
        )

