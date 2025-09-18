from dataclasses import dataclass
from dataclasses import field

from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class IronResolve(CardBase):
    """+500% DEF & HP; first death revives at 30% HP, recharging every 3 turns."""

    id: str = "iron_resolve"
    name: str = "Iron Resolve"
    stars: int = 4
    effects: dict[str, float] = field(
        default_factory=lambda: {"defense": 5, "max_hp": 5}
    )
    about: str = (
        "+500% DEF & +500% HP; the first time an ally dies, revive them at "
        "30% HP. This effect refreshes every 3 turns."
    )

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        cooldowns: dict[int, int] = {id(m): 0 for m in party.members}

        async def _damage_taken(target, attacker, amount) -> None:
            pid = id(target)
            if target not in party.members:
                return
            if target.hp > 0 or cooldowns.get(pid, 0) > 0:
                return
            revive_hp = int(target.max_hp * 0.30)
            target.hp = revive_hp
            cooldowns[pid] = 3
            await BUS.emit_async(
                "card_effect",
                self.id,
                target,
                "revive",
                revive_hp,
                {"revive_hp": revive_hp, "cooldown": 3},
            )

        def _turn_end() -> None:
            for pid in list(cooldowns):
                if cooldowns[pid] > 0:
                    cooldowns[pid] -= 1

        BUS.subscribe("damage_taken", _damage_taken)
        BUS.subscribe("turn_end", _turn_end)