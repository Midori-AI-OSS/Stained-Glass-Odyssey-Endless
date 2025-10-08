import asyncio
from pathlib import Path
import random
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
import llms.torch_checker as torch_checker

from autofighter.party import Party
from autofighter.stats import BUS
from autofighter.stats import set_battle_active
from plugins.cards.phantom_ally import PhantomAlly
from plugins.cards.reality_split import RealitySplit
from plugins.cards.temporal_shield import TemporalShield
from plugins.characters.ally import Ally
from plugins.characters.becca import Becca
from plugins.characters.foe_base import FoeBase


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
        if hasattr(member, 'summon_type') and member.summon_type == "phantom":
            phantom_found = True
            break
    assert phantom_found

    # Test cleanup - emit battle end to trigger summon removal
    await BUS.emit_async("battle_end", FoeBase())
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
    await BUS.emit_async("turn_start")
    assert member.mitigation >= base_mit * 50
    await member.effect_manager.cleanup(member)
    monkeypatch.setattr(random, "random", lambda: 0.6)
    await BUS.emit_async("turn_start")
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
    events: list[tuple[int, object]] = []

    async def _on_card_effect(card_id, _attacker, effect, amount, extra):
        if card_id == RealitySplit.id and effect == "afterimage_echo":
            events.append((amount, extra))

    BUS.subscribe("card_effect", _on_card_effect)
    set_battle_active(True)
    try:
        await BUS.emit_async("battle_start", f1)
        await BUS.emit_async("battle_start", f2)
        monkeypatch.setattr(random, "choice", lambda seq: a1)
        monkeypatch.setattr(random, "random", lambda: 1.0)
        await BUS.emit_async("turn_start")
        await BUS.emit_async("hit_landed", a1, f1, 100, "attack", "test")
        await asyncio.sleep(0)
        new_events = events[:]
        assert len(new_events) == 2
        for amount, _extra in new_events:
            assert amount == 25
    finally:
        BUS.unsubscribe("card_effect", _on_card_effect)
        await BUS.emit_async("battle_end", f1)
        await BUS.emit_async("battle_end", f2)
        set_battle_active(False)


@pytest.mark.asyncio
async def test_reality_split_single_echo_after_back_to_back_battles(monkeypatch):
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)
    a1 = Ally()
    a1.id = "a1"
    a2 = Becca()
    a2.id = "a2"
    party = Party(members=[a1, a2])
    card = RealitySplit()
    await card.apply(party)
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    monkeypatch.setattr(random, "random", lambda: 1.0)
    foes: list[FoeBase] = []
    foes_round_two: list[FoeBase] = []
    events: list[int] = []

    async def _on_card_effect(card_id, _attacker, effect, amount, _extra):
        if card_id == RealitySplit.id and effect == "afterimage_echo":
            events.append(amount)

    BUS.subscribe("card_effect", _on_card_effect)
    set_battle_active(True)
    try:
        # First battle
        foes = [FoeBase(), FoeBase()]
        for index, foe in enumerate(foes, start=1):
            foe.id = f"f{index}"
            await BUS.emit_async("battle_start", foe)
        await BUS.emit_async("turn_start")
        await BUS.emit_async("hit_landed", a1, foes[0], 100, "attack", "test")
        await asyncio.sleep(0)
        first_batch = events[:]
        assert len(first_batch) == len(foes)
        for amount in first_batch:
            assert amount == 25
        for foe in foes:
            await BUS.emit_async("battle_end", foe)

        await asyncio.sleep(0)

        # Second battle immediately after cleanup
        foes_round_two = [FoeBase(), FoeBase()]
        await card.apply(party)
        for index, foe in enumerate(foes_round_two, start=1):
            foe.id = f"s{index}"
            await BUS.emit_async("battle_start", foe)
        await BUS.emit_async("turn_start")
        await BUS.emit_async("hit_landed", a1, foes_round_two[0], 100, "attack", "test")
        await asyncio.sleep(0)
        second_batch = events[len(first_batch) :]
        assert len(second_batch) == len(foes_round_two)
        for amount in second_batch:
            assert amount == 25
        for foe in foes_round_two:
            await BUS.emit_async("battle_end", foe)
    finally:
        BUS.unsubscribe("card_effect", _on_card_effect)
        for foe in foes_round_two:
            await BUS.emit_async("battle_end", foe)
        for foe in foes:
            await BUS.emit_async("battle_end", foe)
        set_battle_active(False)
