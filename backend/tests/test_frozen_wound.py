import pytest

from autofighter.effects import EffectManager
from autofighter.stats import Stats
from plugins.dots.frozen_wound import FrozenWound


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "stacks, roll, expect_miss",
    [
        (0, 0.0, False),
        (1, 0.0, True),
        (10, 0.5, False),
        (50, 0.25, True),
        (100, 0.99, True),
    ],
)
@pytest.mark.asyncio
async def test_frozen_wound_miss_chance(stacks, roll, expect_miss, monkeypatch):
    actor = Stats()
    actor.set_base_stat('atk', 10)
    target = Stats(hp=100)
    actor.id = "actor"
    target.id = "target"
    actor.effect_manager = EffectManager(actor)
    target.effect_manager = EffectManager(target)
    for _ in range(stacks):
        actor.effect_manager.add_dot(FrozenWound(1, 1))
    monkeypatch.setattr("plugins.dots.frozen_wound.random.random", lambda: roll)
    proceed = await actor.effect_manager.on_action()
    if proceed:
        await target.apply_damage(actor.atk, attacker=actor)
    if expect_miss:
        assert target.hp == 100
    else:
        assert target.hp < 100