from dataclasses import dataclass
from dataclasses import field

from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.relics._base import RelicBase


@dataclass
class TatteredFlag(RelicBase):
    """+3% party Max HP; ally deaths grant survivors +3% ATK."""

    id: str = "tattered_flag"
    name: str = "Tattered Flag"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"max_hp": 0.03})
    about: str = "+3% party Max HP; ally deaths grant survivors +3% ATK."

    async def apply(self, party) -> None:
        await super().apply(party)

        async def _fallen(target, attacker, amount, *_: object) -> None:
            if target not in party.members or target.hp > 0:
                return
            survivors = [member for member in party.members if member is not target and member.hp > 0]
            if not survivors:
                return

            stacks = party.relics.count(self.id)

            # Emit relic effect event for ally death buff
            await BUS.emit_async("relic_effect", "tattered_flag", target, "ally_death_buff", 3 * stacks, {
                "fallen_ally": getattr(target, 'id', str(target)),
                "survivors": [getattr(m, 'id', str(m)) for m in survivors],
                "atk_bonus_percentage": 3 * stacks,
                "stacks": stacks
            })

            for member in survivors:
                mod = create_stat_buff(member, name=f"{self.id}_buff", atk_mult=1.03, turns=9999)
                await member.effect_manager.add_modifier(mod)

        self.subscribe(party, "damage_taken", _fallen)

    def describe(self, stacks: int) -> str:
        if stacks == 1:
            return "+3% party Max HP; ally deaths grant survivors +3% ATK."
        else:
            # Stacks are multiplicative: each copy compounds the effect
            total_hp_mult = (1.03 ** stacks - 1) * 100
            return f"+{total_hp_mult:.1f}% party Max HP ({stacks} stacks, multiplicative); ally deaths grant survivors +3% ATK."
