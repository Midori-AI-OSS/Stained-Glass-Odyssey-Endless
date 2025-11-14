from dataclasses import dataclass

from plugins.passives.normal.bubbles_bubble_burst import BubblesBubbleBurst


@dataclass
class BubblesBubbleBurstBoss(BubblesBubbleBurst):
    """Boss variant of Bubbles' Bubble Burst with enhanced area damage."""
    plugin_type = "passive"
    id = "bubbles_bubble_burst_boss"
    name = "Bubble Burst (Boss)"
    trigger = ["turn_start", "hit_landed"]
    max_stacks = 30  # Boss: Increased soft cap from 20
    stack_display = "number"

    async def _trigger_bubble_burst(self, bubbles, trigger_enemy) -> None:
        """Trigger Boss bubble burst area damage and effects."""
        from autofighter.effects import EffectManager
        from autofighter.stat_effect import StatEffect

        bubbles_id = id(bubbles)
        trigger_enemy_id = id(trigger_enemy)

        # Reset bubble stacks for this enemy
        if bubbles_id in self._bubble_stacks and trigger_enemy_id in self._bubble_stacks[bubbles_id]:
            self._bubble_stacks[bubbles_id][trigger_enemy_id] = 0

        # Boss: Grant permanent attack buff with higher soft cap
        current_stacks = len([e for e in bubbles._active_effects if 'burst_bonus' in e.name])

        # Boss: Determine buff strength (soft cap at 30 instead of 20)
        if current_stacks >= 30:
            # Past soft cap: reduced effectiveness (8% instead of 5%)
            attack_buff_multiplier = 0.08
        else:
            # Boss: Normal effectiveness increased to 15% (from 10%)
            attack_buff_multiplier = 0.15

        attack_buff = StatEffect(
            name=f"{self.id}_burst_bonus_{current_stacks}",
            stat_modifiers={"atk": int(bubbles.atk * attack_buff_multiplier)},
            duration=-1,
            source=self.id,
        )
        bubbles.add_effect(attack_buff)

        # Boss: Increased damage (1.5x base)
        allies = list(getattr(bubbles, "allies", []))
        enemies = list(getattr(bubbles, "enemies", []))
        if bubbles not in allies:
            allies.insert(0, bubbles)
        damage = int(getattr(bubbles, "atk", 0) * 1.5)
        for combatant in allies + enemies:
            await combatant.apply_damage(damage, attacker=bubbles, action_name="Bubble Burst")
            if combatant in enemies:
                mgr = getattr(combatant, "effect_manager", None)
                if mgr is None:
                    mgr = EffectManager(combatant)
                    combatant.effect_manager = mgr
                # Boss: 3 turn DoT instead of 2
                await mgr.maybe_inflict_dot(bubbles, damage, turns=3)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[BOSS] Changes element randomly each turn. Hitting a foe adds a bubble; "
            "at 3 stacks bubbles burst for enhanced area damage (1.5x) and give +15% attack "
            "per burst (+8% after 30 stacks). DoTs last 3 turns."
        )
