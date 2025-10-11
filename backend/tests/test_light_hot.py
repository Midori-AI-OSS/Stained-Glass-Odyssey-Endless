import pytest

from autofighter.effects import EffectManager
from autofighter.stats import Stats
from plugins.damage_types.light import Light


@pytest.mark.asyncio
async def test_radiant_regeneration_stacks_and_scales_with_vitality():
    light = Light()
    actor = Stats(damage_type=light)
    actor.set_base_stat("atk", 300)
    ally = Stats()
    actor.effect_manager = EffectManager(actor)
    ally.effect_manager = EffectManager(ally)
    await light.on_action(actor, [actor, ally], [])
    await light.on_action(actor, [actor, ally], [])
    stacks = [h for h in ally.effect_manager.hots if h.id == "light_radiant_regeneration"]
    assert len(stacks) == 2

    expected_base = max(15, int(actor.atk * 0.2))
    expected_healing = int(expected_base * max(actor.vitality, 1.0))
    assert stacks[0].healing == expected_healing

    actor.vitality = 2.5
    actor.set_base_stat("atk", 420)
    await light.on_action(actor, [actor, ally], [])
    stacks = [h for h in ally.effect_manager.hots if h.id == "light_radiant_regeneration"]
    assert len(stacks) == 3
    expected_base = max(15, int(actor.atk * 0.2))
    expected_healing = int(expected_base * max(actor.vitality, 1.0))
    assert stacks[-1].healing == expected_healing


@pytest.mark.asyncio
async def test_light_heals_low_hp_ally():
    light = Light()
    actor = Stats(damage_type=light)
    actor.set_base_stat('atk', 50)
    ally = Stats()
    ally.max_hp = 100
    ally.hp = 20
    actor.effect_manager = EffectManager(actor)
    ally.effect_manager = EffectManager(ally)
    proceed = await light.on_action(actor, [actor, ally], [])
    assert ally.hp > 20
    assert not proceed
