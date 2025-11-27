from dataclasses import dataclass
from typing import TYPE_CHECKING

from autofighter.effects import EffectManager
from autofighter.stat_effect import StatEffect
from plugins.passives.normal.bubbles_bubble_burst import BubblesBubbleBurst

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class BubblesBubbleBurstPrime(BubblesBubbleBurst):
    """[PRIME] Bubbles' bubbles burst harder and leave shields behind."""

    plugin_type = "passive"
    id = "bubbles_bubble_burst_prime"
    name = "Prime Bubble Burst"
    trigger = ["turn_start", "hit_landed"]
    max_stacks = 30
    stack_display = "number"

    async def on_hit_enemy(self, bubbles: "Stats", enemy: "Stats") -> None:
        await super().on_hit_enemy(bubbles, enemy)

    async def _trigger_bubble_burst(self, bubbles: "Stats", trigger_enemy: "Stats") -> None:
        await super()._trigger_bubble_burst(bubbles, trigger_enemy)

        shield_amount = max(1, int(getattr(bubbles, "atk", 0) * 0.5))
        shield_effect = StatEffect(
            name=f"{self.id}_shield",
            stat_modifiers={"shield": shield_amount},
            duration=2,
            source=self.id,
        )

        allies = list(getattr(bubbles, "allies", []))
        if bubbles not in allies:
            allies.append(bubbles)
        for ally in allies:
            ally.add_effect(shield_effect)

        attack_buff_stacks = len([e for e in bubbles._active_effects if 'burst_bonus' in e.name])
        bonus_multiplier = 0.15 if attack_buff_stacks < 20 else 0.07
        bonus = StatEffect(
            name=f"{self.id}_overflow_{attack_buff_stacks}",
            stat_modifiers={"atk": int(getattr(bubbles, "atk", 0) * bonus_multiplier)},
            duration=-1,
            source=self.id,
        )
        bubbles.add_effect(bonus)

        mgr = getattr(trigger_enemy, "effect_manager", None) or EffectManager(trigger_enemy)
        trigger_enemy.effect_manager = mgr
        await mgr.maybe_inflict_dot(bubbles, getattr(bubbles, "atk", 0) // 2, turns=3)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[PRIME] Bubble bursts now grant shields to the team and add +15% attack per burst (7% after 20). "
            "Burst explosions still roll random elements and inflict heavier DoTs on enemies caught in the splash."
        )

