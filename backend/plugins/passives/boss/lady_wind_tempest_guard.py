from dataclasses import dataclass
from typing import TYPE_CHECKING

from autofighter.stat_effect import StatEffect
from plugins.passives.normal.lady_wind_tempest_guard import LadyWindTempestGuard

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class LadyWindTempestGuardBoss(LadyWindTempestGuard):
    """Boss Tempest Guard that bumps gust stack value by 50%."""

    plugin_type = "passive"
    id = "lady_wind_tempest_guard_boss"
    name = "Tempest Guard (Boss)"
    trigger = "turn_start"
    max_stacks = 5
    stack_display = "pips"

    async def apply(self, target: "Stats") -> None:
        entity_id = id(target)
        cls = self.__class__
        if entity_id not in cls._gust_stacks:
            cls._gust_stacks[entity_id] = 0

        if entity_id not in cls._pending_crits:
            cls._pending_crits[entity_id] = set()

        if entity_id not in cls._crit_callbacks:
            from weakref import ref

            from autofighter.stats import BUS

            target_ref = ref(target)

            def _on_critical_hit(attacker, crit_target, *_args, **_kwargs) -> None:
                tracked = target_ref()
                if tracked is None:
                    BUS.unsubscribe("critical_hit", _on_critical_hit)
                    cls._crit_callbacks.pop(entity_id, None)
                    cleanup_cb = cls._cleanup_callbacks.pop(entity_id, None)
                    if cleanup_cb is not None:
                        BUS.unsubscribe("battle_end", cleanup_cb)
                    return

                if attacker is tracked and crit_target is not None:
                    crit_targets = cls._pending_crits.get(entity_id)
                    if crit_targets is not None:
                        crit_targets.add(id(crit_target))

            BUS.subscribe("critical_hit", _on_critical_hit)
            cls._crit_callbacks[entity_id] = _on_critical_hit

            def _on_battle_end(*_args, **_kwargs) -> None:
                BUS.unsubscribe("critical_hit", _on_critical_hit)
                BUS.unsubscribe("battle_end", _on_battle_end)
                cls._crit_callbacks.pop(entity_id, None)
                cls._cleanup_callbacks.pop(entity_id, None)
                cls._gust_stacks.pop(entity_id, None)
                cls._pending_crits.pop(entity_id, None)

            BUS.subscribe("battle_end", _on_battle_end)
            cls._cleanup_callbacks[entity_id] = _on_battle_end

        baseline_barrier = StatEffect(
            name=f"{self.id}_baseline_barrier",
            stat_modifiers={
                "dodge_odds": 0.105,
                "mitigation": 0.18,
                "effect_resistance": 0.075,
            },
            duration=-1,
            source=self.id,
        )
        target.add_effect(baseline_barrier)

        stacks = cls._gust_stacks[entity_id]
        if stacks > 0:
            self._apply_turn_gust(target, stacks)

    async def on_damage_taken(
        self,
        target: "Stats",
        _attacker: "Stats",
        damage: int,
        **_: object,
    ) -> None:
        if damage <= 0:
            return

        entity_id = id(target)
        stacks = self._gust_stacks.get(entity_id, 0)
        if stacks <= 0:
            return

        tailwind_heal = max(1, int(damage * 0.075 * stacks))
        try:
            await target.apply_healing(
                tailwind_heal,
                source_type="passive",
                source_name=self.id,
            )
        except Exception:
            pass

        remaining = max(0, stacks - 1)
        self._gust_stacks[entity_id] = remaining

        gust_effect_name = f"{self.id}_turn_gust"
        if remaining > 0:
            self._apply_turn_gust(target, remaining)
        else:
            target.remove_effect_by_name(gust_effect_name)

    def _apply_turn_gust(self, target: "Stats", stacks: int) -> None:
        gust_effect_name = f"{self.id}_turn_gust"
        target.remove_effect_by_name(gust_effect_name)

        dodge_bonus = 0.045 + (stacks * 0.015)
        mitigation_bonus = 0.06 + (stacks * 0.0225)
        speed_bonus = stacks * 9
        attack_bonus = max(1, int(target.atk * 0.015 * stacks))

        gust_effect = StatEffect(
            name=gust_effect_name,
            stat_modifiers={
                "dodge_odds": dodge_bonus,
                "mitigation": mitigation_bonus,
                "spd": speed_bonus,
                "atk": attack_bonus,
            },
            duration=1,
            source=self.id,
        )
        target.add_effect(gust_effect)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[BOSS] Gust stacks grant 1.5× dodge, mitigation, speed, and attack bonuses; stored stacks heal for 7.5% of damage taken per stack before being consumed."
            "Critical hits still cash out gusts for Wind Slash, but the lingering defenses are much thicker."
        )
