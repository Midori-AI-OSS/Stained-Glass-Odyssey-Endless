from dataclasses import dataclass
from dataclasses import field
import random

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.cards._base import CardBase
from plugins.cards._base import safe_async_task
from plugins.foes._base import FoeBase


@dataclass
class RealitySplit(CardBase):
    id: str = "reality_split"
    name: str = "Reality Split"
    stars: int = 5
    effects: dict[str, float] = field(default_factory=lambda: {"atk": 15.0})
    about: str = (
        "+1500% ATK; at the start of each turn, a random ally gains +50% Crit Rate "
        "and their attacks leave an Afterimage that echoes 25% of the damage to all foes."
    )

    async def apply(self, party):
        await super().apply(party)
        state: dict[str, object] = {"active": None, "foes": []}

        def _battle_start(entity) -> None:
            if isinstance(entity, FoeBase):
                state["foes"].append(entity)

        def _battle_end(entity) -> None:
            if isinstance(entity, FoeBase):
                state["foes"].clear()
                state["active"] = None

        def _turn_start() -> None:
            if not party.members:
                return
            target = random.choice(party.members)
            state["active"] = target
            mgr = getattr(target, "effect_manager", None)
            if mgr is None:
                mgr = EffectManager(target)
                target.effect_manager = mgr
            mod = create_stat_buff(
                target,
                name=f"{self.id}_crit",
                turns=1,
                bypass_diminishing_returns=True,
                crit_rate=0.5,
            )
            mgr.add_modifier(mod)

        def _hit_landed(attacker, _target, amount, *_args) -> None:
            if attacker is not state["active"]:
                return
            foes = state["foes"]
            if not foes:
                return
            echo = int(amount * 0.25)
            for foe in foes:
                if foe.hp <= 0:
                    continue
                safe_async_task(foe.apply_damage(echo, attacker=attacker))
                BUS.emit(
                    "card_effect",
                    self.id,
                    attacker,
                    "afterimage_echo",
                    echo,
                    {"foe": getattr(foe, "id", "foe")},
                )

        BUS.subscribe("battle_start", _battle_start)
        BUS.subscribe("battle_end", _battle_end)
        BUS.subscribe("turn_start", lambda *_: _turn_start())
        BUS.subscribe("hit_landed", _hit_landed)
