"""Tests for Command Beacon relic mechanics."""

import asyncio

import pytest

from autofighter.party import Party
from autofighter.relics import apply_relics
from autofighter.relics import award_relic
from autofighter.stats import BUS
from autofighter.stats import Stats


@pytest.mark.asyncio
async def test_command_beacon_identifies_fastest_ally():
    """Test that Command Beacon identifies the fastest ally correctly."""
    party = Party(members=[Stats(), Stats(), Stats()])

    # Set different SPD for each member
    party.members[0].set_base_stat("spd", 5)
    party.members[1].set_base_stat("spd", 10)  # Fastest
    party.members[2].set_base_stat("spd", 3)

    # Track who paid the HP cost
    cost_events = []

    def _track_cost(relic_id, entity, effect_type, value, details):
        if relic_id == "command_beacon" and effect_type == "coordination_cost":
            cost_events.append({"entity": entity, "cost": value, "details": details})

    BUS.subscribe("relic_effect", _track_cost)

    try:
        award_relic(party, "command_beacon")
        await apply_relics(party)

        # Trigger turn_start with a party member (simulating ally turn)
        await BUS.emit_async("turn_start", party.members[0])
        await asyncio.sleep(0)

        # Fastest ally (member[1] with SPD=10) should pay the cost
        assert len(cost_events) == 1
        assert cost_events[0]["entity"] is party.members[1]

    finally:
        BUS.unsubscribe("relic_effect", _track_cost)
        await BUS.emit_async("battle_end", party)


@pytest.mark.asyncio
async def test_command_beacon_spd_boost():
    """Test that Command Beacon grants SPD boost to non-fastest allies."""
    party = Party(members=[Stats(), Stats(), Stats()])

    # Set different SPD for each member
    party.members[0].set_base_stat("spd", 5)
    party.members[1].set_base_stat("spd", 10)  # Fastest
    party.members[2].set_base_stat("spd", 3)

    award_relic(party, "command_beacon")
    await apply_relics(party)

    # Record initial SPD
    initial_spd_0 = party.members[0].spd
    initial_spd_1 = party.members[1].spd
    initial_spd_2 = party.members[2].spd

    # Trigger turn_start with a party member (simulating ally turn)
    await BUS.emit_async("turn_start", party.members[0])
    await asyncio.sleep(0)

    # Non-fastest allies should have +15% SPD
    assert party.members[0].spd == pytest.approx(initial_spd_0 * 1.15, rel=0.01)
    assert party.members[1].spd == initial_spd_1  # Fastest, no buff
    assert party.members[2].spd == pytest.approx(initial_spd_2 * 1.15, rel=0.01)

    # Clean up
    await BUS.emit_async("battle_end", party)


@pytest.mark.asyncio
async def test_command_beacon_hp_cost():
    """Test that Command Beacon applies HP cost to fastest ally."""
    party = Party(members=[Stats(), Stats()])

    # Set different SPD and HP
    party.members[0].set_base_stat("spd", 5)
    party.members[0].set_base_stat("max_hp", 1000)
    party.members[0].hp = 1000

    party.members[1].set_base_stat("spd", 10)  # Fastest
    party.members[1].set_base_stat("max_hp", 1000)
    party.members[1].hp = 1000

    award_relic(party, "command_beacon")
    await apply_relics(party)

    # Trigger turn_start with a party member (simulating ally turn)
    await BUS.emit_async("turn_start", party.members[0])
    await asyncio.sleep(0)

    # Fastest ally should have lost 3% HP (30 HP)
    expected_hp = 1000 - 30
    assert party.members[1].hp == expected_hp

    # Other ally should not lose HP
    assert party.members[0].hp == 1000

    # Clean up
    await BUS.emit_async("battle_end", party)


@pytest.mark.asyncio
async def test_command_beacon_multi_stack():
    """Test that Command Beacon scales with multiple stacks."""
    party = Party(members=[Stats(), Stats()])

    # Set different SPD and HP
    party.members[0].set_base_stat("spd", 5)
    party.members[0].set_base_stat("max_hp", 1000)
    party.members[0].hp = 1000

    party.members[1].set_base_stat("spd", 10)  # Fastest
    party.members[1].set_base_stat("max_hp", 1000)
    party.members[1].hp = 1000

    # Award 2 stacks
    award_relic(party, "command_beacon")
    award_relic(party, "command_beacon")
    await apply_relics(party)

    initial_spd_0 = party.members[0].spd

    # Trigger turn_start with a party member (simulating ally turn)
    await BUS.emit_async("turn_start", party.members[0])
    await asyncio.sleep(0)

    # Non-fastest ally should have +30% SPD (2 stacks × 15%)
    assert party.members[0].spd == pytest.approx(initial_spd_0 * 1.30, rel=0.01)

    # Fastest ally should have lost 6% HP (2 stacks × 3%)
    expected_hp = 1000 - 60
    assert party.members[1].hp == expected_hp

    # Clean up
    await BUS.emit_async("battle_end", party)


@pytest.mark.asyncio
async def test_command_beacon_buff_expires_at_turn_end():
    """Test that SPD buffs expire at turn end."""
    party = Party(members=[Stats(), Stats()])

    # Set different SPD
    party.members[0].set_base_stat("spd", 5)
    party.members[1].set_base_stat("spd", 10)  # Fastest

    award_relic(party, "command_beacon")
    await apply_relics(party)

    initial_spd_0 = party.members[0].spd

    # Trigger turn_start with a party member (simulating ally turn)
    await BUS.emit_async("turn_start", party.members[0])
    await asyncio.sleep(0)

    # Should have SPD buff
    assert party.members[0].spd > initial_spd_0

    # Trigger turn_end
    await BUS.emit_async("turn_end", party)
    await asyncio.sleep(0)

    # SPD should revert to initial value
    assert party.members[0].spd == pytest.approx(initial_spd_0, rel=0.01)

    # Clean up
    await BUS.emit_async("battle_end", party)


@pytest.mark.asyncio
async def test_command_beacon_skips_dead_allies():
    """Test that Command Beacon skips dead allies."""
    party = Party(members=[Stats(), Stats(), Stats()])

    # Set different SPD
    party.members[0].set_base_stat("spd", 5)
    party.members[0].hp = 0  # Dead

    party.members[1].set_base_stat("spd", 10)  # Fastest (but alive)
    party.members[1].set_base_stat("max_hp", 1000)
    party.members[1].hp = 1000

    party.members[2].set_base_stat("spd", 8)
    party.members[2].set_base_stat("max_hp", 1000)
    party.members[2].hp = 1000

    award_relic(party, "command_beacon")
    await apply_relics(party)

    # Track who got buffed
    buff_events = []

    def _track_buff(relic_id, entity, effect_type, value, details):
        if relic_id == "command_beacon" and effect_type == "speed_coordination":
            buff_events.append({"coordinator": entity, "count": value, "details": details})

    BUS.subscribe("relic_effect", _track_buff)

    try:
        # Trigger turn_start with a party member (simulating ally turn)
        await BUS.emit_async("turn_start", party.members[1])
        await asyncio.sleep(0)

        # Should only buff 1 ally (member[2]), not the dead one
        assert len(buff_events) == 1
        assert buff_events[0]["count"] == 1

        # Dead ally should not gain SPD buff
        assert party.members[0].spd == party.members[0]._base_spd

    finally:
        BUS.unsubscribe("relic_effect", _track_buff)
        await BUS.emit_async("battle_end", party)


@pytest.mark.asyncio
async def test_command_beacon_coordination_events():
    """Test that Command Beacon emits proper telemetry events."""
    party = Party(members=[Stats(), Stats()])

    # Set different SPD and HP
    party.members[0].set_base_stat("spd", 5)
    party.members[1].set_base_stat("spd", 10)  # Fastest
    party.members[1].set_base_stat("max_hp", 1000)
    party.members[1].hp = 1000

    # Track events
    all_events = []

    def _track_events(relic_id, entity, effect_type, value, details):
        if relic_id == "command_beacon":
            all_events.append({
                "type": effect_type,
                "entity": entity,
                "value": value,
                "details": details,
            })

    BUS.subscribe("relic_effect", _track_events)

    try:
        award_relic(party, "command_beacon")
        await apply_relics(party)

        # Trigger turn_start with a party member (simulating ally turn)
        await BUS.emit_async("turn_start", party.members[0])
        await asyncio.sleep(0)

        # Should have both cost and coordination events
        event_types = [e["type"] for e in all_events]
        assert "coordination_cost" in event_types
        assert "speed_coordination" in event_types

    finally:
        BUS.unsubscribe("relic_effect", _track_events)
        await BUS.emit_async("battle_end", party)
