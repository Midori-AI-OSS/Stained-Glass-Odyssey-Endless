import pytest

from autofighter.stats import Stats
from plugins.damage_types.fire import Fire
from plugins.damage_types.ice import Ice
from plugins.passives.lady_fire_and_ice_duality_engine import (
    LadyFireAndIceDualityEngine,
)


@pytest.mark.asyncio
async def test_flux_stacks_and_debuff_application():
    passive = LadyFireAndIceDualityEngine()
    actor = Stats()
    foe = Stats()
    foes = [foe]

    actor.damage_type = Fire()
    await passive.apply(actor, stack_index=0, target=foe, foes=foes)
    assert passive.get_flux_stacks(actor) == 0

    actor.damage_type = Ice()
    await passive.apply(actor, stack_index=0, target=foe, foes=foes)
    assert passive.get_flux_stacks(actor) == 1

    actor.damage_type = Ice()
    await passive.apply(actor, stack_index=0, target=foe, foes=foes)
    assert passive.get_flux_stacks(actor) == 0

    effects = [
        e
        for e in foe.get_active_effects()
        if e.name == f"{passive.id}_flux_enemy_mitigation"
    ]
    assert len(effects) == 1
    assert effects[0].stat_modifiers["mitigation"] == pytest.approx(-0.02)
