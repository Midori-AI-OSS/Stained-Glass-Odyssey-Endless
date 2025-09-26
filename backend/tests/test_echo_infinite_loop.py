"""Test to reproduce the infinite loop in echo relic effects."""

from __future__ import annotations

import asyncio
from pathlib import Path
import sys

import pytest

_PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if _PROJECT_ROOT not in sys.path:
    sys.path.append(_PROJECT_ROOT)

from autofighter.party import Party  # noqa: E402
from autofighter.relics import apply_relics  # noqa: E402
from autofighter.relics import award_relic  # noqa: E402
from autofighter.stats import BUS  # noqa: E402
import plugins.event_bus as event_bus_module  # noqa: E402
from plugins.characters._base import PlayerBase  # noqa: E402
import plugins.relics.echo_bell as echo_bell_module  # noqa: E402
import plugins.relics.echoing_drum as echoing_drum_module  # noqa: E402


@pytest.mark.asyncio
async def test_echo_relics_infinite_loop_prevention():
    """Test that echo relics don't create infinite loops when stacked."""

    # Clear any existing event subscribers
    event_bus_module.bus._subs.clear()

    # Set up party with multiple echo relics
    party = Party()
    attacker = PlayerBase()
    attacker.id = "player"
    attacker.set_base_stat('atk', 100)
    target = PlayerBase()
    target.id = "target"
    target.set_base_stat('max_hp', 1000)
    target.hp = target.max_hp

    async def fake_damage(amount, *_args, **_kwargs):
        target.hp -= amount
        return amount

    target.apply_damage = fake_damage
    party.members.append(attacker)

    # Award multiple echo relics to increase chances of infinite loop
    award_relic(party, "echoing_drum")
    award_relic(party, "echo_bell")
    await apply_relics(party)

    relic_events: list[tuple] = []
    BUS.subscribe("relic_effect", lambda *args: relic_events.append(args))

    # Start battle
    await BUS.emit_async("battle_start")

    # Track the number of events emitted
    event_count = 0
    original_emit = BUS.emit_async

    async def counting_emit(event_type, *args, **kwargs):
        nonlocal event_count
        event_count += 1
        # Prevent infinite recursion by limiting events
        if event_count > 100:
            pytest.fail("Infinite loop detected: too many events emitted")
        return await original_emit(event_type, *args, **kwargs)

    BUS.emit_async = counting_emit

    original_random_drum = echoing_drum_module.random.random
    original_random_bell = echo_bell_module.random.random
    echoing_drum_module.random.random = lambda: 0.0
    echo_bell_module.random.random = lambda: 0.0

    try:
        # This should trigger echo effects but not create infinite loop
        initial_hp = target.hp
        await BUS.emit_async("action_used", attacker, target, 100)
        await asyncio.sleep(0.05)

        # Verify damage was applied (original + echo effects)
        assert relic_events, "No relic_effect events recorded"
        assert target.hp < initial_hp, "No damage was applied"

        # Verify we didn't hit the infinite loop limit
        assert event_count <= 100, f"Too many events emitted: {event_count}"

        print(f"Event count: {event_count}")  # For debugging

    finally:
        # Restore original emit function
        BUS.emit_async = original_emit
        echoing_drum_module.random.random = original_random_drum
        echo_bell_module.random.random = original_random_bell


@pytest.mark.asyncio
async def test_echo_relics_with_timeout():
    """Test echo relics with a timeout to catch infinite loops."""

    # Clear any existing event subscribers
    event_bus_module.bus._subs.clear()

    # Set up party with echo relics
    party = Party()
    attacker = PlayerBase()
    attacker.id = "player"
    attacker.set_base_stat('atk', 100)
    target = PlayerBase()
    target.id = "target"
    target.hp = target.set_base_stat('max_hp', 1000)
    party.members.append(attacker)

    award_relic(party, "echoing_drum")
    award_relic(party, "echo_bell")
    await apply_relics(party)

    await BUS.emit_async("battle_start")

    try:
        # This should complete within 1 second, not timeout
        await asyncio.wait_for(
            BUS.emit_async("action_used", attacker, target, 100),
            timeout=1.0
        )
    except asyncio.TimeoutError:
        pytest.fail("Echo relic processing timed out - infinite loop detected")
