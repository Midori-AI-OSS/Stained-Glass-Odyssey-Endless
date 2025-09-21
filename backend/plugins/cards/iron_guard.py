from dataclasses import dataclass
from dataclasses import field
from itertools import count

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class IronGuard(CardBase):
    id: str = "iron_guard"
    name: str = "Iron Guard"
    stars: int = 2
    effects: dict[str, float] = field(default_factory=lambda: {"defense": 0.55})
    about: str = "+55% DEF; damage grants all allies +10% DEF for 1 turn."

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)
        seq = count()

        async def _damage_taken(victim, *_args) -> None:
            if victim not in party.members:
                return
            # Emit a single card effect event per trigger, regardless of how many party members get the buff
            await BUS.emit_async(
                "card_effect",
                self.id,
                victim,  # Use victim as the event source since they triggered the effect
                "temporary_defense",
                10,
                {"source": getattr(victim, "id", "victim"), "affected_members": len(party.members)},
            )
            for member in party.members:
                mgr = getattr(member, "effect_manager", None)
                if mgr is None:
                    mgr = EffectManager(member)
                    member.effect_manager = mgr
                mod = create_stat_buff(
                    member,
                    name=f"{self.id}_{next(seq)}",
                    turns=1,
                    defense_mult=1.10,
                )
                mgr.add_modifier(mod)

        self.subscribe("damage_taken", _damage_taken)
