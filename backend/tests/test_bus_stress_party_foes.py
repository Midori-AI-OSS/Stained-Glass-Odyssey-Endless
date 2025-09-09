import asyncio
import contextlib
from pathlib import Path
import random

import pytest

from autofighter.party import Party
from autofighter.stats import BUS
from plugins.plugin_loader import PluginLoader


@pytest.mark.asyncio
async def test_bus_stress_party_foes_async():
    plugins_dir = Path(__file__).resolve().parents[1] / "plugins"
    loader = PluginLoader(BUS, required=["player", "foe", "card", "relic"])
    loader.discover(str(plugins_dir))

    player_plugins = loader.get_plugins("player")
    foe_plugins = loader.get_plugins("foe")
    card_plugins = loader.get_plugins("card")

    random.seed(42)

    party = Party()
    for cls in random.sample(list(player_plugins.values()), 5):
        party.members.append(cls(level=20))

    foe_classes = list(foe_plugins.values())
    foes = [random.choice(foe_classes)(level=18) for _ in range(10)]

    party.relics.extend(["fallback_essence"] * 100)
    party.relics.extend(["herbal_charm"] * 5)
    party.relics.extend(["guardian_charm"] * 25)
    party.relics.extend(["frost_sigil"] * 85)

    for card_cls in card_plugins.values():
        card = card_cls()
        if getattr(card, "stars", 0) == 1:
            party.cards.append(card.id)

    async def slow_handler(*args):
        await asyncio.sleep(0.01)

    BUS.subscribe("damage_dealt", slow_handler)

    heartbeat = 0

    async def ticker():
        nonlocal heartbeat
        while True:
            await asyncio.sleep(0)
            heartbeat += 1

    ticker_task = asyncio.create_task(ticker())

    try:
        BUS.clear_metrics()
        tasks = [
            asyncio.create_task(
                BUS.emit_async(
                    "damage_dealt", member, foe, 1, "attack", None, None, "stress"
                )
            )
            for member in party.members
            for foe in foes
        ]

        await asyncio.wait_for(asyncio.gather(*tasks), timeout=1)

        assert heartbeat > 0

        metrics = BUS.get_performance_metrics()
        assert metrics["damage_dealt"]["count"] == 50
    finally:
        ticker_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await ticker_task
        BUS.unsubscribe("damage_dealt", slow_handler)
