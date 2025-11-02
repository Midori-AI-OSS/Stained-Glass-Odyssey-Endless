# ruff: noqa: E402
"""Test Graviton Locket relic effects."""

import asyncio
from pathlib import Path
import sys

import pytest

_PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if _PROJECT_ROOT not in sys.path:
    sys.path.append(_PROJECT_ROOT)

from autofighter.party import Party
from autofighter.relics import apply_relics
from autofighter.relics import award_relic
import autofighter.stats as stats_module
from autofighter.stats import BUS
from plugins.characters._base import PlayerBase
from plugins.characters.foe_base import FoeBase
import plugins.event_bus as event_bus_module


class DummyFoe(FoeBase):
    """Minimal foe for testing."""

    id: str = "test_foe"
    name: str = "Test Foe"
    rank: str = "normal"


@pytest.fixture(autouse=True)
def battle_active():
    """Ensure battle is active for all tests."""
    stats_module.set_battle_active(True)
    yield
    stats_module.set_battle_active(False)


@pytest.mark.asyncio
async def test_graviton_locket_applies_gravity_debuff_to_enemies():
    """Test that Graviton Locket applies SPD and defense debuffs to enemies."""
    event_bus_module.bus._subs.clear()

    party = Party()
    player = PlayerBase()
    player.id = "test-player"
    party.members.append(player)

    foe = DummyFoe()
    foe.id = "test-foe"

    # Award 1 stack of Graviton Locket
    award_relic(party, "graviton_locket")
    await apply_relics(party)

    # Capture relic effect events
    relic_events: list[tuple[str, dict[str, object]]] = []

    def _capture_relic_effect(
        relic_id: str,
        recipient: object,
        event_name: str,
        value: int,
        payload: dict[str, object],
        *_extra: object,
    ) -> None:
        if relic_id == "graviton_locket":
            relic_events.append((event_name, payload))

    BUS.subscribe("relic_effect", _capture_relic_effect)

    # Get initial foe stats
    initial_spd = foe.spd
    initial_defense = foe.defense

    # Trigger battle_start
    await BUS.emit_async("battle_start", foe)
    await asyncio.sleep(0)

    # Verify gravity debuff was applied
    assert foe.spd < initial_spd, "SPD should be reduced by gravity"
    assert foe.defense < initial_defense, "Defense should be reduced by gravity"

    # Verify the reduction amounts (1 stack = 30% SPD, 12% DEF reduction)
    expected_spd = initial_spd * 0.70  # 30% reduction
    expected_defense = initial_defense * 0.88  # 12% reduction

    # Allow for floating point comparison tolerance
    assert abs(foe.spd - expected_spd) < 1, f"Expected SPD ~{expected_spd}, got {foe.spd}"
    assert abs(foe.defense - expected_defense) < 1, f"Expected defense ~{expected_defense}, got {foe.defense}"

    # Verify telemetry was emitted
    gravity_events = [e for e in relic_events if e[0] == "gravity_applied"]
    assert len(gravity_events) == 1, "Should emit gravity_applied event"

    event_name, payload = gravity_events[0]
    assert payload["spd_reduction_pct"] == 30.0, "Should show 30% SPD reduction"
    assert payload["defense_reduction_pct"] == 12.0, "Should show 12% defense reduction"
    assert payload["duration_turns"] == 3, "Duration should be 2 + 1 stack = 3 turns"
    assert payload["stacks"] == 1

    event_bus_module.bus._subs.clear()


@pytest.mark.asyncio
async def test_graviton_locket_hp_drain_while_gravity_active():
    """Test that party loses HP while gravity debuffs are active."""
    event_bus_module.bus._subs.clear()

    party = Party()
    player = PlayerBase()
    player.id = "test-player"
    player.hp = 1000
    player._base_max_hp = 1000
    party.members.append(player)

    foe = DummyFoe()
    foe.id = "test-foe"

    # Award 2 stacks of Graviton Locket
    award_relic(party, "graviton_locket")
    award_relic(party, "graviton_locket")
    await apply_relics(party)

    # Capture HP drain events
    drain_events: list[tuple[str, dict[str, object]]] = []

    def _capture_relic_effect(
        relic_id: str,
        recipient: object,
        event_name: str,
        value: int,
        payload: dict[str, object],
        *_extra: object,
    ) -> None:
        if relic_id == "graviton_locket" and event_name == "hp_drain":
            drain_events.append((event_name, payload))

    BUS.subscribe("relic_effect", _capture_relic_effect)

    # Trigger battle_start to apply gravity
    await BUS.emit_async("battle_start", foe)
    await asyncio.sleep(0)

    initial_hp = player.hp

    # Trigger turn_start (should drain HP)
    await BUS.emit_async("turn_start")
    await asyncio.sleep(0)
    await asyncio.sleep(0)

    # Verify HP was drained (2 stacks = 2% Max HP = 20 HP)
    expected_drain = 20  # 2% of 1000
    expected_hp = initial_hp - expected_drain

    # Player HP should have decreased
    assert player.hp < initial_hp, "HP should be drained while gravity is active"
    assert abs(player.hp - expected_hp) < 5, f"Expected HP ~{expected_hp}, got {player.hp}"

    # Verify drain telemetry
    assert len(drain_events) == 1, "Should emit hp_drain event"
    event_name, payload = drain_events[0]
    assert payload["drain_percentage"] == 2.0, "Should drain 2% (1% per stack)"
    assert payload["stacks"] == 2

    event_bus_module.bus._subs.clear()


@pytest.mark.asyncio
async def test_graviton_locket_no_drain_after_gravity_expires():
    """Test that HP drain stops when all gravity debuffs expire."""
    event_bus_module.bus._subs.clear()

    party = Party()
    player = PlayerBase()
    player.id = "test-player"
    player.hp = 1000
    player._base_max_hp = 1000
    party.members.append(player)

    foe = DummyFoe()
    foe.id = "test-foe"

    # Award 1 stack (duration = 3 turns)
    award_relic(party, "graviton_locket")
    await apply_relics(party)

    # Trigger battle_start
    await BUS.emit_async("battle_start", foe)
    await asyncio.sleep(0)

    # Simulate gravity expiring by setting mod turns to 0
    if hasattr(foe, "effect_manager") and foe.effect_manager:
        for mod in foe.effect_manager.mods:
            if hasattr(mod, "name") and "graviton_locket" in mod.name:
                mod.turns = 0

    initial_hp = player.hp

    # Trigger turn_start after gravity expires
    await BUS.emit_async("turn_start")
    await asyncio.sleep(0)
    await asyncio.sleep(0)

    # HP should not be drained since gravity expired
    assert player.hp == initial_hp, "HP should not drain after gravity expires"

    event_bus_module.bus._subs.clear()


@pytest.mark.asyncio
async def test_graviton_locket_duration_scales_with_stacks():
    """Test that debuff duration increases with stacks."""
    event_bus_module.bus._subs.clear()

    party = Party()
    player = PlayerBase()
    party.members.append(player)

    foe = DummyFoe()

    # Award 3 stacks
    award_relic(party, "graviton_locket")
    award_relic(party, "graviton_locket")
    award_relic(party, "graviton_locket")
    await apply_relics(party)

    # Capture events
    relic_events: list[tuple[str, dict[str, object]]] = []

    def _capture_relic_effect(
        relic_id: str,
        recipient: object,
        event_name: str,
        value: int,
        payload: dict[str, object],
        *_extra: object,
    ) -> None:
        if relic_id == "graviton_locket" and event_name == "gravity_applied":
            relic_events.append((event_name, payload))

    BUS.subscribe("relic_effect", _capture_relic_effect)

    # Trigger battle_start
    await BUS.emit_async("battle_start", foe)
    await asyncio.sleep(0)

    # Verify duration (2 + 3 stacks = 5 turns)
    assert len(relic_events) == 1
    event_name, payload = relic_events[0]
    assert payload["duration_turns"] == 5, "Duration should be 2 + 3 = 5 turns"
    assert abs(payload["spd_reduction_pct"] - 90.0) < 0.01, "SPD reduction should stack (30% × 3)"
    assert abs(payload["defense_reduction_pct"] - 36.0) < 0.01, "DEF reduction should stack (12% × 3)"

    event_bus_module.bus._subs.clear()


@pytest.mark.asyncio
async def test_graviton_locket_cleanup_on_battle_end():
    """Test that all modifiers and subscriptions are cleaned up on battle_end."""
    event_bus_module.bus._subs.clear()

    party = Party()
    player = PlayerBase()
    player.hp = 1000
    player._base_max_hp = 1000
    party.members.append(player)

    foe = DummyFoe()

    award_relic(party, "graviton_locket")
    await apply_relics(party)

    # Trigger battle_start
    await BUS.emit_async("battle_start", foe)
    await asyncio.sleep(0)

    # Verify gravity was applied
    assert hasattr(foe, "effect_manager")

    # Trigger battle_end
    await BUS.emit_async("battle_end", foe)
    await asyncio.sleep(0)

    # Try to drain HP after cleanup
    hp_before_turn = player.hp
    await BUS.emit_async("turn_start")
    await asyncio.sleep(0)
    await asyncio.sleep(0)

    # HP should not be drained after battle_end cleanup
    assert player.hp == hp_before_turn, "No HP drain after battle_end cleanup"

    event_bus_module.bus._subs.clear()


@pytest.mark.asyncio
async def test_graviton_locket_describe():
    """Test the describe method returns correct description."""
    event_bus_module.bus._subs.clear()

    party = Party()
    award_relic(party, "graviton_locket")

    from plugins.relics.graviton_locket import GravitonLocket

    relic = GravitonLocket()

    # Test with 1 stack
    desc1 = relic.describe(1)
    assert "30%" in desc1
    assert "12%" in desc1
    assert "3 turns" in desc1
    assert "1%" in desc1

    # Test with 2 stacks
    desc2 = relic.describe(2)
    assert "60%" in desc2
    assert "24%" in desc2
    assert "4 turns" in desc2
    assert "2%" in desc2

    event_bus_module.bus._subs.clear()


@pytest.mark.asyncio
async def test_graviton_locket_multiple_enemies():
    """Test that gravity is applied to all enemies in a battle."""
    event_bus_module.bus._subs.clear()

    party = Party()
    player = PlayerBase()
    party.members.append(player)

    foe1 = DummyFoe()
    foe1.id = "foe-1"
    foe2 = DummyFoe()
    foe2.id = "foe-2"

    award_relic(party, "graviton_locket")
    await apply_relics(party)

    # Capture gravity application events
    gravity_events = []

    def _capture(relic_id, recipient, event_name, value, payload, *_extra):
        if relic_id == "graviton_locket" and event_name == "gravity_applied":
            gravity_events.append(payload)

    BUS.subscribe("relic_effect", _capture)

    # Apply gravity to both enemies
    initial_spd1 = foe1.spd
    initial_spd2 = foe2.spd

    await BUS.emit_async("battle_start", foe1)
    await BUS.emit_async("battle_start", foe2)
    await asyncio.sleep(0)

    # Verify both enemies were debuffed
    assert foe1.spd < initial_spd1, "Foe 1 should be debuffed"
    assert foe2.spd < initial_spd2, "Foe 2 should be debuffed"
    assert len(gravity_events) == 2, "Should emit event for each enemy"

    event_bus_module.bus._subs.clear()
