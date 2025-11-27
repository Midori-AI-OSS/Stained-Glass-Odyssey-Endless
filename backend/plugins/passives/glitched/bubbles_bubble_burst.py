from dataclasses import dataclass
from typing import TYPE_CHECKING

from plugins.passives.normal.bubbles_bubble_burst import BubblesBubbleBurst

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class BubblesBubbleBurstGlitched(BubblesBubbleBurst):
    """[GLITCHED] Bubbles' Bubble Burst - element switching with doubled burst bonuses.

    This glitched variant doubles the permanent attack buff from bursts (20% instead of 10%
    before soft cap, 10% instead of 5% after), resulting in much faster damage scaling
    while maintaining the same bubble stacking and element rotation mechanics.
    """
    plugin_type = "passive"
    id = "bubbles_bubble_burst_glitched"
    name = "Glitched Bubble Burst"
    trigger = ["turn_start", "hit_landed"]
    max_stacks = 20
    stack_display = "number"

    async def _trigger_bubble_burst(self, bubbles: "Stats", trigger_enemy: "Stats") -> None:
        """Trigger bubble burst with DOUBLED attack bonuses."""
        from autofighter.effects import EffectManager
        from autofighter.stat_effect import StatEffect

        bubbles_id = id(bubbles)
        trigger_enemy_id = id(trigger_enemy)

        # Reset bubble stacks for this enemy
        if bubbles_id in self._bubble_stacks and trigger_enemy_id in self._bubble_stacks[bubbles_id]:
            self._bubble_stacks[bubbles_id][trigger_enemy_id] = 0

        # Grant Bubbles permanent attack buff with DOUBLED values
        current_stacks = len([e for e in bubbles._active_effects if 'burst_bonus' in e.name])

        # Determine buff strength based on current stacks (soft cap at 20)
        if current_stacks >= 20:
            # Past soft cap: DOUBLED reduced effectiveness (10% instead of 5%)
            attack_buff_multiplier = 0.10  # Doubled from 0.05
        else:
            # DOUBLED normal effectiveness (20% instead of 10%)
            attack_buff_multiplier = 0.20  # Doubled from 0.1

        attack_buff = StatEffect(
            name=f"{self.id}_burst_bonus_{current_stacks}",
            stat_modifiers={"atk": int(bubbles.atk * attack_buff_multiplier)},
            duration=-1,  # Permanent
            source=self.id,
        )
        bubbles.add_effect(attack_buff)

        # Damage all combatants (unchanged)
        allies = list(getattr(bubbles, "allies", []))
        enemies = list(getattr(bubbles, "enemies", []))
        if bubbles not in allies:
            allies.insert(0, bubbles)
        damage = int(getattr(bubbles, "atk", 0))
        for combatant in allies + enemies:
            await combatant.apply_damage(damage, attacker=bubbles, action_name="Glitched Bubble Burst")
            if combatant in enemies:
                mgr = getattr(combatant, "effect_manager", None)
                if mgr is None:
                    mgr = EffectManager(combatant)
                    combatant.effect_manager = mgr
                await mgr.maybe_inflict_dot(bubbles, damage, turns=2)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[GLITCHED] Changes element randomly each turn. Hitting a foe adds a bubble; "
            "at 3 stacks bubbles burst for area damage and give +20% attack (doubled) "
            "per burst (+10% after 20 stacks, also doubled)."
        )
