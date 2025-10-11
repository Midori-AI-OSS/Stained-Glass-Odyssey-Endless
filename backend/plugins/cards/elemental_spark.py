from dataclasses import dataclass
from dataclasses import field
import random

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class ElementalSpark(CardBase):
    id: str = "elemental_spark"
    name: str = "Elemental Spark"
    stars: int = 2
    effects: dict[str, float] = field(
        default_factory=lambda: {"atk": 0.55, "effect_hit_rate": 0.55}
    )
    about: str = (
        "+55% ATK & +55% Effect Hit Rate; at battle start, one random ally's debuffs gain +5% potency."
    )

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)
        chosen = {"member": None, "mod": None}

        async def _battle_start(entity) -> None:
            if not party.members:
                return
            member = random.choice(party.members)
            chosen["member"] = member
            mgr = getattr(member, "effect_manager", None)
            if mgr is None:
                mgr = EffectManager(member)
                member.effect_manager = mgr
            mod = create_stat_buff(
                member,
                name=f"{self.id}_potency",
                turns=9999,
                effect_hit_rate_mult=1.05,
            )
            await mgr.add_modifier(mod)
            chosen["mod"] = (mgr, mod)
            await BUS.emit_async(
                "card_effect",
                self.id,
                member,
                "spark_chosen",
                5,
                {"ally": getattr(member, "id", "member")},
            )

        def _battle_end(*_args) -> None:
            member = chosen.get("member")
            data = chosen.get("mod")
            if member is None or data is None:
                self.cleanup_subscriptions()
                return
            mgr, mod = data
            mod.remove()
            if hasattr(mgr, "mods") and mod in mgr.mods:
                mgr.mods.remove(mod)
            if hasattr(member, "mods") and mod.id in member.mods:
                member.mods.remove(mod.id)
            chosen["member"] = None
            chosen["mod"] = None
            self.cleanup_subscriptions()

        self.subscribe("battle_start", _battle_start)
        self.subscribe("battle_end", _battle_end)
