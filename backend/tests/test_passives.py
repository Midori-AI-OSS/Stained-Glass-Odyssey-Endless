from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from autofighter.passives import PassiveRegistry
from autofighter.stats import BUS, Stats
from plugins import PluginLoader
from plugins.characters.player import Player
from plugins.event_bus import bus
from plugins.passives.normal.ixia_tiny_titan import IxiaTinyTitan


def test_passive_discovery():
    loader = PluginLoader(required=["passive"])
    loader.discover(Path(__file__).resolve().parents[1] / "plugins" / "passives")
    passives = loader.get_plugins("passive")
    assert "luna_lunar_reservoir" in passives


@pytest.mark.asyncio
async def test_passive_trigger_and_stack():
    registry = PassiveRegistry()
    player = Player()
    # Use luna_lunar_reservoir to test passive stacking behavior
    player.passives = ["luna_lunar_reservoir"] * 3
    # Trigger action_taken (luna_lunar_reservoir uses action_taken to gain charges)
    await registry.trigger("action_taken", player, action_name="slash")
    # Verify the passive was triggered and charge accumulated
    # The passive system tracks stacks, but charges are cumulative not multiplicative
    from plugins.passives.normal.luna_lunar_reservoir import LunaLunarReservoir
    entity_id = id(player)
    charge = LunaLunarReservoir._charge_points.get(entity_id, 0)
    # With 3 stacks, each action adds charge once (shared state)
    assert charge > 0, "Passive should have accumulated some charge"
    # Clean up
    LunaLunarReservoir._charge_points.clear()


@pytest.mark.asyncio
async def test_ixia_tiny_titan_hot_respects_vitality_and_emits_event():
    ixia = IxiaTinyTitan()
    target = Stats()
    target.id = "ixia_target"
    target.max_hp = 500
    target.hp = 300
    target.vitality = 1.5
    initial_hp = target.hp

    IxiaTinyTitan._vitality_bonuses.clear()
    try:
        entity_id = id(target)
        IxiaTinyTitan._vitality_bonuses[entity_id] = 0.5

        expected_hot = int(0.5 * target.max_hp * 0.02)
        expected_heal = int(expected_hot * target.vitality * target.vitality)

        events: list[tuple[Stats, Stats, int, str, str]] = []

        def _heal(target_obj, healer_obj, amount, source_type, source_name):
            events.append((target_obj, healer_obj, amount, source_type, source_name))

        BUS.subscribe("heal_received", _heal)

        try:
            await ixia.on_turn_end(target)
            await bus._process_batches_internal()
        finally:
            BUS.unsubscribe("heal_received", _heal)

        assert target.hp == min(initial_hp + expected_heal, target.max_hp)
        assert events, "Expected heal_received event"

        event_target, event_healer, event_amount, event_type, event_source = events[-1]
        assert event_target is target
        assert event_healer is target
        assert event_amount == expected_heal
        assert event_type == "hot"
        assert event_source == ixia.id
    finally:
        IxiaTinyTitan._vitality_bonuses.clear()
