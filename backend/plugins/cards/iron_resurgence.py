from dataclasses import dataclass
from dataclasses import field

from autofighter.party import Party
from autofighter.stats import BUS
from plugins.cards._base import CardBase
from plugins.cards._base import safe_async_task


@dataclass
class IronResurgence(CardBase):
    id: str = "iron_resurgence"
    name: str = "Iron Resurgence"
    stars: int = 3
    effects: dict[str, float] = field(
        default_factory=lambda: {"defense": 2.0, "max_hp": 2.0}
    )
    about: str = (
        "+200% DEF & +200% HP; first ally death revives at 10% HP, refreshing every 4 turns."
    )

    async def apply(self, party: Party) -> None:
        await super().apply(party)
        state = {"cooldown": 0}

        def _damage(victim, *_):
            if victim not in party.members or victim.hp > 0 or state["cooldown"] > 0:
                return
            heal = max(int(victim.max_hp * 0.1), 1)
            safe_async_task(victim.apply_healing(heal))
            state["cooldown"] = 4
            BUS.emit(
                "card_effect",
                self.id,
                victim,
                "revive",
                heal,
                {"cooldown": state["cooldown"]},
            )

        def _turn_start() -> None:
            if state["cooldown"] > 0:
                state["cooldown"] -= 1

        def _battle_end(entity) -> None:
            if entity not in party.members:
                return
            BUS.unsubscribe("damage_taken", _damage)
            BUS.unsubscribe("turn_start", _turn_start)
            BUS.unsubscribe("battle_end", _battle_end)

        BUS.subscribe("damage_taken", _damage)
        BUS.subscribe("turn_start", _turn_start)
        BUS.subscribe("battle_end", _battle_end)
