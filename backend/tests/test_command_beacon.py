"""Tests for Command Beacon relic mechanics."""

import asyncio

import pytest

from autofighter.party import Party
from autofighter.relics import apply_relics
from autofighter.relics import award_relic
from autofighter.stats import BUS
from autofighter.stats import Stats
from autofighter.stats import set_battle_active


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

        set_battle_active(True)

        # Trigger turn_start with a party member (simulating ally turn)
        await BUS.emit_async("turn_start", party.members[0])
        await asyncio.sleep(0)

        # Fastest ally (member[1] with SPD=10) should pay the cost
        assert len(cost_events) == 1
        assert cost_events[0]["entity"] is party.members[1]

    finally:
        set_battle_active(False)
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

    set_battle_active(True)
    try:
        # Trigger turn_start with a party member (simulating ally turn)
        await BUS.emit_async("turn_start", party.members[0])
        await asyncio.sleep(0)

        for idx in (0, 2):
            member = party.members[idx]
            mgr = getattr(member, "effect_manager", None)
            assert mgr is not None

            mod_id = f"command_beacon_spd_{id(member)}"
            mods = [mod for mod in mgr.mods if mod.id == mod_id]
            assert len(mods) == 1
            mod = mods[0]
            assert mod.multipliers is not None
            assert mod.multipliers.get("spd") == pytest.approx(1.15, rel=0.001)

        fastest_mgr = getattr(party.members[1], "effect_manager", None)
        if fastest_mgr is not None:
            mod_id = f"command_beacon_spd_{id(party.members[1])}"
            assert [mod for mod in fastest_mgr.mods if mod.id == mod_id] == []

    finally:
        set_battle_active(False)
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

    set_battle_active(True)
    try:
        # Trigger turn_start with a party member (simulating ally turn)
        await BUS.emit_async("turn_start", party.members[0])
        await asyncio.sleep(0)

        # Fastest ally should have lost 3% HP (multiplicative scaling with one stack)
        expected_hp = 1000 - int(1000 * (1 - (0.97 ** 1)))
        assert party.members[1].hp == expected_hp

        # Other ally should not lose HP
        assert party.members[0].hp == 1000

    finally:
        set_battle_active(False)
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

    set_battle_active(True)
    try:
        # Trigger turn_start with a party member (simulating ally turn)
        await BUS.emit_async("turn_start", party.members[0])
        await asyncio.sleep(0)

        member = party.members[0]
        mgr = getattr(member, "effect_manager", None)
        assert mgr is not None

        mod_id = f"command_beacon_spd_{id(member)}"
        mods = [mod for mod in mgr.mods if mod.id == mod_id]
        assert len(mods) == 1
        mod = mods[0]
        assert mod.multipliers is not None
        assert mod.multipliers.get("spd") == pytest.approx(1.15 ** 2, rel=0.001)

        # Fastest ally should have multiplicative HP cost (1 - 0.97 ** stacks)
        expected_hp = 1000 - int(1000 * (1 - (0.97 ** 2)))
        assert party.members[1].hp == expected_hp

    finally:
        set_battle_active(False)
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

    set_battle_active(True)
    try:
        # Trigger turn_start with a party member (simulating ally turn)
        await BUS.emit_async("turn_start", party.members[0])
        await asyncio.sleep(0)

        member = party.members[0]
        mgr = getattr(member, "effect_manager", None)
        assert mgr is not None

        mod_id = f"command_beacon_spd_{id(member)}"
        mods = [mod for mod in mgr.mods if mod.id == mod_id]
        assert len(mods) == 1

        active_effect_names = [effect.name for effect in member.get_active_effects()]
        assert mod_id in active_effect_names

        # Trigger turn_end
        await BUS.emit_async("turn_end", party)
        await asyncio.sleep(0)

        mgr = getattr(member, "effect_manager", None)
        if mgr is not None:
            assert all(mod.id != mod_id for mod in mgr.mods)

        active_effect_names = [effect.name for effect in member.get_active_effects()]
        assert mod_id not in active_effect_names

    finally:
        set_battle_active(False)
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
        set_battle_active(True)

        # Trigger turn_start with a party member (simulating ally turn)
        await BUS.emit_async("turn_start", party.members[1])
        await asyncio.sleep(0)

        # Should only buff 1 ally (member[2]), not the dead one
        assert len(buff_events) == 1
        assert buff_events[0]["count"] == 1

        alive_member = party.members[2]
        alive_mgr = getattr(alive_member, "effect_manager", None)
        assert alive_mgr is not None
        alive_mod_id = f"command_beacon_spd_{id(alive_member)}"
        assert any(mod.id == alive_mod_id for mod in alive_mgr.mods)

        dead_member = party.members[0]
        dead_mgr = getattr(dead_member, "effect_manager", None)
        if dead_mgr is not None:
            dead_mod_id = f"command_beacon_spd_{id(dead_member)}"
            assert all(mod.id != dead_mod_id for mod in dead_mgr.mods)

    finally:
        set_battle_active(False)
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

        set_battle_active(True)

        # Trigger turn_start with a party member (simulating ally turn)
        await BUS.emit_async("turn_start", party.members[0])
        await asyncio.sleep(0)

        # Should have both cost and coordination events
        event_types = [e["type"] for e in all_events]
        assert "coordination_cost" in event_types
        assert "speed_coordination" in event_types

    finally:
        set_battle_active(False)
        BUS.unsubscribe("relic_effect", _track_events)
        await BUS.emit_async("battle_end", party)
