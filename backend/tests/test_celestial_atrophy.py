import pytest

from autofighter.effects import EffectManager
from autofighter.stats import Stats
from plugins.dots.celestial_atrophy import CelestialAtrophy
from tests.helpers import call_maybe_async


@pytest.mark.asyncio
async def test_celestial_atrophy_stacks_and_cleans_up():
    target = Stats()
    target.set_base_stat('atk', 10)
    target.id = "t"
    manager = EffectManager(target)
    target.effect_manager = manager

    dot = CelestialAtrophy(0, 3)
    await call_maybe_async(manager.add_dot, dot)

    await manager.tick()
    assert target.atk == 9

    await manager.tick()
    assert target.atk == 8

    await manager.tick()
    assert target.atk == 10
    assert not target.mods
