import asyncio

import pytest

from autofighter.party import Party
from autofighter.relics import apply_relics, award_relic
from autofighter.stats import BUS
from plugins.characters._base import PlayerBase
from plugins.characters.foe_base import FoeBase
import plugins.event_bus as event_bus_module


@pytest.mark.asyncio
async def test_entropy_mirror_enemy_buff():
    """Test that Entropy Mirror buffs enemy ATK at battle start."""
    event_bus_module.bus._subs.clear()
    party = Party()
    ally = PlayerBase()
    ally.id = "ally"
    ally.hp = ally.set_base_stat("max_hp", 1000)
    party.members.append(ally)

    foe = FoeBase()
    foe.id = "foe"
    foe.set_base_stat("atk", 100)
    foe.hp = foe.set_base_stat("max_hp", 1000)

    award_relic(party, "entropy_mirror")
    await apply_relics(party)

    baseline_atk = foe.atk

    # Trigger battle start with the foe
    await BUS.emit_async("battle_start", foe)
    await asyncio.sleep(0)

    # Foe should have increased ATK (30% increase)
    assert foe.atk > baseline_atk, f"Expected ATK > {baseline_atk}, got {foe.atk}"


@pytest.mark.asyncio
async def test_entropy_mirror_recoil():
    """Test that foes suffer recoil when dealing damage."""
    event_bus_module.bus._subs.clear()
    party = Party()
    ally = PlayerBase()
    ally.id = "ally"
    ally.hp = ally.set_base_stat("max_hp", 1000)
    party.members.append(ally)

    foe = FoeBase()
    foe.id = "foe"
    foe.set_base_stat("atk", 100)
    # Initialize HP properly
    foe.set_base_stat("max_hp", 1000)
    foe._hp = 1000  # Direct assignment to bypass property

    award_relic(party, "entropy_mirror")
    await apply_relics(party)

    # Trigger battle start
    await BUS.emit_async("battle_start", foe)
    await asyncio.sleep(0)

    # Track recoil via events
    recoil_events = []

    async def track_recoil(*args):
        if len(args) >= 3 and args[2] == "recoil_damage":
            recoil_events.append(args)

    BUS.subscribe("relic_effect", track_recoil)

    # Simulate foe dealing 100 damage to ally
    # Recoil should be 10% of 100 = 10 HP
    await BUS.emit_async(
        "damage_dealt", foe, ally, 100, "physical", None, None, "attack", {}
    )
    await asyncio.sleep(0.01)

    # Check that recoil event was emitted
    assert len(recoil_events) > 0, "No recoil events were emitted"
    assert recoil_events[0][3] == 10, f"Expected recoil of 10, got {recoil_events[0][3]}"

    BUS.unsubscribe("relic_effect", track_recoil)


@pytest.mark.asyncio
async def test_entropy_mirror_no_recoil_on_zero_damage():
    """Test that foes don't suffer recoil when dealing zero damage (miss)."""
    event_bus_module.bus._subs.clear()
    party = Party()
    ally = PlayerBase()
    ally.id = "ally"
    ally.hp = ally.set_base_stat("max_hp", 1000)
    party.members.append(ally)

    foe = FoeBase()
    foe.id = "foe"
    foe.hp = foe.set_base_stat("max_hp", 1000)

    award_relic(party, "entropy_mirror")
    await apply_relics(party)

    await BUS.emit_async("battle_start", foe)
    await asyncio.sleep(0)

    foe_hp_before = foe.hp

    # Simulate foe dealing 0 damage (miss)
    await BUS.emit_async(
        "damage_dealt", foe, ally, 0, "physical", None, None, "attack", {}
    )
    await asyncio.sleep(0.01)

    # Foe should not have taken recoil damage
    assert foe.hp == foe_hp_before, f"Expected HP {foe_hp_before}, got {foe.hp}"


@pytest.mark.asyncio
async def test_entropy_mirror_stacks():
    """Test that multiple stacks increase both ATK buff and recoil."""
    event_bus_module.bus._subs.clear()
    party = Party()
    ally = PlayerBase()
    ally.id = "ally"
    ally.hp = ally.set_base_stat("max_hp", 1000)
    party.members.append(ally)

    foe = FoeBase()
    foe.id = "foe"
    foe.set_base_stat("atk", 100)
    foe.set_base_stat("max_hp", 1000)
    foe._hp = 1000  # Direct assignment

    # Award 2 stacks
    award_relic(party, "entropy_mirror")
    award_relic(party, "entropy_mirror")
    await apply_relics(party)

    baseline_atk = foe.atk

    # Trigger battle start
    await BUS.emit_async("battle_start", foe)
    await asyncio.sleep(0)

    # Foe should have +60% ATK (30% × 2 stacks)
    assert foe.atk > baseline_atk

    # Track recoil via events
    recoil_events = []

    async def track_recoil(*args):
        if len(args) >= 3 and args[2] == "recoil_damage":
            recoil_events.append(args)

    BUS.subscribe("relic_effect", track_recoil)

    # Simulate foe dealing 100 damage
    # Recoil should be 20% of 100 = 20 HP (10% × 2 stacks)
    await BUS.emit_async(
        "damage_dealt", foe, ally, 100, "physical", None, None, "attack", {}
    )
    await asyncio.sleep(0.01)

    # Check that recoil event was emitted with correct amount
    assert len(recoil_events) > 0, "No recoil events were emitted"
    assert recoil_events[0][3] == 20, f"Expected recoil of 20, got {recoil_events[0][3]}"

    BUS.unsubscribe("relic_effect", track_recoil)


@pytest.mark.asyncio
async def test_entropy_mirror_no_recoil_on_dead_foe():
    """Test that dead foes don't suffer recoil."""
    event_bus_module.bus._subs.clear()
    party = Party()
    ally = PlayerBase()
    ally.id = "ally"
    ally.hp = ally.set_base_stat("max_hp", 1000)
    party.members.append(ally)

    foe = FoeBase()
    foe.id = "foe"
    foe.set_base_stat("atk", 100)
    foe.hp = 0  # Dead foe
    foe.set_base_stat("max_hp", 1000)

    award_relic(party, "entropy_mirror")
    await apply_relics(party)

    await BUS.emit_async("battle_start", foe)
    await asyncio.sleep(0)

    # Simulate dead foe dealing damage (shouldn't happen, but testing edge case)
    await BUS.emit_async(
        "damage_dealt", foe, ally, 100, "physical", None, None, "attack", {}
    )
    await asyncio.sleep(0.01)

    # Dead foe should remain at 0 HP
    assert foe.hp == 0


@pytest.mark.asyncio
async def test_entropy_mirror_multiple_foes():
    """Test that all foes get buffed at battle start."""
    event_bus_module.bus._subs.clear()
    party = Party()
    ally = PlayerBase()
    ally.id = "ally"
    ally.hp = ally.set_base_stat("max_hp", 1000)
    party.members.append(ally)

    foe1 = FoeBase()
    foe1.id = "foe1"
    foe1.set_base_stat("atk", 100)
    foe1.hp = foe1.set_base_stat("max_hp", 1000)

    foe2 = FoeBase()
    foe2.id = "foe2"
    foe2.set_base_stat("atk", 150)
    foe2.hp = foe2.set_base_stat("max_hp", 1000)

    award_relic(party, "entropy_mirror")
    await apply_relics(party)

    baseline_atk1 = foe1.atk
    baseline_atk2 = foe2.atk

    # Trigger battle start for both foes
    await BUS.emit_async("battle_start", foe1)
    await BUS.emit_async("battle_start", foe2)
    await asyncio.sleep(0)

    # Both foes should have increased ATK
    assert foe1.atk > baseline_atk1
    assert foe2.atk > baseline_atk2


@pytest.mark.asyncio
async def test_entropy_mirror_no_recoil_on_ally_damage():
    """Test that allies don't trigger recoil when dealing damage."""
    event_bus_module.bus._subs.clear()
    party = Party()
    ally = PlayerBase()
    ally.id = "ally"
    ally.hp = ally.set_base_stat("max_hp", 1000)
    party.members.append(ally)

    foe = FoeBase()
    foe.id = "foe"
    foe.hp = foe.set_base_stat("max_hp", 1000)

    award_relic(party, "entropy_mirror")
    await apply_relics(party)

    await BUS.emit_async("battle_start", ally)
    await asyncio.sleep(0)

    ally_hp_before = ally.hp

    # Simulate ally dealing damage to foe (should not trigger recoil on ally)
    await BUS.emit_async(
        "damage_dealt", ally, foe, 100, "physical", None, None, "attack", {}
    )
    await asyncio.sleep(0.01)

    # Ally should not have taken recoil damage
    assert ally.hp == ally_hp_before


@pytest.mark.asyncio
async def test_entropy_mirror_cleanup():
    """Test that state is cleaned up at battle end."""
    event_bus_module.bus._subs.clear()
    party = Party()
    ally = PlayerBase()
    ally.id = "ally"
    ally.hp = ally.set_base_stat("max_hp", 1000)
    party.members.append(ally)

    foe = FoeBase()
    foe.id = "foe"
    foe.set_base_stat("atk", 100)
    foe.hp = foe.set_base_stat("max_hp", 1000)

    award_relic(party, "entropy_mirror")
    await apply_relics(party)

    # Trigger battle start
    await BUS.emit_async("battle_start", foe)
    await asyncio.sleep(0)

    # Check state exists
    assert hasattr(party, "_entropy_mirror_state")
    state = party._entropy_mirror_state
    assert len(state["buffed_foes"]) > 0

    # Trigger battle end
    await BUS.emit_async("battle_end")
    await asyncio.sleep(0)

    # State should be cleared
    assert len(state["buffed_foes"]) == 0
