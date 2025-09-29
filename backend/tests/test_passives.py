from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from autofighter.passives import PassiveRegistry
from autofighter.stats import BUS
from autofighter.stats import Stats
from autofighter.stats import set_enrage_percent
from plugins import PluginLoader
from plugins.characters.player import Player
from plugins.event_bus import bus
from plugins.passives.normal.ixia_tiny_titan import IxiaTinyTitan


def test_passive_discovery():
    loader = PluginLoader(required=["passive"])
    loader.discover(Path(__file__).resolve().parents[1] / "plugins" / "passives")
    passives = loader.get_plugins("passive")
    assert "attack_up" in passives


@pytest.mark.asyncio
async def test_passive_trigger_and_stack():
    registry = PassiveRegistry()
    player = Player()
    player.passives = ["attack_up"] * 5
    await registry.trigger("battle_start", player)
    assert player.atk == 100 + 5 * 5


@pytest.mark.asyncio
async def test_room_heal_trigger():
    registry = PassiveRegistry()
    player = Player()
    player.hp = 900
    player.passives = ["room_heal"] * 10
    await registry.trigger("battle_end", player)
    assert player.hp == 910


@pytest.mark.asyncio
async def test_room_heal_event_and_enrage(monkeypatch):
    # Create a fresh registry to avoid cross-test contamination
    import importlib

    from autofighter import passives
    importlib.reload(passives)

    registry = PassiveRegistry()
    player = Player()
    player.hp = 90
    player.set_base_stat("max_hp", 100)
    player.passives = ["room_heal"]
    amounts: list[int] = []

    def _heal(target, healer, amount, *_args):
        amounts.append(amount)

    BUS.subscribe("heal_received", _heal)
    await bus._process_batches_internal()
    amounts.clear()

    # Monkeypatch the registry's copy of the class, not the imported one
    registry_room_heal_cls = registry._registry["room_heal"]
    monkeypatch.setattr(registry_room_heal_cls, "amount", 10, raising=False)

    set_enrage_percent(0.5)
    await registry.trigger("battle_end", player)

    # Wait for batched events to be processed
    await bus._process_batches_internal()

    set_enrage_percent(0.0)
    BUS.unsubscribe("heal_received", _heal)

    assert amounts and amounts[-1] == 5
    assert player.hp == 95


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
