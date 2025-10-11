from dataclasses import dataclass
from dataclasses import field
import random

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.cards._base import CardBase
from plugins.cards._base import safe_async_task
from plugins.characters.foe_base import FoeBase


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

        handlers_store = getattr(party, "_reality_split_handlers", None)
        if handlers_store is None:
            handlers_store = {}
            party._reality_split_handlers = handlers_store

        if handlers_store.get(self.id):
            return

        state: dict[str, object] = {"active": None, "foes": []}

        def _cleanup() -> None:
            handlers_store.pop(self.id, None)
            self.cleanup_subscriptions()
            state["foes"].clear()
            state["active"] = None

        def _battle_start(entity) -> None:
            if isinstance(entity, FoeBase) and entity not in state["foes"]:
                state["foes"].append(entity)

        def _battle_end(entity) -> None:
            if isinstance(entity, FoeBase):
                state["foes"].clear()
                state["active"] = None
                _cleanup()
                return
            members = getattr(party, "members", ())
            if entity is None or entity in members or entity is party:
                _cleanup()

        async def _turn_start_handler(*_args) -> None:
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
                crit_rate=0.5,
            )
            await mgr.add_modifier(mod)

        async def _hit_landed(attacker, _target, amount, *_args) -> None:
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
                await BUS.emit_async(
                    "card_effect",
                    self.id,
                    attacker,
                    "afterimage_echo",
                    echo,
                    {"foe": getattr(foe, "id", "foe")},
                )

        handlers: dict[str, object] = {}

        def _register(event_name: str, handler) -> None:
            handlers[event_name] = handler
            self.subscribe(event_name, handler)

        handlers_store[self.id] = {"handlers": handlers}

        _register("battle_start", _battle_start)
        _register("battle_end", _battle_end)
        _register("turn_start", _turn_start_handler)
        _register("hit_landed", _hit_landed)
