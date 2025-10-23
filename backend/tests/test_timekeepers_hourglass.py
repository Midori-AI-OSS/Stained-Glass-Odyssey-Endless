"""Tests for Timekeeper's Hourglass relic - speed buff mechanics."""
import asyncio
import random
import sys
import types

from autofighter.party import Party
from autofighter.stats import BUS
from plugins.characters._base import PlayerBase
from plugins.relics.timekeepers_hourglass import TimekeepersHourglass


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


def test_timekeepers_hourglass_buffs_ally_without_effect_manager():
    """Test that Timekeeper's Hourglass can buff allies without effect_manager."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    party = Party()

    # Create an ally without effect_manager
    member = PlayerBase()
    member.id = "ally_no_mgr"
    member.set_base_stat("max_hp", 100)
    member.set_base_stat("spd", 50)
    member.hp = 100
    member.actions_per_turn = 1
    # Intentionally do NOT create effect_manager
    party.members.append(member)

    # Add Timekeeper's Hourglass relic
    party.relics.append("timekeepers_hourglass")

    # Apply the relic
    relic = TimekeepersHourglass()
    loop.run_until_complete(relic.apply(party))

    # Force the relic to proc (100% chance)
    original_random = random.random
    random.random = lambda: 0.0  # Always proc

    try:
        # Emit turn_start to trigger the buff
        loop.run_until_complete(BUS.emit_async("turn_start"))
        loop.run_until_complete(asyncio.sleep(0.1))

        # Check that effect_manager was created
        assert hasattr(member, "effect_manager"), "Effect manager should be created"
        assert member.effect_manager is not None, "Effect manager should not be None"

        # Check that speed buff was applied
        assert len(member.effect_manager.mods) > 0, "Speed buff should be applied"
        assert member.spd > 50, f"Speed should be buffed (was 50, now {member.spd})"

    finally:
        random.random = original_random


def test_timekeepers_hourglass_buffs_ally_with_existing_effect_manager():
    """Test that Timekeeper's Hourglass works with allies that already have effect_manager."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    party = Party()

    # Create an ally with effect_manager
    from autofighter.effects import EffectManager
    member = PlayerBase()
    member.id = "ally_with_mgr"
    member.set_base_stat("max_hp", 100)
    member.set_base_stat("spd", 50)
    member.hp = 100
    member.actions_per_turn = 1
    member.effect_manager = EffectManager(member)
    party.members.append(member)

    # Add Timekeeper's Hourglass relic
    party.relics.append("timekeepers_hourglass")

    # Apply the relic
    relic = TimekeepersHourglass()
    loop.run_until_complete(relic.apply(party))

    # Force the relic to proc
    original_random = random.random
    random.random = lambda: 0.0

    try:
        # Emit turn_start to trigger the buff
        loop.run_until_complete(BUS.emit_async("turn_start"))
        loop.run_until_complete(asyncio.sleep(0.1))

        # Check that speed buff was applied
        assert len(member.effect_manager.mods) > 0, "Speed buff should be applied"
        assert member.spd > 50, f"Speed should be buffed (was 50, now {member.spd})"

    finally:
        random.random = original_random


def test_timekeepers_hourglass_does_not_buff_dead_allies():
    """Test that Timekeeper's Hourglass doesn't buff dead allies."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    party = Party()

    # Create a dead ally
    member = PlayerBase()
    member.id = "dead_ally"
    member.set_base_stat("max_hp", 100)
    member.set_base_stat("spd", 50)
    member.hp = 0  # Dead
    member.actions_per_turn = 1
    party.members.append(member)

    # Add Timekeeper's Hourglass relic
    party.relics.append("timekeepers_hourglass")

    # Apply the relic
    relic = TimekeepersHourglass()
    loop.run_until_complete(relic.apply(party))

    # Force the relic to proc
    original_random = random.random
    random.random = lambda: 0.0

    try:
        # Emit turn_start
        loop.run_until_complete(BUS.emit_async("turn_start"))
        loop.run_until_complete(asyncio.sleep(0.1))

        # Dead ally should not get effect_manager or buffs
        if hasattr(member, "effect_manager") and member.effect_manager:
            assert len(member.effect_manager.mods) == 0, "Dead ally should not be buffed"

    finally:
        random.random = original_random


def test_timekeepers_hourglass_stacks_increase_buff():
    """Test that multiple Timekeeper's Hourglass stacks increase the speed buff."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()

    # Test with 1 stack
    party1 = Party()
    member1 = PlayerBase()
    member1.id = "ally1"
    member1.set_base_stat("max_hp", 100)
    member1.set_base_stat("spd", 50)
    member1.hp = 100
    member1.actions_per_turn = 1
    party1.members.append(member1)
    party1.relics.append("timekeepers_hourglass")

    relic1 = TimekeepersHourglass()
    loop.run_until_complete(relic1.apply(party1))

    original_random = random.random
    random.random = lambda: 0.0

    try:
        loop.run_until_complete(BUS.emit_async("turn_start"))
        loop.run_until_complete(asyncio.sleep(0.1))
        speed_with_1_stack = member1.spd

        # Test with 2 stacks
        party2 = Party()
        member2 = PlayerBase()
        member2.id = "ally2"
        member2.set_base_stat("max_hp", 100)
        member2.set_base_stat("spd", 50)
        member2.hp = 100
        member2.actions_per_turn = 1
        party2.members.append(member2)
        party2.relics.extend(["timekeepers_hourglass", "timekeepers_hourglass"])

        relic2 = TimekeepersHourglass()
        loop.run_until_complete(relic2.apply(party2))
        loop.run_until_complete(BUS.emit_async("turn_start"))
        loop.run_until_complete(asyncio.sleep(0.1))
        speed_with_2_stacks = member2.spd

        # 2 stacks should give bigger buff than 1 stack
        assert speed_with_2_stacks > speed_with_1_stack, \
            f"2 stacks ({speed_with_2_stacks}) should buff more than 1 stack ({speed_with_1_stack})"

    finally:
        random.random = original_random
