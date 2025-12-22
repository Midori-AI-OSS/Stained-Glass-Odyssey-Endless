from dataclasses import dataclass, field
import random

from autofighter.effects import EffectManager, create_stat_buff
from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class TemporalShield(CardBase):
    id: str = "temporal_shield"
    name: str = "Temporal Shield"
    stars: int = 5
    effects: dict[str, float] = field(
        default_factory=lambda: {"defense": 30.0, "max_hp": 30.0}
    )
    full_about: str = (
        "+3000% DEF & HP; each turn has a 50% chance to grant 99% damage reduction for that turn."
    )
    summarized_about: str = "Boosts def and hp massively; chance to grant near immunity each turn"

    async def apply(self, party):
        await super().apply(party)

        async def _turn_start(*_args) -> None:
            for member in party.members:
                if random.random() < 0.5:
                    mgr = getattr(member, "effect_manager", None)
                    if mgr is None:
                        mgr = EffectManager(member)
                        member.effect_manager = mgr
                    mod = create_stat_buff(
                        member,
                        name=f"{self.id}_mitigation",
                        turns=1,
                        mitigation_mult=100.0,
                    )
                    await mgr.add_modifier(mod)
                    await BUS.emit_async(
                        "card_effect",
                        self.id,
                        member,
                        "damage_reduction",
                        99,
                        {"reduction_percent": 99},
                    )

        self.subscribe("turn_start", _turn_start)
