"""Tests for Lady Fire and Ice's Duality Engine passive."""
import asyncio
import sys
import types

from autofighter.effects import EffectManager
from autofighter.party import Party
from plugins.characters._base import PlayerBase
from plugins.damage_types.fire import Fire
from plugins.damage_types.ice import Ice
from plugins.passives.normal.lady_fire_and_ice_duality_engine import (
    LadyFireAndIceDualityEngine,
)


def setup_event_loop():
    """Set up or create an asyncio event loop for the tests."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


def reset_duality_engine_state() -> None:
    """Clear class-level tracking between tests."""
    LadyFireAndIceDualityEngine._last_element.clear()
    LadyFireAndIceDualityEngine._flux_stacks.clear()


def test_duality_engine_applies_hot_on_flux_consumption():
    """Consuming Flux stacks should apply a HoT and debuff foes."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    reset_duality_engine_state()

    party = Party()

    actor = PlayerBase()
    actor.id = "lady_fire_ice"
    actor.set_base_stat("max_hp", 200)
    actor.hp = 150
    actor.effect_manager = EffectManager(actor)
    actor.damage_type = Fire()
    party.members.append(actor)

    foe = PlayerBase()
    foe.id = "training_dummy"
    foe.effect_manager = EffectManager(foe)

    passive = LadyFireAndIceDualityEngine()

    loop.run_until_complete(passive.apply(actor, foes=[foe]))  # seed last element

    actor.damage_type = Ice()
    loop.run_until_complete(passive.apply(actor, foes=[foe]))  # gain one stack
    assert (
        LadyFireAndIceDualityEngine.get_flux_stacks(actor) == 1
    ), "Flux stack should increment when alternating elements"

    actor.damage_type = Ice()
    loop.run_until_complete(passive.apply(actor, foes=[foe]))  # consume stack

    assert actor.effect_manager.hots, "HoT should be applied when stacks are consumed"
    hot = actor.effect_manager.hots[0]
    assert hot.healing > 0, "HoT must provide positive healing"
    assert hot.turns == 3, "HoT duration should match specification"

    foe_effects = foe.get_active_effects()
    assert any(
        effect.name == f"{passive.id}_flux_enemy_mitigation" for effect in foe_effects
    ), "Foes should receive a mitigation debuff when stacks are consumed"


def test_duality_engine_creates_effect_manager_when_missing():
    """The passive should create an EffectManager if the owner lacks one."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    reset_duality_engine_state()

    actor = PlayerBase()
    actor.id = "lady_fire_ice_missing_mgr"
    actor.set_base_stat("max_hp", 180)
    actor.hp = 140
    actor.damage_type = Fire()

    passive = LadyFireAndIceDualityEngine()

    loop.run_until_complete(passive.apply(actor))

    actor.damage_type = Ice()
    loop.run_until_complete(passive.apply(actor))  # gain stack
    actor.damage_type = Ice()
    loop.run_until_complete(passive.apply(actor))  # consume stack

    assert hasattr(actor, "effect_manager"), "EffectManager should be created automatically"
    assert actor.effect_manager.hots, "HoT should be tracked even without pre-existing manager"


def test_duality_engine_hot_scales_with_stacks():
    """More Flux stacks should produce stronger healing."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()

    # Single-stack scenario
    reset_duality_engine_state()
    actor_one = PlayerBase()
    actor_one.id = "lady_fire_ice_single"
    actor_one.set_base_stat("max_hp", 200)
    actor_one.hp = 150
    actor_one.effect_manager = EffectManager(actor_one)
    actor_one.damage_type = Fire()
    passive_one = LadyFireAndIceDualityEngine()

    loop.run_until_complete(passive_one.apply(actor_one))
    actor_one.damage_type = Ice()
    loop.run_until_complete(passive_one.apply(actor_one))  # gain stack
    actor_one.damage_type = Ice()
    loop.run_until_complete(passive_one.apply(actor_one))  # consume
    assert actor_one.effect_manager.hots
    single_heal = actor_one.effect_manager.hots[0].healing

    # Multi-stack scenario
    reset_duality_engine_state()
    actor_two = PlayerBase()
    actor_two.id = "lady_fire_ice_multi"
    actor_two.set_base_stat("max_hp", 200)
    actor_two.hp = 150
    actor_two.effect_manager = EffectManager(actor_two)
    passive_two = LadyFireAndIceDualityEngine()

    actor_two.damage_type = Fire()
    loop.run_until_complete(passive_two.apply(actor_two))

    actor_two.damage_type = Ice()
    loop.run_until_complete(passive_two.apply(actor_two))

    actor_two.damage_type = Fire()
    loop.run_until_complete(passive_two.apply(actor_two))

    actor_two.damage_type = Ice()
    loop.run_until_complete(passive_two.apply(actor_two))

    actor_two.damage_type = Ice()
    loop.run_until_complete(passive_two.apply(actor_two))  # consume stacks

    assert actor_two.effect_manager.hots
    stacked_heal = actor_two.effect_manager.hots[0].healing

    assert (
        stacked_heal > single_heal
    ), f"Healing ({stacked_heal}) should increase with more Flux stacks compared to {single_heal}"

