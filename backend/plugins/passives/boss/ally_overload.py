from dataclasses import dataclass

from plugins.passives.normal.ally_overload import AllyOverload


@dataclass
class AllyOverloadBoss(AllyOverload):
    """Boss variant of Ally's Overload with enhanced charge mechanics."""
    plugin_type = "passive"
    id = "ally_overload_boss"
    name = "Overload (Boss)"
    trigger = "action_taken"
    max_stacks = 180  # Boss: Increased soft cap from 120
    stack_display = "number"

    async def apply(self, target) -> None:
        """Apply Boss Ally's twin dagger and overload mechanics with enhanced values."""
        entity_id = id(target)

        # Initialize if not present
        if entity_id not in self._overload_charge:
            self._overload_charge[entity_id] = 0
            self._overload_active[entity_id] = False

        # Twin daggers - always grants two attacks per action
        if not self._overload_active[entity_id]:
            target.actions_per_turn = 2

        # Boss: Build 15 Overload charge per pair of strikes (increased from 10)
        base_charge_gain = 15

        # Soft cap: past 180, gain charge at reduced rate (50% effectiveness)
        current_charge = self._overload_charge[entity_id]
        if current_charge > 180:
            charge_gain = base_charge_gain * 0.5
        else:
            charge_gain = base_charge_gain

        self._overload_charge[entity_id] += charge_gain

        # Boss: Overload can be triggered at 80+ charge (reduced from 100)
        current_charge = self._overload_charge[entity_id]
        if current_charge >= 80 and not self._overload_active[entity_id]:
            await self._activate_overload(target)

        # Handle charge decay when stance is inactive - Boss: Slower decay
        if not self._overload_active[entity_id]:
            self._overload_charge[entity_id] = max(0, current_charge - 3)  # Boss: 3 instead of 5

    async def _activate_overload(self, target) -> None:
        """Activate Boss Overload stance with enhanced bonuses."""
        from autofighter.stat_effect import StatEffect

        entity_id = id(target)
        self._overload_active[entity_id] = True

        # Double attack count
        target.actions_per_turn = 4

        # Boss: +50% damage bonus (increased from 30%)
        damage_bonus = StatEffect(
            name=f"{self.id}_damage_bonus",
            stat_modifiers={"atk": int(target.atk * 0.5)},
            duration=-1,
            source=self.id,
        )
        target.add_effect(damage_bonus)

        # Boss: +30% damage taken vulnerability (reduced from 40%)
        damage_vulnerability = StatEffect(
            name=f"{self.id}_damage_vulnerability",
            stat_modifiers={"mitigation": -0.3},
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

        # Boss: Cap recoverable HP at 30% of normal (increased from 20%)
        max_recoverable_hp = int(target.max_hp * 0.3)
        hp_cap = StatEffect(
            name=f"{self.id}_hp_cap",
            stat_modifiers={"max_hp": max_recoverable_hp - target.max_hp},
            duration=-1,
            source=self.id,
        )
        target.add_effect(hp_cap)

    async def on_turn_end(self, target) -> None:
        """Handle end-of-turn Boss Overload mechanics."""
        entity_id = id(target)

        if entity_id not in self._overload_charge:
            self._overload_charge[entity_id] = 0
            self._overload_active[entity_id] = False

        if self._overload_active[entity_id]:
            # Boss: Drain 15 charge per turn while active (reduced from 20)
            self._overload_charge[entity_id] = max(0, self._overload_charge[entity_id] - 15)

            if self._overload_charge[entity_id] <= 0:
                await self._deactivate_overload(target)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[BOSS] Twin daggers grant two attacks per action and build 15 charge, decaying by 3 when inactive. "
            "At 80 charge, Overload activates: attack count doubles again, damage +50%, and damage taken +30%, "
            "draining 15 charge per turn. Charge gain halves above 180."
        )
