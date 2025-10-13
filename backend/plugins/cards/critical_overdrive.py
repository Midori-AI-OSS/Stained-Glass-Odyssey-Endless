from dataclasses import dataclass
from dataclasses import field

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.party import Party
from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class CriticalOverdrive(CardBase):
    id: str = "critical_overdrive"
    name: str = "Critical Overdrive"
    stars: int = 3
    effects: dict[str, float] = field(default_factory=lambda: {"atk": 2.55})
    about: str = (
        "+255% ATK; while any ally has Critical Boost active, all allies gain +10% Crit Rate and "
        "convert excess Crit Rate to +2% Crit Damage."
    )

    async def apply(self, party: Party) -> None:
        await super().apply(party)
        active_targets: set[int] = set()

        def _remove_effect(entity) -> None:
            pid = id(entity)
            effect_id = f"{self.id}_{pid}"
            mgr = getattr(entity, "effect_manager", None)
            if mgr is not None:
                for existing in list(getattr(mgr, "mods", [])):
                    if existing.id == effect_id:
                        existing.remove()
                        mgr.mods.remove(existing)
                        break
            mods = getattr(entity, "mods", None)
            if mods is not None:
                while effect_id in mods:
                    mods.remove(effect_id)
            if hasattr(entity, "remove_effect_by_name"):
                try:
                    entity.remove_effect_by_name(effect_id)
                except Exception:
                    pass
            active_targets.discard(pid)

        async def _change(target, stacks) -> None:
            if target not in party.members:
                return
            pid = id(target)
            if stacks <= 0:
                _remove_effect(target)
                if not active_targets:
                    self.cleanup_subscriptions()
                return

            effect_id = f"{self.id}_{pid}"
            mgr = getattr(target, "effect_manager", None)
            if mgr is None:
                mgr = EffectManager(target)
                target.effect_manager = mgr
            if stacks > 0:
                extra_rate = 0.10
                # Use base crit rate to avoid compounding with other effects
                if hasattr(target, "get_base_stat"):
                    base_crit = float(target.get_base_stat("crit_rate"))
                else:
                    base_crit = float(getattr(target, "_base_crit_rate", 0.05))
                excess = max(0.0, base_crit + extra_rate - 1.0)
                new_mod = create_stat_buff(
                    target,
                    name=effect_id,
                    id=effect_id,
                    turns=9999,
                    bypass_diminishing=True,
                    crit_rate=extra_rate,
                    crit_damage=excess * 2,
                )
                await mgr.add_modifier(new_mod)
                active_targets.add(pid)
                await BUS.emit_async(
                    "card_effect",
                    self.id,
                    target,
                    "crit_overdrive",
                    int(excess * 200),
                    {
                        "extra_crit_rate": extra_rate * 100,
                        "excess_crit_rate": excess * 100,
                        "extra_crit_damage": excess * 200,
                    },
                )

        def _battle_end(entity) -> None:
            if entity not in party.members:
                return
            pid = id(entity)
            if pid in active_targets:
                _remove_effect(entity)
            if not active_targets:
                self.cleanup_subscriptions()

        self.subscribe("critical_boost_change", _change)
        self.subscribe("battle_end", _battle_end)
