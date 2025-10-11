from dataclasses import dataclass
from dataclasses import field

from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.relics._base import RelicBase
from plugins.relics._base import safe_async_task


@dataclass
class SoulPrism(RelicBase):
    """Revives fallen allies at 1% HP with heavy Max HP penalty and small buffs."""

    id: str = "soul_prism"
    name: str = "Soul Prism"
    stars: int = 5
    effects: dict[str, float] = field(default_factory=lambda: {"defense": 0.05, "mitigation": 0.05})
    about: str = "Revives fallen allies at 1% HP with heavy Max HP penalty and small buffs."

    async def apply(self, party) -> None:
        """Revive fallen allies after battles with reduced Max HP."""
        await super().apply(party)

        stacks = party.relics.count(self.id)
        penalty = 0.75 - 0.05 * (stacks - 1)
        multiplier = 1 - penalty
        buff = 0.05 + 0.02 * (stacks - 1)

        async def _battle_end(entity) -> None:
            from plugins.characters.foe_base import FoeBase

            if not isinstance(entity, FoeBase):
                return
            revived_count = 0
            for member in party.members:
                if member.hp > 0:
                    continue
                revived_count += 1
                base = getattr(member, "_soul_prism_hp", member.max_hp)
                member._soul_prism_hp = base
                mod_id = f"{self.id}_{id(member)}"
                existing = next(
                    (m for m in member.effect_manager.mods if m.id == mod_id),
                    None,
                )
                if existing:
                    existing.remove()
                    member.effect_manager.mods.remove(existing)
                    if existing.id in member.mods:
                        member.mods.remove(existing.id)
                mod = create_stat_buff(
                    member,
                    name=mod_id,
                    id=mod_id,
                    max_hp_mult=multiplier,
                    defense_mult=1 + buff,
                    mitigation_mult=1 + buff,
                    turns=9999,
                )
                await member.effect_manager.add_modifier(mod)
                heal = max(1, int(member.max_hp * 0.01))

                # Track the revival
                await BUS.emit_async("relic_effect", "soul_prism", member, "ally_revived", heal, {
                    "ally": getattr(member, 'id', str(member)),
                    "max_hp_penalty": penalty * 100,
                    "defense_buff": buff * 100,
                    "mitigation_buff": buff * 100,
                    "revival_hp": heal,
                    "revival_hp_percentage": 1,
                    "stacks": stacks
                })

                safe_async_task(member.apply_healing(heal))

            # Track revival summary if any allies were revived
            if revived_count > 0:
                await BUS.emit_async("relic_effect", "soul_prism", party, "battle_revival_summary", revived_count, {
                    "allies_revived": revived_count,
                    "max_hp_penalty": penalty * 100,
                    "buffs_applied": ["defense", "mitigation"],
                    "buff_percentage": buff * 100
                })

            self.unsubscribe(party, "battle_end", _battle_end)

        self.subscribe(party, "battle_end", _battle_end)

    def describe(self, stacks: int) -> str:
        penalty = 75 - 5 * (stacks - 1)
        buff = 5 + 2 * (stacks - 1)
        return (
            "Revives fallen allies at 1% HP after battles. "
            f"Reduces Max HP by {penalty}% and grants +{buff}% DEF and mitigation."
        )
