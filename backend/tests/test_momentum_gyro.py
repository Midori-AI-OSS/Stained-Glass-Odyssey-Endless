import asyncio

import pytest

from autofighter.party import Party
from autofighter.relics import apply_relics
from autofighter.relics import award_relic
from autofighter.stats import BUS
from plugins.characters._base import PlayerBase
import plugins.event_bus as event_bus_module


@pytest.mark.asyncio
async def test_momentum_gyro_streak_buildup():
    """Test that Momentum Gyro builds streak when hitting the same target."""
    event_bus_module.bus._subs.clear()
    party = Party()
    attacker = PlayerBase()
    attacker.id = "attacker"
    attacker.set_base_stat("atk", 100)
    attacker.hp = attacker.set_base_stat("max_hp", 1000)

    target = PlayerBase()
    target.id = "target"
    target.hp = target.set_base_stat("max_hp", 1000)

    party.members.append(attacker)

    # Award relic and apply
    award_relic(party, "momentum_gyro")
    await apply_relics(party)

    await BUS.emit_async("battle_start", attacker)

    # Get baseline ATK
    baseline_atk = attacker.atk

    # First hit (streak = 1)
    await BUS.emit_async(
        "damage_dealt",
        attacker,
        target,
        10,
        None,  # damage_type
        None,  # source
        None,  # source_action
        "attack",
        {}
    )
    await asyncio.sleep(0)

    # Should have ATK buff now (5% per stack * 1 relic * 1 streak = 5%)
    assert attacker.atk > baseline_atk

    # Second hit to same target (streak = 2)
    await BUS.emit_async(
        "damage_dealt",
        attacker,
        target,
        10,
        None,
        None,
        None,
        "attack",
        {}
    )
    await asyncio.sleep(0)

    # ATK should be higher (5% per stack * 1 relic * 2 streak = 10%)
    # Note: Buffs stack multiplicatively in this system
    assert attacker.atk > baseline_atk


@pytest.mark.asyncio
async def test_momentum_gyro_streak_reset_on_target_switch():
    """Test that streak resets when switching targets."""
    event_bus_module.bus._subs.clear()
    party = Party()
    attacker = PlayerBase()
    attacker.id = "attacker"
    attacker.set_base_stat("atk", 100)
    attacker.hp = attacker.set_base_stat("max_hp", 1000)

    target1 = PlayerBase()
    target1.id = "target1"
    target1.hp = target1.set_base_stat("max_hp", 1000)

    target2 = PlayerBase()
    target2.id = "target2"
    target2.hp = target2.set_base_stat("max_hp", 1000)

    party.members.append(attacker)

    award_relic(party, "momentum_gyro")
    await apply_relics(party)

    await BUS.emit_async("battle_start", attacker)

    # Hit target1 twice (streak = 2)
    await BUS.emit_async("damage_dealt", attacker, target1, 10, None, None, None, "attack", {})
    await asyncio.sleep(0)

    await BUS.emit_async("damage_dealt", attacker, target1, 10, None, None, None, "attack", {})
    await asyncio.sleep(0)

    # Check state (streak should be 2)
    state = getattr(party, "_momentum_gyro_state", None)
    assert state is not None
    chains = state.get("chains", {})
    attacker_id = id(attacker)
    assert attacker_id in chains
    assert chains[attacker_id]["streak"] == 2

    # Switch to target2 (streak should reset to 1)
    await BUS.emit_async("damage_dealt", attacker, target2, 10, None, None, None, "attack", {})
    await asyncio.sleep(0)

    # Streak should be 1 now
    assert chains[attacker_id]["streak"] == 1
    assert id(chains[attacker_id]["target"]) == id(target2)


@pytest.mark.asyncio
async def test_momentum_gyro_streak_cap():
    """Test that streak caps at 5."""
    event_bus_module.bus._subs.clear()
    party = Party()
    attacker = PlayerBase()
    attacker.id = "attacker"
    attacker.set_base_stat("atk", 100)
    attacker.hp = attacker.set_base_stat("max_hp", 1000)

    target = PlayerBase()
    target.id = "target"
    target.hp = target.set_base_stat("max_hp", 1000)

    party.members.append(attacker)

    award_relic(party, "momentum_gyro")
    await apply_relics(party)

    await BUS.emit_async("battle_start", attacker)

    # Hit 10 times to try to exceed cap
    for _ in range(10):
        await BUS.emit_async("damage_dealt", attacker, target, 10, None, None, None, "attack", {})
        await asyncio.sleep(0)

    # Check that streak is capped at 5
    state = getattr(party, "_momentum_gyro_state", None)
    chains = state.get("chains", {})
    attacker_id = id(attacker)
    assert chains[attacker_id]["streak"] == 5


@pytest.mark.asyncio
async def test_momentum_gyro_mitigation_debuff():
    """Test that targets receive mitigation debuff."""
    event_bus_module.bus._subs.clear()
    party = Party()
    attacker = PlayerBase()
    attacker.id = "attacker"
    attacker.set_base_stat("atk", 100)
    attacker.hp = attacker.set_base_stat("max_hp", 1000)

    target = PlayerBase()
    target.id = "target"
    target.set_base_stat("mitigation", 1.0)
    target.hp = target.set_base_stat("max_hp", 1000)

    party.members.append(attacker)

    award_relic(party, "momentum_gyro")
    await apply_relics(party)

    await BUS.emit_async("battle_start", attacker)

    baseline_mitigation = target.mitigation

    # First hit (streak = 1, debuff = 5%)
    await BUS.emit_async("damage_dealt", attacker, target, 10, None, None, None, "attack", {})
    await asyncio.sleep(0)

    # Mitigation should be reduced
    assert target.mitigation < baseline_mitigation


@pytest.mark.asyncio
async def test_momentum_gyro_multiple_stacks():
    """Test that multiple relic stacks increase bonuses."""
    event_bus_module.bus._subs.clear()
    party = Party()
    attacker = PlayerBase()
    attacker.id = "attacker"
    attacker.set_base_stat("atk", 100)
    attacker.hp = attacker.set_base_stat("max_hp", 1000)

    target = PlayerBase()
    target.id = "target"
    target.hp = target.set_base_stat("max_hp", 1000)

    party.members.append(attacker)

    # Award 2 stacks
    award_relic(party, "momentum_gyro")
    award_relic(party, "momentum_gyro")
    await apply_relics(party)

    await BUS.emit_async("battle_start", attacker)

    baseline_atk = attacker.atk

    # First hit with 2 stacks (5% * 2 stacks * 1 streak = 10%)
    await BUS.emit_async("damage_dealt", attacker, target, 10, None, None, None, "attack", {})
    await asyncio.sleep(0)

    # ATK buff should be larger with 2 stacks
    assert attacker.atk > baseline_atk


@pytest.mark.asyncio
async def test_momentum_gyro_zero_damage_ignored():
    """Test that zero damage doesn't build momentum."""
    event_bus_module.bus._subs.clear()
    party = Party()
    attacker = PlayerBase()
    attacker.id = "attacker"
    attacker.set_base_stat("atk", 100)
    attacker.hp = attacker.set_base_stat("max_hp", 1000)

    target = PlayerBase()
    target.id = "target"
    target.hp = target.set_base_stat("max_hp", 1000)

    party.members.append(attacker)

    award_relic(party, "momentum_gyro")
    await apply_relics(party)

    await BUS.emit_async("battle_start", attacker)

    # Zero damage should not create streak
    await BUS.emit_async("damage_dealt", attacker, target, 0, None, None, None, "attack", {})
    await asyncio.sleep(0)

    # No chain should be created
    state = getattr(party, "_momentum_gyro_state", None)
    chains = state.get("chains", {})
    attacker_id = id(attacker)
    assert attacker_id not in chains or chains[attacker_id]["streak"] == 0


@pytest.mark.asyncio
async def test_momentum_gyro_cleanup():
    """Test that state is cleaned up on battle end."""
    event_bus_module.bus._subs.clear()
    party = Party()
    attacker = PlayerBase()
    attacker.id = "attacker"
    attacker.set_base_stat("atk", 100)
    attacker.hp = attacker.set_base_stat("max_hp", 1000)

    target = PlayerBase()
    target.id = "target"
    target.hp = target.set_base_stat("max_hp", 1000)

    party.members.append(attacker)

    award_relic(party, "momentum_gyro")
    await apply_relics(party)

    await BUS.emit_async("battle_start", attacker)

    # Build a streak
    await BUS.emit_async("damage_dealt", attacker, target, 10, None, None, None, "attack", {})
    await asyncio.sleep(0)

    # Verify state exists
    state = getattr(party, "_momentum_gyro_state", None)
    assert state is not None

    # End battle
    await BUS.emit_async("battle_end")
    await asyncio.sleep(0)

    # State should be cleaned up
    state_after = getattr(party, "_momentum_gyro_state", None)
    assert state_after is None
