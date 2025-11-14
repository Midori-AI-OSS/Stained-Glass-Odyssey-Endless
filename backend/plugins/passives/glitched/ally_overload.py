from dataclasses import dataclass

from plugins.passives.normal.ally_overload import AllyOverload


@dataclass
class AllyOverloadGlitched(AllyOverload):
    """Glitched variant of Ally's Overload with doubled charge and unstable mechanics."""
    plugin_type = "passive"
    id = "ally_overload_glitched"
    name = "Glitched Overload"
    trigger = "action_taken"
    max_stacks = 240  # Glitched: Doubled soft cap from 120
    stack_display = "number"

    async def apply(self, target) -> None:
        """Apply Glitched Ally's twin dagger and overload mechanics with doubled values."""
        entity_id = id(target)

        if entity_id not in self._overload_charge:
            self._overload_charge[entity_id] = 0
            self._overload_active[entity_id] = False

        # Twin daggers - always grants two attacks per action
        if not self._overload_active[entity_id]:
            target.actions_per_turn = 2

        # Glitched: Build 20 Overload charge per pair of strikes (doubled from 10)
        base_charge_gain = 20

        # Soft cap: past 240, gain charge at reduced rate
        current_charge = self._overload_charge[entity_id]
        if current_charge > 240:
            charge_gain = base_charge_gain * 0.5
        else:
            charge_gain = base_charge_gain

        self._overload_charge[entity_id] += charge_gain

        # Glitched: Check if Overload can be triggered (100+ charge)
        current_charge = self._overload_charge[entity_id]
        if current_charge >= 100 and not self._overload_active[entity_id]:
            await self._activate_overload(target)

        # Handle charge decay when stance is inactive - Glitched: Doubled decay
        if not self._overload_active[entity_id]:
            self._overload_charge[entity_id] = max(0, current_charge - 10)  # Glitched: 10 instead of 5

    async def _activate_overload(self, target) -> None:
        """Activate Glitched Overload stance with doubled bonuses."""
        from autofighter.stat_effect import StatEffect

        entity_id = id(target)
        self._overload_active[entity_id] = True

        # Double attack count
        target.actions_per_turn = 4

        # Glitched: +60% damage bonus (doubled from 30%)
        damage_bonus = StatEffect(
            name=f"{self.id}_damage_bonus",
            stat_modifiers={"atk": int(target.atk * 0.6)},
            duration=-1,
            source=self.id,
        )
        target.add_effect(damage_bonus)

        # Glitched: +80% damage taken vulnerability (doubled from 40%)
        damage_vulnerability = StatEffect(
            name=f"{self.id}_damage_vulnerability",
            stat_modifiers={"mitigation": -0.8},
            duration=-1,
            source=self.id,
        )
        target.add_effect(damage_vulnerability)

        # Remove existing HoTs and block new applications
        em = getattr(target, "effect_manager", None)
        if em is not None:
            em.hots.clear()
            target.hots.clear()

            async def _block_hot(self_em, *_: object, **__: object) -> None:
                return None

            self._add_hot_backup[entity_id] = em.add_hot
            em.add_hot = _block_hot.__get__(em, type(em))

        from autofighter.stats import BUS

        existing_handler = self._battle_end_handlers.pop(entity_id, None)
        if existing_handler is not None:
            BUS.unsubscribe("battle_end", existing_handler)

        async def _on_battle_end(*_: object, **__: object) -> None:
            BUS.unsubscribe("battle_end", _on_battle_end)
            self._battle_end_handlers.pop(entity_id, None)

            if self._overload_active.get(entity_id):
                await self._deactivate_overload(target)
                return

            original = self._add_hot_backup.pop(entity_id, None)
            if em is not None and original is not None:
                em.add_hot = original

        self._battle_end_handlers[entity_id] = _on_battle_end
        BUS.subscribe("battle_end", _on_battle_end)

        # Glitched: Cap recoverable HP at 40% of normal (doubled from 20%)
        max_recoverable_hp = int(target.max_hp * 0.4)
        hp_cap = StatEffect(
            name=f"{self.id}_hp_cap",
            stat_modifiers={"max_hp": max_recoverable_hp - target.max_hp},
            duration=-1,
            source=self.id,
        )
        target.add_effect(hp_cap)

    async def on_turn_end(self, target) -> None:
        """Handle end-of-turn Glitched Overload mechanics."""
        entity_id = id(target)

        if entity_id not in self._overload_charge:
            self._overload_charge[entity_id] = 0
            self._overload_active[entity_id] = False

        if self._overload_active[entity_id]:
            # Glitched: Drain 40 charge per turn while active (doubled from 20)
            self._overload_charge[entity_id] = max(0, self._overload_charge[entity_id] - 40)

            if self._overload_charge[entity_id] <= 0:
                await self._deactivate_overload(target)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[GLITCHED] Twin daggers grant two attacks per action and build 20 charge (doubled), decaying by 10 when inactive. "
            "At 100 charge, Overload activates: attack count doubles again, damage +60%, and damage taken +80% (doubled), "
            "draining 40 charge per turn. Charge gain halves above 240."
        )
