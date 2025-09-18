import asyncio
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from autofighter.passives import PassiveRegistry
from autofighter.stats import BUS
from autofighter.stats import set_enrage_percent
from plugins import PluginLoader
from plugins.players.player import Player


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

    # Monkeypatch the registry's copy of the class, not the imported one
    registry_room_heal_cls = registry._registry["room_heal"]
    monkeypatch.setattr(registry_room_heal_cls, "amount", 10, raising=False)

    set_enrage_percent(0.5)
    await registry.trigger("battle_end", player)

    # Wait for batched events to be processed
    await asyncio.sleep(0.1)  # Wait for batch processing

    set_enrage_percent(0.0)
    BUS.unsubscribe("heal_received", _heal)

    assert amounts == [5]
    assert player.hp == 95
