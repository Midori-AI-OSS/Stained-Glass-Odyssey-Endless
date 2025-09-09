import asyncio
import random

import pytest

from autofighter.party import Party
from autofighter.relics import apply_relics
from autofighter.relics import award_relic
from autofighter.stats import BUS
from autofighter.stats import Stats
from plugins.effects.aftertaste import Aftertaste
import plugins.event_bus as event_bus_module
from plugins.players._base import PlayerBase


class DummyPlayer(Stats):
    def use_ultimate(self) -> bool:
        if not self.ultimate_ready:
            return False
        self.ultimate_charge = 0
        self.ultimate_ready = False
        BUS.emit("ultimate_used", self)
        return True


@pytest.mark.asyncio
async def test_frost_sigil_applies_chill(monkeypatch):
    event_bus_module.bus._subs.clear()
    party = Party()
    a = PlayerBase()
    b = PlayerBase()
    b.hp = b.max_hp = 100
    a.atk = 100
    party.members.append(a)
    award_relic(party, "frost_sigil")
    apply_relics(party)

    monkeypatch.setattr(Aftertaste, "rolls", lambda self: [self.base_pot] * self.hits)

    async def fake_apply_damage(self, amount, attacker=None):
        self.hp -= amount
        return amount

    monkeypatch.setattr(Stats, "apply_damage", fake_apply_damage, raising=False)

    BUS.emit("hit_landed", a, b, 10)
    await asyncio.sleep(0)

    assert b.hp == 100 - int(100 * 0.05)


@pytest.mark.asyncio
async def test_frost_sigil_stacks(monkeypatch):
    event_bus_module.bus._subs.clear()
    party = Party()
    a = PlayerBase()
    b = PlayerBase()
    b.hp = b.max_hp = 100
    a.atk = 100
    party.members.append(a)
    award_relic(party, "frost_sigil")
    award_relic(party, "frost_sigil")
    apply_relics(party)

    monkeypatch.setattr(Aftertaste, "rolls", lambda self: [self.base_pot] * self.hits)

    async def fake_apply_damage(self, amount, attacker=None):
        self.hp -= amount
        return amount

    monkeypatch.setattr(Stats, "apply_damage", fake_apply_damage, raising=False)

    BUS.emit("hit_landed", a, b, 10)
    await asyncio.sleep(0)

    assert b.hp == 100 - int(100 * 0.05) * 2


def test_killer_instinct_grants_extra_turn():
    event_bus_module.bus._subs.clear()
    party = Party()
    a = DummyPlayer()
    b = DummyPlayer()
    b.hp = 10
    party.members.append(a)
    award_relic(party, "killer_instinct")
    apply_relics(party)
    base = a.atk
    a.add_ultimate_charge(15)
    a.use_ultimate()
    assert a.atk > base
    turns: list[PlayerBase] = []
    BUS.subscribe("extra_turn", lambda m: turns.append(m))
    b.hp = 0
    BUS.emit("damage_taken", b, a, 10)
    BUS.emit("turn_end")
    assert turns == [a]
    assert a.atk == base


def test_travelers_charm_buff():
    event_bus_module.bus._subs.clear()
    party = Party()
    a = PlayerBase()
    attacker = PlayerBase()
    a.defense = 100
    a.mitigation = 100
    party.members.append(a)
    award_relic(party, "travelers_charm")
    apply_relics(party)
    BUS.emit("damage_taken", a, attacker, 10)
    BUS.emit("turn_start")
    assert a.defense == 100 + int(100 * 0.25)
    assert a.mitigation == 110
    BUS.emit("turn_end")
    assert a.defense == 100
    assert a.mitigation == 100


def test_timekeepers_hourglass_extra_turn():
    event_bus_module.bus._subs.clear()
    party = Party()
    a = PlayerBase()
    party.members.append(a)
    award_relic(party, "timekeepers_hourglass")
    apply_relics(party)
    turns: list[PlayerBase] = []
    BUS.subscribe("extra_turn", lambda m: turns.append(m))
    orig = random.random
    random.random = lambda: 0.0
    BUS.emit("turn_start")
    random.random = orig
    assert turns == [a]


def test_greed_engine_drains_and_rewards():
    event_bus_module.bus._subs.clear()
    party = Party()
    a = PlayerBase()
    a.hp = a.max_hp = 200
    party.members.append(a)
    award_relic(party, "greed_engine")
    apply_relics(party)
    BUS.emit("turn_start")
    assert a.hp == 200 - int(200 * 0.01)
    BUS.emit("gold_earned", 100)
    assert party.gold == int(100 * 0.5)


def test_greed_engine_stacks():
    event_bus_module.bus._subs.clear()
    party = Party()
    a = PlayerBase()
    a.hp = a.max_hp = 200
    party.members.append(a)
    award_relic(party, "greed_engine")
    award_relic(party, "greed_engine")
    apply_relics(party)
    BUS.emit("turn_start")
    assert a.hp == 200 - int(200 * (0.01 + 0.005))
    BUS.emit("gold_earned", 100)
    assert party.gold == int(100 * (0.5 + 0.25))


def test_stellar_compass_crit_bonus():
    event_bus_module.bus._subs.clear()
    party = Party()
    a = PlayerBase()
    a.atk = 100
    party.members.append(a)
    award_relic(party, "stellar_compass")
    apply_relics(party)
    BUS.emit("crit_hit", a, None, 0)
    assert a.atk == int(100 * 1.015)
    BUS.emit("gold_earned", 100)
    assert party.gold == int(100 * 0.015)


def test_stellar_compass_stacks():
    event_bus_module.bus._subs.clear()
    party = Party()
    a = PlayerBase()
    a.atk = 100
    party.members.append(a)
    award_relic(party, "stellar_compass")
    award_relic(party, "stellar_compass")
    apply_relics(party)
    BUS.emit("crit_hit", a, None, 0)
    assert a.atk == int(100 * (1.015**2))
    BUS.emit("gold_earned", 100)
    assert party.gold == int(100 * 0.03)


def test_echoing_drum_repeats_attack():
    event_bus_module.bus._subs.clear()
    party = Party()
    a = PlayerBase()
    b = PlayerBase()
    b.hp = 100
    party.members.append(a)
    award_relic(party, "echoing_drum")
    apply_relics(party)
    BUS.emit("battle_start")
    b.hp -= 20
    BUS.emit("attack_used", a, b, 20)
    assert b.hp == 100 - 20 - int(20 * 0.25)
    b.hp -= 20
    BUS.emit("attack_used", a, b, 20)
    assert b.hp == 100 - 20 - int(20 * 0.25) - 20


def test_echoing_drum_stacks():
    event_bus_module.bus._subs.clear()
    party = Party()
    a = PlayerBase()
    b = PlayerBase()
    b.hp = 100
    party.members.append(a)
    award_relic(party, "echoing_drum")
    award_relic(party, "echoing_drum")
    apply_relics(party)
    BUS.emit("battle_start")
    b.hp -= 20
    BUS.emit("attack_used", a, b, 20)
    assert b.hp == 100 - 20 - int(20 * 0.25) * 2
