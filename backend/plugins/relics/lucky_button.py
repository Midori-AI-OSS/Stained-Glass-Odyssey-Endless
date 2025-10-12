from dataclasses import dataclass
from dataclasses import field

from autofighter.stats import BUS
from plugins.effects.critical_boost import CriticalBoost
from plugins.characters._base import PlayerBase
from plugins.relics._base import RelicBase


@dataclass
class LuckyButton(RelicBase):
    """+3% Crit Rate; missed crits grant Critical Boost next turn."""

    id: str = "lucky_button"
    name: str = "Lucky Button"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"crit_rate": 0.03})
    about: str = "+3% Crit Rate; missed crits grant Critical Boost next turn."

    async def apply(self, party) -> None:
        await super().apply(party)

        pending: dict[int, int] = {}
        active: dict[int, tuple[PlayerBase, CriticalBoost]] = {}

        async def _crit_missed(attacker, target) -> None:
            if attacker is None or attacker not in getattr(party, "members", ()):  # type: ignore[arg-type]
                return
            pid = id(attacker)
            pending[pid] = pending.get(pid, 0) + 1

            # Emit relic effect event for crit miss tracking
            await BUS.emit_async("relic_effect", "lucky_button", attacker, "crit_missed_tracked", 1, {
                "target": getattr(target, 'id', str(target)),
                "pending_stacks": pending[pid]
            })

        async def _turn_start() -> None:
            for pid, stacks in list(pending.items()):
                member = next((m for m in party.members if id(m) == pid), None)
                if member is None:
                    continue
                effect = active.get(pid)
                if effect is None:
                    effect = CriticalBoost()
                    active[pid] = (member, effect)
                for _ in range(stacks):
                    await effect.apply(member)

                # Emit relic effect event for critical boost application
                await BUS.emit_async("relic_effect", "lucky_button", member, "critical_boost_applied", stacks, {
                    "boost_stacks": stacks,
                    "from_missed_crits": True
                })
            pending.clear()

        async def _turn_end() -> None:
            for pid, (member, effect) in list(active.items()):
                await effect._on_damage_taken(member)
                del active[pid]

        async def _battle_end(_entity, *_args) -> None:
            self.clear_subscriptions(party)
            pending.clear()
            active.clear()

        self.subscribe(party, "crit_missed", _crit_missed)
        self.subscribe(party, "turn_start", _turn_start)
        self.subscribe(party, "turn_end", _turn_end)
        self.subscribe(party, "battle_end", _battle_end)

    def describe(self, stacks: int) -> str:
        if stacks == 1:
            return "+3% Crit Rate; missed crits grant Critical Boost next turn."
        else:
            # Stacks are multiplicative: each copy compounds the effect
            total_mult = (1.03 ** stacks - 1) * 100
            return (
                f"+{total_mult:.1f}% Crit Rate ({stacks} stacks, multiplicative); missed crits grant {stacks} "
                f"Critical Boost stack{'s' if stacks != 1 else ''} next turn."
            )
