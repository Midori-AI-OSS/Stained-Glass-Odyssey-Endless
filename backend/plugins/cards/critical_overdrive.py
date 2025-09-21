from dataclasses import dataclass
from dataclasses import field

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
        state: dict[int, object] = {}

        async def _change(target, stacks) -> None:
            if target not in party.members:
                return
            pid = id(target)
            mod = state.pop(pid, None)
            if mod is not None:
                mod.remove()
                if mod in target.effect_manager.mods:
                    target.effect_manager.mods.remove(mod)
            if stacks > 0:
                extra_rate = 0.10
                # Use base crit rate to avoid compounding with other effects
                base_crit = getattr(target, 'base_crit_rate', 0.05)  # Default 5% base crit rate
                excess = max(0.0, base_crit + extra_rate - 1.0)
                new_mod = create_stat_buff(
                    target,
                    name=f"{self.id}_{pid}",
                    turns=9999,
                    crit_rate=extra_rate,
                    crit_damage=excess * 2,
                )
                target.effect_manager.add_modifier(new_mod)
                state[pid] = new_mod
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
            mod = state.pop(pid, None)
            if mod is not None:
                mod.remove()
                if mod in entity.effect_manager.mods:
                    entity.effect_manager.mods.remove(mod)
            if not state:
                self.cleanup_subscriptions()

        self.subscribe("critical_boost_change", _change)
        self.subscribe("battle_end", _battle_end)
