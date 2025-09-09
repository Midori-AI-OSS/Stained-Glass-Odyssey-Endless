import asyncio

from autofighter.effects import DamageOverTime
from autofighter.effects import EffectManager
from autofighter.stats import BUS
from autofighter.stats import Stats
from plugins.damage_types.dark import Dark


class DummyPlayer(Stats):
    pass


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

    async def fake_apply_damage(self, amount, attacker=None, *, trigger_on_hit=True):
        return amount

    monkeypatch.setattr(Stats, "apply_damage", fake_apply_damage, raising=False)

    hits: list[int] = []
    BUS.subscribe("damage", lambda a, t, d: hits.append(d))

    asyncio.get_event_loop().run_until_complete(
        actor.damage_type.ultimate(actor, actor.allies, actor.enemies)
    )

    expected = int(100 * (Dark.ULT_PER_STACK**2))
    assert hits and all(h == expected for h in hits)


def test_dark_ultimate_six_hits(monkeypatch):
    actor = DummyPlayer()
    actor.damage_type = Dark()
    actor._base_atk = 100
    actor.ultimate_ready = True

    target = Stats()
    actor.allies = [actor]
    actor.enemies = [target]

    async def fake_apply_damage(self, amount, attacker=None, *, trigger_on_hit=True):
        return amount

    monkeypatch.setattr(Stats, "apply_damage", fake_apply_damage, raising=False)

    hits: list[int] = []
    BUS.subscribe("damage", lambda a, t, d: hits.append(d))

    asyncio.get_event_loop().run_until_complete(
        actor.damage_type.ultimate(actor, actor.allies, actor.enemies)
    )

    assert len(hits) == 6
