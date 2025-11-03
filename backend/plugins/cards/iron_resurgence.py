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
    effects: dict[str, float] = field(default_factory=lambda: {"defense": 2.0, "max_hp": 2.0})
    full_about: str = (
        "+200% DEF & +200% HP; when an ally dies, they are immediately revived at 10% HP. "
        "This effect has a 4-turn cooldown and triggers on the first death only."
    )
    summarized_about: str = "Boosts def and hp; revives first fallen ally after cooldown"

    async def apply(self, party: Party) -> None:
        await super().apply(party)
        state = {"cooldown": 0}

        async def _damage(victim, *_):
            if victim not in party.members or victim.hp > 0 or state["cooldown"] > 0:
                return
            heal = max(int(victim.max_hp * 0.1), 1)
            safe_async_task(victim.apply_healing(heal))
            state["cooldown"] = 4
            await BUS.emit_async(
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
            self.cleanup_subscriptions()

        self.subscribe("damage_taken", _damage)
        self.subscribe("turn_start", _turn_start)
        self.subscribe("battle_end", _battle_end)
