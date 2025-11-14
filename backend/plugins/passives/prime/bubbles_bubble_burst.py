from dataclasses import dataclass

from plugins.passives.normal.bubbles_bubble_burst import BubblesBubbleBurst


@dataclass
class BubblesBubbleBurstPrime(BubblesBubbleBurst):
    """Prime variant of Bubbles' Bubble Burst with massive area damage."""
    plugin_type = "passive"
    id = "bubbles_bubble_burst_prime"
    name = "Prime Bubble Burst"
    trigger = ["turn_start", "hit_landed"]
    max_stacks = 50  # Prime: Massive soft cap increase
    stack_display = "number"

    async def on_hit_enemy(self, bubbles, enemy) -> None:
        """Apply bubble stack with Prime mechanic - only needs 2 stacks instead of 3."""
        bubbles_id = id(bubbles)
        enemy_id = id(enemy)

        # Initialize tracking
        if bubbles_id not in self._bubble_stacks:
            self._bubble_stacks[bubbles_id] = {}
        if enemy_id not in self._bubble_stacks[bubbles_id]:
            self._bubble_stacks[bubbles_id][enemy_id] = 0

        # Add bubble stack
        self._bubble_stacks[bubbles_id][enemy_id] += 1

        # Prime: Only needs 2 stacks for burst instead of 3
        if self._bubble_stacks[bubbles_id][enemy_id] >= 2:
            await self._trigger_bubble_burst(bubbles, enemy)

    async def _trigger_bubble_burst(self, bubbles, trigger_enemy) -> None:
        """Trigger Prime bubble burst area damage and effects."""
        from autofighter.effects import EffectManager
        from autofighter.stat_effect import StatEffect

        bubbles_id = id(bubbles)
        trigger_enemy_id = id(trigger_enemy)

        # Reset bubble stacks for this enemy
        if bubbles_id in self._bubble_stacks and trigger_enemy_id in self._bubble_stacks[bubbles_id]:
            self._bubble_stacks[bubbles_id][trigger_enemy_id] = 0

        # Prime: Grant permanent attack buff with much higher soft cap
        current_stacks = len([e for e in bubbles._active_effects if 'burst_bonus' in e.name])

        # Prime: Determine buff strength (soft cap at 50 instead of 20)
        if current_stacks >= 50:
            # Past soft cap: reduced effectiveness (12% instead of 5%)
            attack_buff_multiplier = 0.12
        else:
            # Prime: Massive normal effectiveness (25% from 10%)
            attack_buff_multiplier = 0.25

        attack_buff = StatEffect(
            name=f"{self.id}_burst_bonus_{current_stacks}",
            stat_modifiers={
                "atk": int(bubbles.atk * attack_buff_multiplier),
                "crit_rate": 0.02,  # Prime: Added crit rate bonus
            },
            duration=-1,
            source=self.id,
        )
        bubbles.add_effect(attack_buff)

        # Prime: Massive damage (2.5x base)
        allies = list(getattr(bubbles, "allies", []))
        enemies = list(getattr(bubbles, "enemies", []))
        if bubbles not in allies:
            allies.insert(0, bubbles)
        damage = int(getattr(bubbles, "atk", 0) * 2.5)
        for combatant in allies + enemies:
            await combatant.apply_damage(damage, attacker=bubbles, action_name="Prime Bubble Burst")
            if combatant in enemies:
                mgr = getattr(combatant, "effect_manager", None)
                if mgr is None:
                    mgr = EffectManager(combatant)
                    combatant.effect_manager = mgr
                # Prime: 4 turn DoT
                await mgr.maybe_inflict_dot(bubbles, damage, turns=4)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[PRIME] Changes element randomly each turn. Hitting a foe adds a bubble; "
            "at only 2 stacks bubbles burst for massive area damage (2.5x) and give +25% attack and +2% crit "
            "per burst (+12% attack after 50 stacks). DoTs last 4 turns."
        )
