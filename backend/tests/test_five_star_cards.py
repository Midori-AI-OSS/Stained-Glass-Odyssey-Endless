import asyncio
from pathlib import Path
import random
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
import llms.torch_checker as torch_checker

from autofighter.party import Party
from autofighter.stats import BUS
from plugins.cards.phantom_ally import PhantomAlly
from plugins.cards.reality_split import RealitySplit
from plugins.cards.temporal_shield import TemporalShield
from plugins.foes._base import FoeBase
from plugins.players.ally import Ally
from plugins.players.becca import Becca


@pytest.mark.asyncio
async def test_phantom_ally_summon_lifecycle(monkeypatch):
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)
    a = Ally()
    a.id = "a"
    b = Becca()
    b.id = "b"
    party = Party(members=[a, b])
    await PhantomAlly().apply(party)
    assert len(party.members) == 3
    # Check that one member is a phantom summon
    phantom_found = False
    for member in party.members:
        if hasattr(member, "summon_type") and member.summon_type == "phantom":
            phantom_found = True
            break
    assert phantom_found

    # Test cleanup - emit battle end to trigger summon removal
    BUS.emit("battle_end", FoeBase())
    assert len(party.members) == 2


@pytest.mark.asyncio
async def test_temporal_shield_damage_reduction(monkeypatch):
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)
    member = Ally()
    member.id = "a"
    party = Party(members=[member])
    await TemporalShield().apply(party)
    base_mit = member.mitigation
    monkeypatch.setattr(random, "random", lambda: 0.4)
    BUS.emit("turn_start")
    assert member.mitigation >= base_mit * 50
    await member.effect_manager.cleanup(member)
    monkeypatch.setattr(random, "random", lambda: 0.6)
    BUS.emit("turn_start")
    assert member.mitigation == base_mit


@pytest.mark.asyncio
async def test_reality_split_afterimage(monkeypatch):
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)
    a1 = Ally()
    a1.id = "a1"
    a2 = Becca()
    a2.id = "a2"
    party = Party(members=[a1, a2])
    await RealitySplit().apply(party)
    f1 = FoeBase()
    f1.id = "f1"
    f2 = FoeBase()
    f2.id = "f2"
    BUS.emit("battle_start", f1)
    BUS.emit("battle_start", f2)
    monkeypatch.setattr(random, "choice", lambda seq: a1)
    monkeypatch.setattr(random, "random", lambda: 1.0)
    BUS.emit("turn_start")
    BUS.emit("hit_landed", a1, f1, 100, "attack", "test")
    await asyncio.sleep(0)
    loss1 = f1.max_hp - f1.hp
    loss2 = f2.max_hp - f2.hp
    assert loss1 > 0 and loss1 == loss2
