"""Test suite for Event Horizon relic."""

import pytest

from autofighter.party import Party
from autofighter.stats import BUS
from plugins.characters._base import PlayerBase
from plugins.characters.foe_base import FoeBase
from plugins.relics.event_horizon import EventHorizon

"""Test suite for Event Horizon relic."""




def create_fresh_party():
    """Create a fresh test party with two members."""
    p = Party()
    p.members = []

    # Create two allies
    for i in range(2):
        ally = PlayerBase()
        ally.id = f"ally_{i}"
        ally.hp = 1000
        ally.max_hp = 1000
        ally.atk = 100
        ally.defense = 50
        p.members.append(ally)

    return p


def create_fresh_foes():
    """Create fresh test foes."""
    foe_list = []
    for i in range(2):
        foe = FoeBase()
        foe.id = f"foe_{i}"
        foe.hp = 500
        foe.max_hp = 500
        foe.atk = 80
        foe.defense = 40
        foe_list.append(foe)
    return foe_list


@pytest.mark.asyncio
async def test_event_horizon_basic_pulse():
    """Test basic gravity pulse mechanics."""
    party = create_fresh_party()
    foes = create_fresh_foes()
    relic = EventHorizon()
    party.relics = [relic.id]

    await relic.apply(party)

    # Simulate foes starting their turns (to populate foe cache)
    for foe in foes:
        await BUS.emit_async("turn_start", foe)

    # Track events
    events = []

    async def track_event(relic_id, entity, effect_type, value, metadata):
        events.append({
            "relic_id": relic_id,
            "entity": entity,
            "effect_type": effect_type,
            "value": value,
            "metadata": metadata,
        })

    BUS.subscribe("relic_effect", track_event)

    try:
        # Simulate ally turn start
        ally = party.members[0]
        await BUS.emit_async("turn_start", ally)

        # Should have 2 gravity_pulse events (one per foe) + 1 self_drain event
        assert len(events) == 3

        # Check gravity pulse events
        pulse_events = [e for e in events if e["effect_type"] == "gravity_pulse"]
        assert len(pulse_events) == 2

        for pulse in pulse_events:
            assert pulse["relic_id"] == "event_horizon"
            assert pulse["entity"] in foes
            # 6% of 500 HP = 30 damage
            assert pulse["value"] == 30
            assert pulse["metadata"]["stacks"] == 1
            assert pulse["metadata"]["damage_percentage"] == 6

        # Check self-drain event
        drain_events = [e for e in events if e["effect_type"] == "self_drain"]
        assert len(drain_events) == 1
        assert drain_events[0]["entity"] == ally
        # 3% of 1000 Max HP = 30 damage
        assert drain_events[0]["value"] == 30
        assert drain_events[0]["metadata"]["stacks"] == 1
        assert drain_events[0]["metadata"]["drain_percentage"] == 3
    finally:
        BUS.unsubscribe("relic_effect", track_event)
        relic.clear_subscriptions(party)


@pytest.mark.asyncio
async def test_event_horizon_multiple_stacks():
    """Test gravity pulse with multiple stacks."""
    party = create_fresh_party()
    foes = create_fresh_foes()
    relic = EventHorizon()
    party.relics = [relic.id, relic.id, relic.id]  # 3 stacks

    await relic.apply(party)

    # Populate foe cache
    for foe in foes:
        await BUS.emit_async("turn_start", foe)

    events = []

    async def track_event(relic_id, entity, effect_type, value, metadata):
        events.append({
            "effect_type": effect_type,
            "value": value,
            "metadata": metadata,
        })

    BUS.subscribe("relic_effect", track_event)

    try:
        ally = party.members[0]
        await BUS.emit_async("turn_start", ally)

        # Check gravity pulse events (3 stacks = 18% damage)
        pulse_events = [e for e in events if e["effect_type"] == "gravity_pulse"]
        for pulse in pulse_events:
            # 18% of 500 HP = 90 damage
            assert pulse["value"] == 90
            assert pulse["metadata"]["stacks"] == 3
            assert pulse["metadata"]["damage_percentage"] == 18

        # Check self-drain event (3 stacks = 9% drain)
        drain_events = [e for e in events if e["effect_type"] == "self_drain"]
        assert len(drain_events) == 1
        # 9% of 1000 Max HP = 90 damage
        assert drain_events[0]["value"] == 90
        assert drain_events[0]["metadata"]["stacks"] == 3
        assert drain_events[0]["metadata"]["drain_percentage"] == 9
    finally:
        BUS.unsubscribe("relic_effect", track_event)
        relic.clear_subscriptions(party)


@pytest.mark.asyncio
async def test_event_horizon_minimum_damage():
    """Test minimum damage of 1 per stack."""
    party = create_fresh_party()
    relic = EventHorizon()
    party.relics = [relic.id, relic.id]  # 2 stacks

    await relic.apply(party)

    # Create a foe with very low HP
    low_hp_foe = FoeBase()
    low_hp_foe.id = "low_hp_foe"
    low_hp_foe.hp = 5  # Very low HP
    low_hp_foe.max_hp = 100

    # Populate foe cache with low HP foe
    await BUS.emit_async("turn_start", low_hp_foe)

    events = []

    async def track_event(relic_id, entity, effect_type, value, metadata):
        if effect_type == "gravity_pulse":
            events.append(value)

    BUS.subscribe("relic_effect", track_event)

    try:
        ally = party.members[0]
        await BUS.emit_async("turn_start", ally)

        # 12% of 5 HP = 0.6, should be rounded to 1 minimum
        assert len(events) == 1
        assert events[0] >= 1
    finally:
        BUS.unsubscribe("relic_effect", track_event)
        relic.clear_subscriptions(party)


@pytest.mark.asyncio
async def test_event_horizon_no_living_foes():
    """Test that pulse is skipped when no living foes exist."""
    party = create_fresh_party()
    relic = EventHorizon()
    party.relics = [relic.id]

    await relic.apply(party)

    # Create dead foes
    dead_foe = FoeBase()
    dead_foe.id = "dead_foe"
    dead_foe.hp = 0  # Dead
    dead_foe.max_hp = 100

    # Populate foe cache with dead foe
    await BUS.emit_async("turn_start", dead_foe)

    events = []

    async def track_event(relic_id, entity, effect_type, value, metadata):
        events.append(effect_type)

    BUS.subscribe("relic_effect", track_event)

    try:
        ally = party.members[0]
        await BUS.emit_async("turn_start", ally)

        # Should not emit any events since no living foes
        assert len(events) == 0
    finally:
        BUS.unsubscribe("relic_effect", track_event)
        relic.clear_subscriptions(party)


@pytest.mark.asyncio
async def test_event_horizon_foe_turns_ignored():
    """Test that foe turns don't trigger gravity pulses."""
    party = create_fresh_party()
    foes = create_fresh_foes()
    relic = EventHorizon()
    party.relics = [relic.id]

    await relic.apply(party)

    events = []

    async def track_event(relic_id, entity, effect_type, value, metadata):
        events.append(effect_type)

    BUS.subscribe("relic_effect", track_event)

    try:
        # Foe turn should only add to cache, not trigger pulse
        await BUS.emit_async("turn_start", foes[0])

        # Should not emit any events
        assert len(events) == 0
    finally:
        BUS.unsubscribe("relic_effect", track_event)
        relic.clear_subscriptions(party)


@pytest.mark.asyncio
async def test_event_horizon_extra_turns():
    """Test that extra turns trigger additional pulses."""
    party = create_fresh_party()
    foes = create_fresh_foes()
    relic = EventHorizon()
    party.relics = [relic.id]

    await relic.apply(party)

    # Populate foe cache
    for foe in foes:
        await BUS.emit_async("turn_start", foe)

    events = []

    async def track_event(relic_id, entity, effect_type, value, metadata):
        events.append(effect_type)

    BUS.subscribe("relic_effect", track_event)

    try:
        ally = party.members[0]

        # First turn
        await BUS.emit_async("turn_start", ally)
        first_turn_events = len(events)

        # Extra turn (event fires again)
        await BUS.emit_async("turn_start", ally)
        second_turn_events = len(events)

        # Should have double the events after extra turn
        assert second_turn_events == first_turn_events * 2
    finally:
        BUS.unsubscribe("relic_effect", track_event)
        relic.clear_subscriptions(party)


@pytest.mark.asyncio
async def test_event_horizon_battle_end_cleanup():
    """Test that foe cache is cleared on battle end."""
    party = create_fresh_party()
    foes = create_fresh_foes()
    relic = EventHorizon()
    party.relics = [relic.id]

    await relic.apply(party)

    # Populate foe cache
    for foe in foes:
        await BUS.emit_async("turn_start", foe)

    state = getattr(party, "_event_horizon_state", None)
    assert state is not None
    assert len(state["foes"]) == 2

    # Trigger battle end
    await BUS.emit_async("battle_end", foes[0])

    # Foe cache should be cleared
    assert len(state["foes"]) == 0

    relic.clear_subscriptions(party)


@pytest.mark.asyncio
async def test_event_horizon_ally_no_hp():
    """Test that dead allies don't trigger pulses."""
    party = create_fresh_party()
    foes = create_fresh_foes()
    relic = EventHorizon()
    party.relics = [relic.id]

    await relic.apply(party)

    # Populate foe cache
    for foe in foes:
        await BUS.emit_async("turn_start", foe)

    events = []

    async def track_event(relic_id, entity, effect_type, value, metadata):
        events.append(effect_type)

    BUS.subscribe("relic_effect", track_event)

    try:
        # Set ally HP to 0
        ally = party.members[0]
        ally.hp = 0

        # Dead ally turn should not trigger pulse
        await BUS.emit_async("turn_start", ally)

        # Should not emit any events
        assert len(events) == 0
    finally:
        BUS.unsubscribe("relic_effect", track_event)
        relic.clear_subscriptions(party)


@pytest.mark.asyncio
async def test_event_horizon_describe():
    """Test the describe method with different stack counts."""
    relic = EventHorizon()

    # 1 stack
    desc1 = relic.describe(1)
    assert "6%" in desc1
    assert "3%" in desc1
    assert "minimum 1" in desc1

    # 3 stacks
    desc3 = relic.describe(3)
    assert "18%" in desc3
    assert "9%" in desc3
    assert "minimum 3" in desc3
