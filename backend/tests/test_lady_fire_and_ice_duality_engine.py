import pytest

from autofighter.effects import EffectManager
from autofighter.stats import Stats
from plugins.damage_types.fire import Fire
from plugins.damage_types.ice import Ice
from plugins.passives.normal.lady_fire_and_ice_duality_engine import (
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
        e for e in foe.get_active_effects()
        if e.name == f"{passive.id}_flux_enemy_mitigation"
    ]
    assert len(effects) == 1
    assert effects[0].stat_modifiers["mitigation"] == pytest.approx(-0.02)


@pytest.mark.asyncio
async def test_duality_engine_hot_application():
    """Test that consuming flux stacks applies HoT."""
    passive = LadyFireAndIceDualityEngine()
    actor = Stats()
    actor.effect_manager = EffectManager(actor)
    foe = Stats()
    foes = [foe]

    # Build flux stacks
    actor.damage_type = Fire()
    await passive.apply(actor, stack_index=0, target=foe, foes=foes)
    actor.damage_type = Ice()
    await passive.apply(actor, stack_index=0, target=foe, foes=foes)
    actor.damage_type = Fire()
    await passive.apply(actor, stack_index=0, target=foe, foes=foes)

    assert passive.get_flux_stacks(actor) == 2, "Should have 2 flux stacks"

    # Consume stacks
    await passive.apply(actor, stack_index=0, target=foe, foes=foes)

    # Check HoT was applied
    assert len(actor.effect_manager.hots) > 0, "HoT should be applied"
    hot = actor.effect_manager.hots[0]
    assert hot.healing == 20, "HoT should heal 20 (10 per stack * 2 stacks)"
    assert hot.turns == 3, "HoT should last 3 turns"
    assert passive.get_flux_stacks(actor) == 0, "Flux stacks should be consumed"


@pytest.mark.asyncio
async def test_duality_engine_hot_without_effect_manager():
    """Test that HoT creation works when effect_manager is missing."""
    passive = LadyFireAndIceDualityEngine()
    actor = Stats()
    # Intentionally do NOT create effect_manager
    foe = Stats()
    foes = [foe]

    # Build flux stacks
    actor.damage_type = Fire()
    await passive.apply(actor, stack_index=0, target=foe, foes=foes)
    actor.damage_type = Ice()
    await passive.apply(actor, stack_index=0, target=foe, foes=foes)

    # Consume stacks (should create effect_manager)
    await passive.apply(actor, stack_index=0, target=foe, foes=foes)

    # Check effect_manager was created and HoT applied
    assert hasattr(actor, "effect_manager"), "Effect manager should be created"
    assert actor.effect_manager is not None, "Effect manager should not be None"
    assert len(actor.effect_manager.hots) > 0, "HoT should be applied"


@pytest.mark.asyncio
async def test_duality_engine_hot_scales_with_stacks():
    """Test that HoT healing scales with number of flux stacks."""
    passive = LadyFireAndIceDualityEngine()

    # Test with 1 stack
    actor1 = Stats()
    actor1.effect_manager = EffectManager(actor1)
    actor1.damage_type = Fire()
    await passive.apply(actor1)
    actor1.damage_type = Ice()
    await passive.apply(actor1)
    await passive.apply(actor1)  # Consume 1 stack
    healing_1 = actor1.effect_manager.hots[0].healing if actor1.effect_manager.hots else 0

    # Clear state
    passive._last_element.clear()
    passive._flux_stacks.clear()

    # Test with 3 stacks
    actor2 = Stats()
    actor2.effect_manager = EffectManager(actor2)
    actor2.damage_type = Fire()
    await passive.apply(actor2)
    actor2.damage_type = Ice()
    await passive.apply(actor2)
    actor2.damage_type = Fire()
    await passive.apply(actor2)
    actor2.damage_type = Ice()
    await passive.apply(actor2)
    await passive.apply(actor2)  # Consume 3 stacks
    healing_3 = actor2.effect_manager.hots[0].healing if actor2.effect_manager.hots else 0

    assert healing_3 > healing_1, f"3 stacks ({healing_3}) should heal more than 1 stack ({healing_1})"
    assert healing_1 == 10, f"1 stack should heal 10 HP (got {healing_1})"
    assert healing_3 == 30, f"3 stacks should heal 30 HP (got {healing_3})"
