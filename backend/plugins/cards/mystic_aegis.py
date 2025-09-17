from dataclasses import dataclass
from dataclasses import field

from autofighter.stats import BUS
from plugins.cards._base import CardBase
from plugins.cards._base import safe_async_task


@dataclass
class MysticAegis(CardBase):
    id: str = "mystic_aegis"
    name: str = "Mystic Aegis"
    stars: int = 2
    effects: dict[str, float] = field(default_factory=lambda: {"effect_resistance": 0.55})
    about: str = "+55% Effect Res; when an ally resists a debuff, they heal for 5% Max HP."

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        async def _resisted(member) -> None:
            if member not in party.members:
                return
            heal = int(member.max_hp * 0.05)
            await BUS.emit_async(
                "card_effect",
                self.id,
                member,
                "healing",
                heal,
                {"heal_amount": heal},
            )
            safe_async_task(member.apply_healing(heal))

        BUS.subscribe("debuff_resisted", _resisted)