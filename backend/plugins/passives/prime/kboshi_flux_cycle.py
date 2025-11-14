from dataclasses import dataclass

from plugins.passives.normal.kboshi_flux_cycle import KboshiFluxCycle


@dataclass
class KboshiFluxCyclePrime(KboshiFluxCycle):
    """Prime variant of Kboshi's Flux Cycle with powerful enhancements."""
    plugin_type = "passive"
    id = "kboshi_flux_cycle_prime"
    name = "Prime Flux Cycle"
    trigger = "turn_start"
    stack_display = "pips"

    async def apply(self, target) -> None:
        """Apply Prime Flux Cycle element switching mechanics for Kboshi."""
        import random

        from autofighter.effects import HealingOverTime
        from autofighter.stat_effect import StatEffect

        entity_id = id(target)

        # Initialize tracking if needed
        if entity_id not in self._damage_stacks:
            self._damage_stacks[entity_id] = 0
            self._hot_stacks[entity_id] = 0

        # Prime: Very high chance to switch (95% instead of 80%)
        if random.random() < 0.95:
            # Get current damage type
            current_type_id = getattr(target.damage_type, 'id', 'Dark')

            # Filter out current type
            available_types = [dt for dt in self._damage_types
                             if dt().id != current_type_id]

            if not available_types:
                available_types = self._damage_types

            # Select random new damage type
            new_damage_type_class = random.choice(available_types)
            new_damage_type = new_damage_type_class()

            # Actually switch the damage type
            target.damage_type = new_damage_type

            # Element successfully changed - remove accumulated stacks
            if self._damage_stacks[entity_id] > 0 or self._hot_stacks[entity_id] > 0:
                stacks = self._damage_stacks[entity_id]

                # Remove existing bonus effects
                target.remove_effect_by_source(self.id)

                # Clear any active HoTs
                if hasattr(target, "effect_manager") and target.effect_manager:
                    await target.effect_manager.remove_hots(
                        lambda hot: hot.id.startswith(f"{self.id}_hot_{entity_id}")
                    )

                # Reset stacks
                self._damage_stacks[entity_id] = 0
                self._hot_stacks[entity_id] = 0

                # Prime: Apply massive mitigation debuff (-5% per stack) and ATK debuff
                if stacks > 0:
                    mitigation = stacks * -0.05
                    atk_debuff = -int(stacks * 20)
                    for foe in getattr(target, "enemies", []):
                        debuff = StatEffect(
                            name=f"{self.id}_mitigation_debuff",
                            stat_modifiers={
                                "mitigation": mitigation,
                                "atk": atk_debuff,  # Prime: Added ATK debuff
                            },
                            duration=2,  # Prime: 2 turns instead of 1
                            source=self.id,
                        )
                        foe.add_effect(debuff)
        else:
            # Element failed to change - gain massive bonuses
            self._damage_stacks[entity_id] += 1
            self._hot_stacks[entity_id] += 1

            # Prime: Apply 50% damage bonus per stack
            base_attack = (
                int(target.get_base_stat("atk"))
                if hasattr(target, "get_base_stat")
                else int(getattr(target, "_base_atk", target.atk))
            )
            bonus_amount = max(1, int(base_attack * 0.5))
            damage_bonus = StatEffect(
                name=f"{self.id}_damage_bonus_{self._damage_stacks[entity_id]}",
                stat_modifiers={
                    "atk": bonus_amount,
                    "crit_rate": 0.05,  # Prime: Added crit rate bonus
                },
                duration=-1,
                source=self.id,
            )
            target.add_effect(damage_bonus)

            # Prime: Apply massive HoT - heal 10% max HP per stack
            heal_amount = max(1, int(target.max_hp * 0.10 * self._hot_stacks[entity_id]))
            hot = HealingOverTime(
                name=f"Flux Cycle HoT (Stack {self._hot_stacks[entity_id]})",
                healing=heal_amount,
                turns=2,  # Prime: 2 turn duration
                id=f"{self.id}_hot_{entity_id}_{self._hot_stacks[entity_id]}",
                source=target,
            )
            # Add HoT through effect manager
            mgr = getattr(target, "effect_manager", None)
            if mgr is None:
                from autofighter.effects import EffectManager

                mgr = EffectManager(target)
                target.effect_manager = mgr

            await mgr.add_hot(hot)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[PRIME] 95% chance each turn to switch to a new element. "
            "Failing to switch grants a 50% attack bonus, +5% crit, and a massive HoT for 2 turns; "
            "switching clears stacks and applies -5% mitigation and -20 ATK to foes per stack for 2 turns."
        )
