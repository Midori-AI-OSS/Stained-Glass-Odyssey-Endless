import asyncio
import sys
import types
from unittest.mock import patch

import pytest

from autofighter.party import Party
from autofighter.stats import BUS
from autofighter.stats import set_battle_active
from plugins.cards.arc_lightning import ArcLightning
import plugins.event_bus as event_bus_module
from plugins.foes._base import FoeBase
from plugins.players._base import PlayerBase


@pytest.fixture(autouse=True)
def disable_llms(monkeypatch):
    stub = types.ModuleType("llms")
    torch_checker = types.ModuleType("llms.torch_checker")
    torch_checker.is_torch_available = lambda: False
    stub.torch_checker = torch_checker
    original_llms = sys.modules.get("llms")
    original_checker = sys.modules.get("llms.torch_checker")
    monkeypatch.setitem(sys.modules, "llms", stub)
    monkeypatch.setitem(sys.modules, "llms.torch_checker", torch_checker)
    try:
        yield
    finally:
        if original_llms is not None:
            monkeypatch.setitem(sys.modules, "llms", original_llms)
        else:
            monkeypatch.delitem(sys.modules, "llms", raising=False)
        if original_checker is not None:
            monkeypatch.setitem(sys.modules, "llms.torch_checker", original_checker)
        else:
            monkeypatch.delitem(sys.modules, "llms.torch_checker", raising=False)


@pytest.mark.asyncio
async def test_arc_lightning_chains_damage() -> None:
    event_bus_module.bus._subs.clear()
    attacker = PlayerBase()
    foe1 = FoeBase()
    foe2 = FoeBase()
    party = Party([attacker])
    card = ArcLightning()
    await card.apply(party)
    set_battle_active(True)
    try:
        await BUS.emit_async("battle_start", foe1)
        await BUS.emit_async("battle_start", foe2)
        await BUS.emit_async("battle_start", attacker)
        initial = foe2.hp
        with patch("plugins.cards.arc_lightning.random.choice", return_value=foe2):
            await BUS.emit_async("hit_landed", attacker, foe1, 100, "attack")
            await asyncio.sleep(0.05)
        assert foe2.hp < initial
    finally:
        set_battle_active(False)
