from dataclasses import dataclass
from dataclasses import field

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.cards._base import CardBase
from plugins.effects.critical_boost import CriticalBoost


@dataclass
class CriticalTransfer(CardBase):
    id: str = "critical_transfer"
    name: str = "Critical Transfer"
    stars: int = 2
    effects: dict[str, float] = field(default_factory=dict)
    about: str = (
        "Ultimates absorb all Critical Boost stacks and grant +4% ATK per stack for that turn."
    )

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        async def _ultimate_used(user) -> None:
            total = 0
            for member in party.members:
                boost = getattr(member, "_critical_boost", None)
                if isinstance(boost, CriticalBoost):
                    total += boost.stacks
                    await boost._on_damage_taken(member)
            if total == 0:
                return
            effect = getattr(user, "_critical_boost", None)
            if not isinstance(effect, CriticalBoost):
                effect = CriticalBoost()
                setattr(user, "_critical_boost", effect)
            for _ in range(total):
                await effect.apply(user)
            mgr = getattr(user, "effect_manager", None)
            if mgr is None:
                mgr = EffectManager(user)
                user.effect_manager = mgr
            mod = create_stat_buff(
                user,
                name=f"{self.id}_atk",
                turns=1,
                atk_mult=1 + 0.04 * total,
            )
            await mgr.add_modifier(mod)
            await BUS.emit_async(
                "card_effect",
                self.id,
                user,
                "critical_transfer",
                total,
                {"stacks": total, "atk_bonus_pct": 4 * total},
            )

        self.subscribe("ultimate_used", _ultimate_used)
