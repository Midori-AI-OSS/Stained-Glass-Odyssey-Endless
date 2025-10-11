"""Paradox Hourglass relic effects."""

from dataclasses import dataclass
from dataclasses import field
import random

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.relics._base import RelicBase


@dataclass
class ParadoxHourglass(RelicBase):
    """Can sacrifice allies at battle start to supercharge survivors and debuff foes."""

    id: str = "paradox_hourglass"
    name: str = "Paradox Hourglass"
    stars: int = 5
    effects: dict[str, float] = field(default_factory=lambda: {"atk": 2.0, "defense": 2.0})
    about: str = (
        "At battle start may sacrifice allies to supercharge survivors and shred foe defense."
    )

    async def apply(self, party) -> None:
        """On battle start possibly sacrifices allies for massive buffs."""
        await super().apply(party)

        stacks = party.relics.count(self.id)
        state: dict[str, dict] = {"buffs": {}, "foe": {}}

        async def _battle_start(entity) -> None:
            from plugins.characters.foe_base import FoeBase

            if isinstance(entity, FoeBase):
                base_def = entity.defense
                div = 4 + (stacks - 1)
                new_def = max(100, int(base_def / div))
                mgr = getattr(entity, "effect_manager", None)
                if mgr is None:
                    mgr = EffectManager(entity)
                    entity.effect_manager = mgr

                mod = create_stat_buff(
                    entity,
                    name=f"{self.id}_foe_{id(entity)}",
                    defense=new_def - base_def,
                    turns=9999,
                )
                await mgr.add_modifier(mod)
                state["foe"][id(entity)] = mod

                # Track foe defense reduction
                await BUS.emit_async("relic_effect", "paradox_hourglass", entity, "defense_shredded", base_def - new_def, {
                    "original_defense": base_def,
                    "new_defense": new_def,
                    "division_factor": div,
                    "stacks": stacks
                })
                return

            if state.get("done"):
                return
            state["done"] = True

            alive = [m for m in party.members if m.hp > 0]
            if len(alive) <= 1:
                return
            chance = 0.6 * (len(alive) - 1) / len(alive)

            # Track activation attempt
            await BUS.emit_async("relic_effect", "paradox_hourglass", party, "activation_attempt", int(chance * 100), {
                "alive_count": len(alive),
                "activation_chance": chance,
                "max_sacrifices": min(stacks, 4, len(alive) - 1)
            })

            if random.random() >= chance:
                return

            kill_count = min(stacks, 4, len(alive) - 1)
            to_kill = random.sample(alive, kill_count)

            # Track sacrifices
            for m in to_kill:
                await BUS.emit_async("relic_effect", "paradox_hourglass", m, "ally_sacrificed", m.hp, {
                    "sacrifice_count": kill_count,
                    "ally_name": getattr(m, 'id', str(m))
                })
                m.hp = 0

            survivors = [m for m in party.members if m.hp > 0]
            mult = 3 + (stacks - 1)

            for m in survivors:
                mgr = getattr(m, "effect_manager", None)
                if mgr is None:
                    mgr = EffectManager(m)
                    m.effect_manager = mgr

                mod = create_stat_buff(
                    m,
                    name=f"{self.id}_ally_{id(m)}",
                    turns=9999,
                    atk_mult=mult,
                    defense_mult=mult,
                    max_hp_mult=mult,
                    hp_mult=mult,
                    crit_rate_mult=mult,
                    crit_damage_mult=mult,
                    effect_hit_rate_mult=mult,
                    effect_resistance_mult=mult,
                    vitality_mult=mult,
                    mitigation_mult=mult,
                )
                await mgr.add_modifier(mod)
                m.hp = m.max_hp
                state["buffs"][id(m)] = mod

                # Track survivor supercharging
                await BUS.emit_async("relic_effect", "paradox_hourglass", m, "survivor_supercharged", mult, {
                    "multiplier": mult,
                    "sacrifices_made": kill_count,
                    "full_heal": True,
                    "stats_affected": ["atk", "defense", "max_hp", "crit_rate", "crit_damage", "effect_hit_rate", "effect_resistance", "vitality", "mitigation"]
                })

        def _battle_end(entity) -> None:
            from plugins.characters.foe_base import FoeBase

            if isinstance(entity, FoeBase):
                mod = state["foe"].pop(id(entity), None)
                if mod:
                    mod.remove()
                    if mod in entity.effect_manager.mods:
                        entity.effect_manager.mods.remove(mod)
                    if mod.id in entity.mods:
                        entity.mods.remove(mod.id)
                return

            for member in party.members:
                mod = state["buffs"].pop(id(member), None)
                if mod:
                    mod.remove()
                    if mod in member.effect_manager.mods:
                        member.effect_manager.mods.remove(mod)
                    if mod.id in member.mods:
                        member.mods.remove(mod.id)
            state.pop("done", None)

        self.subscribe(party, "battle_start", _battle_start)
        self.subscribe(party, "battle_end", _battle_end)

    def describe(self, stacks: int) -> str:
        div = 4 + (stacks - 1)
        mult = 3 + (stacks - 1)
        max_kill = min(stacks, 4)
        return (
            f"60% chance to sacrifice up to {max_kill} random allies (max 4, min 1 survivor). "
            f"Survivors gain {mult}x stats and foes' DEF is divided by {div}."
        )
