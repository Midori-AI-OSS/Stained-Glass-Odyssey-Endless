import pytest

from autofighter.effects import EffectManager
from autofighter.passives import PassiveRegistry
from autofighter.stats import Stats
from autofighter.stats import set_battle_active
from plugins.damage_types import ALL_DAMAGE_TYPES
from plugins.damage_types import load_damage_type
from plugins.damage_types.generic import Generic
from plugins.passives.normal.bubbles_bubble_burst import BubblesBubbleBurst


@pytest.mark.asyncio
async def test_bubbles_random_damage_type():
    registry = PassiveRegistry()
    bubbles = Stats(hp=1000, damage_type=Generic())
    bubbles.passives = ["bubbles_bubble_burst"]
    await registry.trigger("turn_start", bubbles)
    assert bubbles.damage_type.id in ALL_DAMAGE_TYPES


@pytest.mark.asyncio
async def test_bubble_burst_stacks_and_dot():
    set_battle_active(True)
    try:
        bubbles = Stats(hp=1000, damage_type=load_damage_type("Fire"))
        bubbles.set_base_stat("atk", 100)
        ally = Stats(hp=1000, damage_type=Generic())
        enemy1 = Stats(hp=1000, damage_type=Generic())
        enemy2 = Stats(hp=1000, damage_type=Generic())
        enemy1.effect_manager = EffectManager(enemy1)
        enemy2.effect_manager = EffectManager(enemy2)
        bubbles.allies = [bubbles, ally]
        bubbles.enemies = [enemy1, enemy2]

        passive = BubblesBubbleBurst()
        for _ in range(2):
            await passive.on_hit_enemy(bubbles, enemy1)
        await passive.on_hit_enemy(bubbles, enemy2)
        assert BubblesBubbleBurst.get_bubble_stacks(bubbles, enemy1) == 2
        assert BubblesBubbleBurst.get_bubble_stacks(bubbles, enemy2) == 1

        await passive.on_hit_enemy(bubbles, enemy1)
        assert BubblesBubbleBurst.get_bubble_stacks(bubbles, enemy1) == 0
        assert BubblesBubbleBurst.get_bubble_stacks(bubbles, enemy2) == 1
        assert bubbles.hp < 1000
        assert ally.hp < 1000
        assert enemy1.hp < 1000
        assert enemy2.hp < 1000
        assert enemy1.effect_manager.dots
        assert enemy2.effect_manager.dots
        assert enemy1.effect_manager.dots[0].turns == 2
        assert enemy2.effect_manager.dots[0].turns == 2
    finally:
        set_battle_active(False)
