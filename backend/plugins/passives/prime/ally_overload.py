from dataclasses import dataclass

from plugins.passives.normal.ally_overload import AllyOverload


@dataclass
class AllyOverloadPrime(AllyOverload):
    """Prime variant of Ally's Overload with massive charge mechanics."""
    plugin_type = "passive"
    id = "ally_overload_prime"
    name = "Prime Overload"
    trigger = "action_taken"
    max_stacks = 250  # Prime: Massive soft cap increase
    stack_display = "number"

    async def apply(self, target) -> None:
        """Apply Prime Ally's twin dagger and overload mechanics."""
        entity_id = id(target)

        if entity_id not in self._overload_charge:
            self._overload_charge[entity_id] = 0
            self._overload_active[entity_id] = False

        # Twin daggers - always grants two attacks per action
        if not self._overload_active[entity_id]:
            target.actions_per_turn = 2

        # Prime: Build 20 Overload charge per pair of strikes
        base_charge_gain = 20

        # Soft cap: past 250, gain charge at reduced rate
        current_charge = self._overload_charge[entity_id]
        if current_charge > 250:
            charge_gain = base_charge_gain * 0.5
        else:
            charge_gain = base_charge_gain

        self._overload_charge[entity_id] += charge_gain

        # Prime: Overload can be triggered at 60+ charge
        current_charge = self._overload_charge[entity_id]
        if current_charge >= 60 and not self._overload_active[entity_id]:
            await self._activate_overload(target)

        # Handle charge decay when stance is inactive - Prime: Very slow decay
        if not self._overload_active[entity_id]:
            self._overload_charge[entity_id] = max(0, current_charge - 2)

    async def _activate_overload(self, target) -> None:
        """Activate Prime Overload stance with massive bonuses."""
        from autofighter.stat_effect import StatEffect

        entity_id = id(target)
        self._overload_active[entity_id] = True

        # Prime: Triple attack count (6 attacks)
        target.actions_per_turn = 6

        # Prime: +75% damage bonus
        damage_bonus = StatEffect(
            name=f"{self.id}_damage_bonus",
            stat_modifiers={
                "atk": int(target.atk * 0.75),
                "crit_rate": 0.1,  # Prime: Added crit rate
            },
            duration=-1,
            source=self.id,
        )
        target.add_effect(damage_bonus)

        # Prime: +25% damage taken vulnerability (reduced from 40%)
        damage_vulnerability = StatEffect(
            name=f"{self.id}_damage_vulnerability",
            stat_modifiers={"mitigation": -0.25},
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

        # Prime: Cap recoverable HP at 40% of normal
        max_recoverable_hp = int(target.max_hp * 0.4)
        hp_cap = StatEffect(
            name=f"{self.id}_hp_cap",
            stat_modifiers={"max_hp": max_recoverable_hp - target.max_hp},
            duration=-1,
            source=self.id,
        )
        target.add_effect(hp_cap)

    async def on_turn_end(self, target) -> None:
        """Handle end-of-turn Prime Overload mechanics."""
        entity_id = id(target)

        if entity_id not in self._overload_charge:
            self._overload_charge[entity_id] = 0
            self._overload_active[entity_id] = False

        if self._overload_active[entity_id]:
            # Prime: Drain 10 charge per turn while active
            self._overload_charge[entity_id] = max(0, self._overload_charge[entity_id] - 10)

            if self._overload_charge[entity_id] <= 0:
                await self._deactivate_overload(target)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[PRIME] Twin daggers grant two attacks per action and build 20 charge, decaying by 2 when inactive. "
            "At 60 charge, Overload activates: attack count triples, damage +75%, +10% crit, and damage taken +25%, "
            "draining 10 charge per turn. Charge gain halves above 250."
        )
