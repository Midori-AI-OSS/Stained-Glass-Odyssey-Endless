from dataclasses import dataclass
from typing import TYPE_CHECKING

from plugins.passives.normal.bubbles_bubble_burst import BubblesBubbleBurst

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class BubblesBubbleBurstBoss(BubblesBubbleBurst):
    """Boss Bubble Burst with heavier snowballing per detonation."""

    plugin_type = "passive"
    id = "bubbles_bubble_burst_boss"
    name = "Bubble Burst (Boss)"
    trigger = ["turn_start", "hit_landed"]
    max_stacks = 20
    stack_display = "number"

    async def _trigger_bubble_burst(self, bubbles: "Stats", trigger_enemy: "Stats") -> None:
        """Detonate bubbles with 1.5× permanent attack gain per burst."""

        from autofighter.effects import EffectManager
        from autofighter.stat_effect import StatEffect

        bubbles_id = id(bubbles)
        trigger_enemy_id = id(trigger_enemy)

        if bubbles_id in self._bubble_stacks and trigger_enemy_id in self._bubble_stacks[bubbles_id]:
            self._bubble_stacks[bubbles_id][trigger_enemy_id] = 0

        current_stacks = len([e for e in bubbles._active_effects if "burst_bonus" in e.name])
        if current_stacks >= 20:
            attack_buff_multiplier = 0.075
        else:
            attack_buff_multiplier = 0.15

        attack_buff = StatEffect(
            name=f"{self.id}_burst_bonus_{current_stacks}",
            stat_modifiers={"atk": int(bubbles.atk * attack_buff_multiplier)},
            duration=-1,
            source=self.id,
        )
        bubbles.add_effect(attack_buff)

        allies = list(getattr(bubbles, "allies", []))
        enemies = list(getattr(bubbles, "enemies", []))
        if bubbles not in allies:
            allies.insert(0, bubbles)
        damage = int(getattr(bubbles, "atk", 0))
        for combatant in allies + enemies:
            await combatant.apply_damage(
                damage,
                attacker=bubbles,
                action_name="Boss Bubble Burst",
            )
            if combatant in enemies:
                mgr = getattr(combatant, "effect_manager", None)
                if mgr is None:
                    mgr = EffectManager(combatant)
                    combatant.effect_manager = mgr
                await mgr.maybe_inflict_dot(bubbles, damage, turns=2)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[BOSS] Rotates elements every turn. Landing three hits on a foe detonates bubbles for area damage and +15% attack per burst (+7.5% beyond 20 stacks)."
        )
