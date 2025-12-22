from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from autofighter.stat_effect import StatEffect

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class IxiaTinyTitanPrime:
    """Prime variant of Ixia's Tiny Titan with massive scaling.

    Prime Ixia has extreme conversion rates and healing, representing
    the pinnacle of the glass cannon design with minimal defense penalty.
    """
    plugin_type = "passive"
    id = "ixia_tiny_titan_prime"
    name = "Prime Tiny Titan"
    trigger = "damage_taken"
    max_stacks = 1
    stack_display = "spinner"

    # Class-level tracking of accumulated Vitality bonuses
    _vitality_bonuses: ClassVar[dict[int, float]] = {}

    async def apply(self, target: "Stats") -> None:
        """Apply prime-tier Tiny Titan mechanics."""
        entity_id = id(target)

        if entity_id not in self._vitality_bonuses:
            self._vitality_bonuses[entity_id] = 0.0

        # Prime: Faster Vitality gain (0.015 per hit)
        self._vitality_bonuses[entity_id] += 0.015

        stacks = int(round(self._vitality_bonuses[entity_id] * 100))

        # Prime: Massive HP multiplier (10x instead of 4x)
        try:
            base_max_hp = int(getattr(target, 'get_base_stat')('max_hp'))
        except Exception:
            base_max_hp = int(getattr(target, 'max_hp', 0))
        vitality_hp_bonus = int(self._vitality_bonuses[entity_id] * 10 * base_max_hp)

        hp_effect = StatEffect(
            name=f"{self.id}_vitality_hp",
            stat_modifiers={"max_hp": vitality_hp_bonus},
            duration=-1,
            source=self.id,
        )
        target.add_effect(hp_effect)

        # Prime: Extreme attack conversion (1250% instead of 500%)
        try:
            base_atk = int(getattr(target, 'get_base_stat')('atk'))
        except Exception:
            base_atk = int(getattr(target, 'atk', 0))
        vitality_attack_bonus = int(self._vitality_bonuses[entity_id] * 12.5 * base_atk)

        attack_effect = StatEffect(
            name=f"{self.id}_vitality_attack",
            stat_modifiers={"atk": vitality_attack_bonus},
            duration=-1,
            source=self.id,
        )
        target.add_effect(attack_effect)

        # Prime: Enhanced mitigation (7.5% instead of 5%)
        damage_reduction = self._vitality_bonuses[entity_id] * 0.075
        mitigation_effect = StatEffect(
            name=f"{self.id}_vitality_mitigation",
            stat_modifiers={"mitigation": damage_reduction},
            duration=-1,
            source=self.id,
        )
        target.add_effect(mitigation_effect)

        # Prime: Minimal defense penalty (-10 instead of -25)
        try:
            base_def = int(getattr(target, 'get_base_stat')('defense'))
        except Exception:
            base_def = int(getattr(target, 'defense', 0))
        max_penalty = max(base_def - 10, 0)
        desired_penalty = 10 * max(stacks, 0)
        penalty = min(desired_penalty, max_penalty)
        defense_effect = StatEffect(
            name=f"{self.id}_defense_penalty",
            stat_modifiers={"defense": -int(penalty)},
            duration=-1,
            source=self.id,
        )
        target.add_effect(defense_effect)

    async def on_turn_end(self, target: "Stats") -> None:
        """Apply enhanced HoT each turn."""
        entity_id = id(target)
        vitality_bonus = self._vitality_bonuses.get(entity_id, 0.0)

        if vitality_bonus > 0:
            # Prime: Enhanced HoT (3% instead of 2%)
            hot_amount = int(vitality_bonus * target.max_hp * 0.03)
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
            "[PRIME] Taking damage increases Vitality by 0.015 permanently (enhanced). "
            "Each 0.01 Vitality grants 10x HP gain, converts 1250% of Vitality to attack, "
            "adds 7.5% mitigation, and reduces defense by only 10 (minimal penalty)."
        )

