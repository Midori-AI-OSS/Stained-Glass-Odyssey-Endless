from dataclasses import dataclass
from dataclasses import field
import inspect
import random

from autofighter.effects import StatModifier
from autofighter.effects import create_stat_buff
from plugins.relics._base import RelicBase


@dataclass
class TimekeepersHourglass(RelicBase):
    """Each turn, allies may gain a short burst of speed."""

    id: str = "timekeepers_hourglass"
    name: str = "Timekeeper's Hourglass"
    stars: int = 4
    effects: dict[str, float] = field(default_factory=dict)
    about: str = (
        "Each turn, 10% base chance (+1% per extra stack) to grant ready allies a 2-turn speed buff."
    )

    async def apply(self, party) -> None:
        if getattr(party, "_t_hourglass_applied", False):
            return
        party._t_hourglass_applied = True
        await super().apply(party)

        stacks = party.relics.count(self.id)
        chance = 0.10 + 0.01 * (stacks - 1)
        chance = min(1.0, max(0.0, chance))
        boost = 1.0 + 0.20 * stacks
        active_mods: dict[int, StatModifier] = {}

        def _member_can_act(member) -> bool:
            if getattr(member, "hp", 0) <= 0:
                return False
            if getattr(member, "actions_per_turn", 0) <= 0:
                return False

            for attr in ("can_act", "can_take_turn"):
                state = getattr(member, attr, None)
                if state is False:
                    return False
                if callable(state):
                    try:
                        result = state()
                    except TypeError:
                        continue
                    if inspect.isawaitable(result):
                        continue
                    if result is False:
                        return False

            return True

        async def _turn_start() -> None:
            if random.random() < chance:
                for member in party.members:
                    if not _member_can_act(member):
                        continue
                    mgr = getattr(member, "effect_manager", None)
                    if mgr is None:
                        continue

                    existing = active_mods.pop(id(member), None)
                    if existing is not None:
                        try:
                            existing.remove()
                        except Exception:
                            pass
                        if existing in mgr.mods:
                            mgr.mods.remove(existing)
                        if getattr(member, "mods", None) and existing.id in member.mods:
                            member.mods.remove(existing.id)

                    mod = create_stat_buff(
                        member,
                        name=f"{self.id}_spd",
                        spd_mult=boost,
                        turns=2,
                    )
                    mgr.add_modifier(mod)
                    active_mods[id(member)] = mod

        def _battle_end(_entity) -> None:
            self.clear_subscriptions(party)
            for member in party.members:
                mod = active_mods.pop(id(member), None)
                if mod is None:
                    continue
                try:
                    mod.remove()
                except Exception:
                    pass
                mgr = getattr(member, "effect_manager", None)
                if mgr is not None and mod in mgr.mods:
                    mgr.mods.remove(mod)
                if getattr(member, "mods", None) and mod.id in member.mods:
                    member.mods.remove(mod.id)
            active_mods.clear()
            if hasattr(party, "_t_hourglass_applied"):
                delattr(party, "_t_hourglass_applied")

        self.subscribe(party, "turn_start", _turn_start)
        self.subscribe(party, "battle_end", _battle_end)

    def describe(self, stacks: int) -> str:
        pct = 10 + 1 * (stacks - 1)
        boost = int(20 * stacks)
        return (
            f"Each turn, {pct}% chance for ready allies to gain +{boost}% SPD for 2 turns."
        )
