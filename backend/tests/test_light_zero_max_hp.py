import pytest

from autofighter.stats import Stats
from plugins.damage_types.light import Light


@pytest.mark.asyncio
async def test_light_on_action_skips_zero_max_hp_ally():
    light = Light()
    actor = Stats(damage_type=light)
    ally = Stats()
    ally.set_base_stat("max_hp", 0)
    ally.hp = 1

    result = await light.on_action(actor, [actor, ally], [])

    assert result is True
