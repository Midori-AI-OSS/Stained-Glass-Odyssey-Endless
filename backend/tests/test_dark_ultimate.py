import asyncio
import random
import types

from autofighter.effects import DamageOverTime
from autofighter.effects import EffectManager
from autofighter.stats import BUS
from autofighter.stats import Stats
from plugins.damage_types.dark import Dark


class DummyPlayer(Stats):
    async def use_ultimate(self) -> bool:  # pragma: no cover - simple helper
        if not getattr(self, "ultimate_ready", False):
            return False
        self.ultimate_charge = 0
        self.ultimate_ready = False
        return True


def test_dark_ultimate_dot_scaling(monkeypatch):
    actor = DummyPlayer()
    actor.damage_type = Dark()
    actor._base_atk = 100
    actor.ultimate_ready = True

    ally = Stats()
    actor.effect_manager = EffectManager(actor)
    ally.effect_manager = EffectManager(ally)
    actor.effect_manager.add_dot(DamageOverTime("d1", 1, 1, "d1"))
    ally.effect_manager.add_dot(DamageOverTime("d2", 1, 1, "d2"))

    target = Stats()
    actor.allies = [actor, ally]
    actor.enemies = [target]

    async def fake_apply_damage(
        self,
        amount,
        attacker=None,
        *,
        trigger_on_hit=True,
        action_name=None,
    ):
        return amount

    monkeypatch.setattr(Stats, "apply_damage", fake_apply_damage, raising=False)

    hits: list[int] = []
    BUS.subscribe("damage", lambda a, t, d: hits.append(d))

    asyncio.get_event_loop().run_until_complete(
        actor.damage_type.ultimate(actor, actor.allies, actor.enemies)
    )

    expected = int(100 * (Dark.ULT_PER_STACK ** 2))
    assert hits and all(h == expected for h in hits)


def test_dark_ultimate_six_hits(monkeypatch):
    actor = DummyPlayer()
    actor.damage_type = Dark()
    actor._base_atk = 100
    actor.ultimate_ready = True

    target = Stats()
    actor.allies = [actor]
    actor.enemies = [target]

    async def fake_apply_damage(
        self,
        amount,
        attacker=None,
        *,
        trigger_on_hit=True,
        action_name=None,
    ):
        return amount

    monkeypatch.setattr(Stats, "apply_damage", fake_apply_damage, raising=False)

    hits: list[int] = []
    BUS.subscribe("damage", lambda a, t, d: hits.append(d))

    asyncio.get_event_loop().run_until_complete(
        actor.damage_type.ultimate(actor, actor.allies, actor.enemies)
    )

    assert len(hits) == 6


def test_dark_ultimate_prefers_high_aggro_targets(monkeypatch):
    random.seed(99)

    actor = DummyPlayer()
    actor.damage_type = Dark()
    actor._base_atk = 250
    actor.ultimate_ready = True
    actor.ultimate_charge = actor.ultimate_charge_max

    allies = [actor]
    foes: list[Stats] = []
    hits: dict[str, int] = {}

    async def record_damage(self, *_args, **_kwargs):
        hits[self.id] = hits.get(self.id, 0) + 1
        return 0

    for idx, aggro in enumerate((1.0, 3.0, 9.0)):
        foe = Stats()
        foe.id = f"foe-{idx}"
        foe.hp = 5_000
        foe.base_aggro = aggro
        foe.apply_damage = types.MethodType(record_damage, foe)
        foes.append(foe)

    actor.allies = allies
    actor.enemies = foes

    loop = asyncio.get_event_loop()
    for _ in range(5):
        loop.run_until_complete(actor.damage_type.ultimate(actor, actor.allies, actor.enemies))
        actor.ultimate_ready = True
        actor.ultimate_charge = actor.ultimate_charge_max

    assert sum(hits.values()) == 30
    assert hits.get("foe-2", 0) > hits.get("foe-1", 0) >= hits.get("foe-0", 0)
