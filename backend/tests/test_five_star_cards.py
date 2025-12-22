import asyncio
import math
from pathlib import Path
import random
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
import llms.torch_checker as torch_checker

from autofighter.party import Party
from autofighter.stats import BUS, set_battle_active
from plugins.cards.equilibrium_prism import EquilibriumPrism
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


@pytest.mark.asyncio
async def test_equilibrium_prism_redistribution_heals_without_harm(monkeypatch):
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)
    card = EquilibriumPrism()
    frontline = Ally()
    frontline.id = "frontline"
    frontline.max_hp = 1200
    frontline.hp = 1200
    support = Becca()
    support.id = "support"
    support.max_hp = 900
    support.hp = 180
    party = Party(members=[frontline, support])

    await card.apply(party)

    expected_average = (
        (frontline.hp / frontline.max_hp) + (support.hp / support.max_hp)
    ) / 2
    expected_support_hp = min(
        support.max_hp,
        max(support.hp, math.ceil(expected_average * support.max_hp)),
    )

    await BUS.emit_async("turn_start")

    state = getattr(party, "_equilibrium_prism_state", {})
    card_state = state.get(card.id, {}).get("state", {})

    assert frontline.hp == 1200
    assert support.hp == expected_support_hp
    assert card_state.get("tokens") == 1


@pytest.mark.asyncio
async def test_equilibrium_prism_burst_buffs_and_damage(monkeypatch):
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)
    card = EquilibriumPrism()

    a1 = Ally()
    a1.id = "a1"
    a1.max_hp = 1100
    a1.hp = 1100
    a1.atk = 600

    a2 = Becca()
    a2.id = "a2"
    a2.max_hp = 1000
    a2.hp = 1000
    a2.atk = 550

    a3 = Ally()
    a3.id = "a3"
    a3.max_hp = 950
    a3.hp = 950
    a3.atk = 500

    party = Party(members=[a1, a2, a3])

    foe_one = FoeBase()
    foe_one.id = "foe_one"
    foe_one.max_hp = 4200
    foe_one.hp = 4200
    foe_one.last_damage_taken = 0

    foe_two = FoeBase()
    foe_two.id = "foe_two"
    foe_two.max_hp = 6400
    foe_two.hp = 6400
    foe_two.last_damage_taken = 0

    await card.apply(party)

    base_stats = {
        member.id: {
            "crit": member.crit_rate,
            "mit": member.mitigation,
        }
        for member in party.members
    }

    events: list[tuple[str, int | float, dict[str, object], str | None]] = []

    async def _on_card_effect(card_id, actor, effect, amount, extra):
        if card_id == card.id:
            events.append((effect, amount, extra, getattr(actor, "id", None)))

    BUS.subscribe("card_effect", _on_card_effect)
    set_battle_active(True)

    await BUS.emit_async("battle_start", foe_one)
    await BUS.emit_async("battle_start", foe_two)

    try:
        for _ in range(3):
            a2.hp = int(a2.max_hp * 0.2)
            a3.hp = int(a3.max_hp * 0.25)
            await BUS.emit_async("turn_start")

        state = getattr(party, "_equilibrium_prism_state", {})
        card_state = state.get(card.id, {}).get("state", {})
        assert card_state.get("tokens") == 0

        for member in party.members:
            baseline = base_stats[member.id]
            assert member.crit_rate >= baseline["crit"] + 0.5
            assert member.mitigation >= baseline["mit"] * 1.5

        assert foe_two.last_damage_taken > 0
        assert foe_two.hp == foe_two.max_hp - foe_two.last_damage_taken
        assert foe_one.last_damage_taken == 0

        effect_names = {effect for effect, *_ in events}
        assert "balance_burst_damage" in effect_names
        assert "balance_burst_buff" in effect_names
    finally:
        BUS.unsubscribe("card_effect", _on_card_effect)
        await BUS.emit_async("battle_end", foe_one)
        await BUS.emit_async("battle_end", foe_two)
        set_battle_active(False)
