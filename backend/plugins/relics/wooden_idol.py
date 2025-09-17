from dataclasses import dataclass
from dataclasses import field

from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.players._base import PlayerBase
from plugins.relics._base import RelicBase


@dataclass
class WoodenIdol(RelicBase):
    """+3% Effect Res; resisting a debuff grants +1% Effect Res next turn."""

    id: str = "wooden_idol"
    name: str = "Wooden Idol"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"effect_resistance": 0.03})
    about: str = "+3% Effect Res; resisting a debuff grants +1% Effect Res next turn."

    async def apply(self, party) -> None:
        await super().apply(party)

        pending: dict[int, float] = {}
        active: dict[int, tuple[PlayerBase, object]] = {}

        async def _resisted(member) -> None:
            if member not in party.members:
                return
            pid = id(member)
            bonus = 0.01 * party.relics.count(self.id)
            pending[pid] = pending.get(pid, 0) + bonus

            # Track debuff resistance
            await BUS.emit_async("relic_effect", "wooden_idol", member, "debuff_resisted", int(bonus * 100), {
                "ally": getattr(member, 'id', str(member)),
                "resistance_bonus_next_turn": bonus * 100,
                "total_pending_bonus": pending[pid] * 100,
                "stacks": party.relics.count(self.id)
            })

        async def _turn_start() -> None:
            applied_count = 0
            for pid, bonus in list(pending.items()):
                member = next((m for m in party.members if id(m) == pid), None)
                if member is None:
                    continue

                # Create a temporary stat buff for the resistance bonus
                mod = create_stat_buff(
                    member,
                    name=f"{self.id}_resistance_{pid}",
                    effect_resistance=bonus,
                    turns=1,
                )
                member.effect_manager.add_modifier(mod)
                active[pid] = (member, mod)
                applied_count += 1

                # Track resistance buff application
                await BUS.emit_async("relic_effect", "wooden_idol", member, "resistance_buff_applied", int(bonus * 100), {
                    "ally": getattr(member, 'id', str(member)),
                    "resistance_bonus": bonus * 100,
                    "new_total_resistance": member.effect_resistance * 100,
                    "duration_turns": 1
                })

            pending.clear()

        def _turn_end() -> None:
            for pid, (member, mod) in list(active.items()):
                mod.remove()
                if mod in member.effect_manager.mods:
                    member.effect_manager.mods.remove(mod)
                if mod.id in member.mods:
                    member.mods.remove(mod.id)
            active.clear()

        BUS.subscribe("debuff_resisted", _resisted)
        BUS.subscribe("turn_start", lambda *_: _turn_start())
        BUS.subscribe("turn_end", lambda *_: _turn_end())

    def describe(self, stacks: int) -> str:
        if stacks == 1:
            return "+3% Effect Res; resisting a debuff grants +1% Effect Res next turn."
        else:
            # Stacks are multiplicative: each copy compounds the effect
            total_res_mult = (1.03 ** stacks - 1) * 100
            return (
                f"+{total_res_mult:.1f}% Effect Res ({stacks} stacks, multiplicative); resisting a debuff grants +1% Effect Res next turn."
            )