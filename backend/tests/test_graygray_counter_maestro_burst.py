import pytest

from autofighter.passives import PassiveRegistry
from autofighter.stats import Stats
from plugins.damage_types.generic import Generic
from plugins.passives.normal.graygray_counter_maestro import GraygrayCounterMaestro


@pytest.mark.asyncio
async def test_graygray_counter_maestro_burst_consumes_stacks_and_deals_max_hp():
    registry = PassiveRegistry()

    graygray = Stats(hp=1000, damage_type=Generic())
    graygray.passives = ["graygray_counter_maestro"]

    attacker = Stats(hp=1000, damage_type=Generic())

    for _ in range(49):
        await registry.trigger_damage_taken(graygray, attacker, 10)

    assert GraygrayCounterMaestro.get_stacks(graygray) == 49
    assert attacker.hp > 0

    await registry.trigger_damage_taken(graygray, attacker, 10)

    assert attacker.hp == 0
    assert attacker.last_damage_taken >= graygray.max_hp
    assert GraygrayCounterMaestro.get_stacks(graygray) == 0

    attacker2 = Stats(hp=1000, damage_type=Generic())
    for _ in range(5):
        await registry.trigger_damage_taken(graygray, attacker2, 10)

    assert GraygrayCounterMaestro.get_stacks(graygray) == 5
