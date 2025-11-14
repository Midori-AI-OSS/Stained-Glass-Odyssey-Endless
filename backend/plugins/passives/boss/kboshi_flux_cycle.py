from dataclasses import dataclass

from plugins.passives.normal.kboshi_flux_cycle import KboshiFluxCycle


@dataclass
class KboshiFluxCycleBoss(KboshiFluxCycle):
    """Boss variant of Kboshi's Flux Cycle with enhanced mechanics."""
    plugin_type = "passive"
    id = "kboshi_flux_cycle_boss"
    name = "Flux Cycle (Boss)"
    trigger = "turn_start"
    stack_display = "pips"

    async def apply(self, target) -> None:
        """Apply Boss Flux Cycle element switching mechanics for Kboshi."""
        import random

        from autofighter.effects import HealingOverTime
        from autofighter.stat_effect import StatEffect

        entity_id = id(target)

        # Initialize tracking if needed
        if entity_id not in self._damage_stacks:
            self._damage_stacks[entity_id] = 0
            self._hot_stacks[entity_id] = 0

        # Boss: Higher chance to switch (90% instead of 80%)
        if random.random() < 0.9:
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

                # Boss: Apply stronger mitigation debuff (-3% per stack instead of -2%)
                if stacks > 0:
                    mitigation = stacks * -0.03
                    for foe in getattr(target, "enemies", []):
                        debuff = StatEffect(
                            name=f"{self.id}_mitigation_debuff",
                            stat_modifiers={"mitigation": mitigation},
                            duration=1,
                            source=self.id,
                        )
                        foe.add_effect(debuff)
        else:
            # Element failed to change - gain damage bonus and HoT
            self._damage_stacks[entity_id] += 1
            self._hot_stacks[entity_id] += 1

            # Boss: Apply 30% damage bonus per stack (increased from 20%)
            base_attack = (
                int(target.get_base_stat("atk"))
                if hasattr(target, "get_base_stat")
                else int(getattr(target, "_base_atk", target.atk))
            )
            bonus_amount = max(1, int(base_attack * 0.3))
            damage_bonus = StatEffect(
                name=f"{self.id}_damage_bonus_{self._damage_stacks[entity_id]}",
                stat_modifiers={"atk": bonus_amount},
                duration=-1,
                source=self.id,
            )
            target.add_effect(damage_bonus)

            # Boss: Apply larger HoT - heal 7% max HP per stack (increased from 5%)
            heal_amount = max(1, int(target.max_hp * 0.07 * self._hot_stacks[entity_id]))
            hot = HealingOverTime(
                name=f"Flux Cycle HoT (Stack {self._hot_stacks[entity_id]})",
                healing=heal_amount,
                turns=1,
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
            "[BOSS] 90% chance each turn to switch to a new element. "
            "Failing to switch grants a 30% attack bonus and a larger HoT for that turn; "
            "switching clears stacks and applies -3% mitigation to foes per stack."
        )
