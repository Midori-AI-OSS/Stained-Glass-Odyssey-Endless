from dataclasses import dataclass
from typing import TYPE_CHECKING

from autofighter.stat_effect import StatEffect
from autofighter.stats import BUS
from plugins.passives.normal.ally_overload import AllyOverload

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class AllyOverloadBoss(AllyOverload):
    """Boss-tier Overload that accelerates charge gain and reduces drawbacks."""

    plugin_type = "passive"
    id = "ally_overload_boss"
    name = "Overload (Boss)"
    trigger = "action_taken"
    max_stacks = 180
    stack_display = "number"

    async def apply(self, target: "Stats") -> None:
        """Build charge faster to unlock a heavier Overload stance."""

        entity_id = id(target)
        if entity_id not in self._overload_charge:
            self._overload_charge[entity_id] = 0
            self._overload_active[entity_id] = False

        if not self._overload_active[entity_id]:
            target.actions_per_turn = 2

        base_charge_gain = 15
        current_charge = self._overload_charge[entity_id]
        if current_charge > 180:
            charge_gain = base_charge_gain * 0.5
        else:
            charge_gain = base_charge_gain

        self._overload_charge[entity_id] += charge_gain
        current_charge = self._overload_charge[entity_id]

        if current_charge >= 100 and not self._overload_active[entity_id]:
            await self._activate_overload(target)

        if not self._overload_active[entity_id]:
            self._overload_charge[entity_id] = max(0, current_charge - 5)

    async def _activate_overload(self, target: "Stats") -> None:
        """Boss tuning: more output, softer penalties, larger heal lock."""

        entity_id = id(target)
        self._overload_active[entity_id] = True

        target.actions_per_turn = 5

        damage_bonus = StatEffect(
            name=f"{self.id}_damage_bonus",
            stat_modifiers={"atk": int(target.atk * 0.45)},
            duration=-1,
            source=self.id,
        )
        target.add_effect(damage_bonus)

        damage_vulnerability = StatEffect(
            name=f"{self.id}_damage_vulnerability",
            stat_modifiers={"mitigation": -0.3},
            duration=-1,
            source=self.id,
        )
        target.add_effect(damage_vulnerability)

        em = getattr(target, "effect_manager", None)
        if em is not None:
            em.hots.clear()
            target.hots.clear()

            async def _block_hot(self_em, *_: object, **__: object) -> None:
                return None

            self._add_hot_backup[entity_id] = em.add_hot
            em.add_hot = _block_hot.__get__(em, type(em))

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

        max_recoverable_hp = int(target.max_hp * 0.3)
        hp_cap = StatEffect(
            name=f"{self.id}_hp_cap",
            stat_modifiers={"max_hp": max_recoverable_hp - target.max_hp},
            duration=-1,
            source=self.id,
        )
        target.add_effect(hp_cap)

    async def on_turn_end(self, target: "Stats") -> None:
        """Drain charge more slowly to keep bosses threatening longer."""

        entity_id = id(target)
        if entity_id not in self._overload_charge:
            self._overload_charge[entity_id] = 0
            self._overload_active[entity_id] = False

        if self._overload_active[entity_id]:
            self._overload_charge[entity_id] = max(
                0, self._overload_charge[entity_id] - 15
            )
            if self._overload_charge[entity_id] <= 0:
                await self._deactivate_overload(target)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[BOSS] Twin daggers build 15 charge per action (halved past 180). "
            "At 100 charge, Overload ignites with five swings, +45% damage, and only +30% damage taken while capping healing at 30% HP. "
            "Active Overload drains 15 charge per turn; idle charge still decays by 5."
        )
