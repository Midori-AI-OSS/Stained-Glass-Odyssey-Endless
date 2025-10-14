"""Tests for Kboshi Flux Cycle passive - element switching with HoT."""
import asyncio
import sys
import types

from autofighter.effects import EffectManager
from autofighter.party import Party
from plugins.characters._base import PlayerBase
from plugins.passives.normal.kboshi_flux_cycle import KboshiFluxCycle


def setup_event_loop():
    """Set up an event loop for testing."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


def test_flux_cycle_grants_hot_on_failed_switch():
    """Test that failing to switch elements grants a HoT."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    party = Party()
    kboshi = PlayerBase()
    kboshi.id = "kboshi"
    kboshi.set_base_stat("max_hp", 100)
    kboshi.hp = 50
    kboshi.effect_manager = EffectManager(kboshi)
    party.members.append(kboshi)

    # Create passive instance
    passive = KboshiFluxCycle()

    # Clear any existing state
    KboshiFluxCycle._damage_stacks.clear()
    KboshiFluxCycle._hot_stacks.clear()

    # Monkey-patch random to force failed switch
    import random
    original_random = random.random
    random.random = lambda: 0.9  # 90% means it will fail the 80% chance

    try:
        # Apply passive - should fail to switch and grant HoT
        loop.run_until_complete(passive.apply(kboshi))

        # Check that HoT was added
        assert len(kboshi.effect_manager.hots) == 1, "HoT should be added on failed switch"
        assert kboshi.effect_manager.hots[0].healing > 0, "HoT should have positive healing"
        assert kboshi.effect_manager.hots[0].turns == 1, "HoT should last 1 turn"

        # Check stacks were incremented
        assert KboshiFluxCycle.get_hot_stacks(kboshi) == 1, "HoT stacks should be 1"
        assert KboshiFluxCycle.get_damage_stacks(kboshi) == 1, "Damage stacks should be 1"

        # Simulate turn and check healing happens
        initial_hp = kboshi.hp
        loop.run_until_complete(kboshi.effect_manager.tick())
        assert kboshi.hp > initial_hp, "HP should increase after HoT tick"

    finally:
        random.random = original_random


def test_flux_cycle_clears_hot_on_element_switch():
    """Test that switching elements clears accumulated HoTs."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    party = Party()
    kboshi = PlayerBase()
    kboshi.id = "kboshi"
    kboshi.set_base_stat("max_hp", 100)
    kboshi.hp = 50
    kboshi.effect_manager = EffectManager(kboshi)
    party.members.append(kboshi)

    # Create passive instance
    passive = KboshiFluxCycle()

    # Clear any existing state
    KboshiFluxCycle._damage_stacks.clear()
    KboshiFluxCycle._hot_stacks.clear()

    import random
    original_random = random.random

    try:
        # First apply: fail to switch to build stacks
        random.random = lambda: 0.9
        loop.run_until_complete(passive.apply(kboshi))

        assert len(kboshi.effect_manager.hots) == 1, "HoT should be added"
        assert KboshiFluxCycle.get_hot_stacks(kboshi) == 1, "Should have 1 HoT stack"

        # Second apply: succeed in switching to clear stacks
        random.random = lambda: 0.5  # 50% means it will succeed the 80% chance
        loop.run_until_complete(passive.apply(kboshi))

        # Check that HoTs were cleared
        assert len(kboshi.effect_manager.hots) == 0, "HoTs should be cleared on element switch"
        assert KboshiFluxCycle.get_hot_stacks(kboshi) == 0, "HoT stacks should be reset to 0"
        assert KboshiFluxCycle.get_damage_stacks(kboshi) == 0, "Damage stacks should be reset to 0"

    finally:
        random.random = original_random


def test_flux_cycle_stacks_hot_healing():
    """Test that multiple failed switches increase HoT healing."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    party = Party()
    kboshi = PlayerBase()
    kboshi.id = "kboshi"
    kboshi.set_base_stat("max_hp", 100)
    kboshi.hp = 50
    kboshi.effect_manager = EffectManager(kboshi)
    party.members.append(kboshi)

    # Create passive instance
    passive = KboshiFluxCycle()

    # Clear any existing state
    KboshiFluxCycle._damage_stacks.clear()
    KboshiFluxCycle._hot_stacks.clear()

    import random
    original_random = random.random
    random.random = lambda: 0.9  # Always fail to switch

    try:
        # First failed switch
        loop.run_until_complete(passive.apply(kboshi))
        first_heal = kboshi.effect_manager.hots[0].healing if kboshi.effect_manager.hots else 0

        # Second failed switch
        loop.run_until_complete(passive.apply(kboshi))
        second_heal = kboshi.effect_manager.hots[-1].healing if len(kboshi.effect_manager.hots) > 1 else 0

        # Second HoT should heal more due to stacking
        assert second_heal > first_heal, f"Second HoT ({second_heal}) should heal more than first ({first_heal})"
        assert KboshiFluxCycle.get_hot_stacks(kboshi) == 2, "Should have 2 HoT stacks"

    finally:
        random.random = original_random
