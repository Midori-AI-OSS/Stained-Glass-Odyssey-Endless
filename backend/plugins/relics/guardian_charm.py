from dataclasses import dataclass
from dataclasses import field

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from plugins.relics._base import RelicBase


@dataclass
class GuardianCharm(RelicBase):
    """At battle start, grants +20% DEF to the lowest-HP ally."""

    id: str = "guardian_charm"
    name: str = "Guardian Charm"
    stars: int = 2
    effects: dict[str, float] = field(default_factory=dict)
    about: str = "At battle start, grants +20% DEF to the lowest-HP ally per stack."

    async def apply(self, party) -> None:
        from autofighter.stats import BUS  # Import here to avoid circular imports

        await super().apply(party)
        if not party.members:
            return
        member = min(party.members, key=lambda m: m.hp)
        stacks = party.relics.count(self.id)
        defense_pct = 20 * stacks

        # Emit relic effect event for defense boost
        await BUS.emit_async(
            "relic_effect",
            "guardian_charm",
            member,
            "defense_boost",
            defense_pct,
            {
                "target_selection": "lowest_hp",
                "defense_percentage": defense_pct,
                "target_hp": member.hp,
                "target_max_hp": member.max_hp,
                "stacks": stacks,
            },
        )

        mgr = getattr(member, "effect_manager", None)
        if mgr is None:
            mgr = EffectManager(member)
            member.effect_manager = mgr

        mod = create_stat_buff(
            member,
            name=self.id,
            defense_mult=1 + 0.2 * stacks,
            turns=9999,
        )
        await mgr.add_modifier(mod)

    def describe(self, stacks: int) -> str:
        pct = 20 * stacks
        return f"At battle start, grants +{pct}% DEF to the lowest-HP ally."
