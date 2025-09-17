import asyncio
from math import isclose

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
    async def use_ultimate(self) -> bool:
        if not self.ultimate_ready:
            return False
        self.ultimate_charge = 0
        self.ultimate_ready = False
        await BUS.emit_async("ultimate_used", self)
        return True


def test_bent_dagger_kill_trigger():
    event_bus_module.bus._subs.clear()
    party = Party()
    member = PlayerBase()
    enemy = PlayerBase()
    member.set_base_stat('atk', 100)
    enemy.hp = enemy.set_base_stat('max_hp', 10)
    party.members.append(member)
    award_relic(party, "bent_dagger")
    apply_relics(party)
    enemy.hp = 0
    BUS.emit("damage_taken", enemy, member, 10)
    assert member.atk == int(100 * 1.03 * 1.01)


def test_bent_dagger_kill_trigger_stacks():
    event_bus_module.bus._subs.clear()
    party = Party()
    member = PlayerBase()
    enemy = PlayerBase()
    member.set_base_stat('atk', 100)
    enemy.hp = enemy.set_base_stat('max_hp', 10)
    party.members.append(member)
    award_relic(party, "bent_dagger")
    award_relic(party, "bent_dagger")
    apply_relics(party)
    enemy.hp = 0
    BUS.emit("damage_taken", enemy, member, 10)
    expected = int(100 * 1.03 * 1.03 * 1.01 * 1.01)
    assert member.atk == expected


def test_lucky_button_stacks():
    party = Party()
    member = PlayerBase()
    member.set_base_stat('crit_rate', 0.1)
    party.members.append(member)
    award_relic(party, "lucky_button")
    award_relic(party, "lucky_button")
    apply_relics(party)
    assert isclose(party.members[0].crit_rate, 0.1 * 1.03 * 1.03)


@pytest.mark.parametrize("copies", [1, 2, 3])
def test_vengeful_pendant_reflects(copies: int) -> None:
    event_bus_module.bus._subs.clear()
    party = Party()
    ally = PlayerBase()
    enemy = PlayerBase()
    ally.id = "ally"
    enemy.id = "enemy"
    ally.hp = 100
    enemy.hp = 100
    party.members.append(ally)
    for _ in range(copies):
        award_relic(party, "vengeful_pendant")
    apply_relics(party)
    BUS.emit("damage_taken", ally, enemy, 20)
    assert enemy.hp == 100 - int(20 * 0.15 * copies)


def test_guardian_charm_targets_lowest_hp():
    party = Party()
    low = PlayerBase()
    high = PlayerBase()
    low.hp = low.set_base_stat('max_hp', 50)
    high.hp = high.set_base_stat('max_hp', 100)
    party.members.extend([low, high])
    award_relic(party, "guardian_charm")
    apply_relics(party)
    assert low.defense == int(50 * 1.2)
    assert high.defense == 50


def test_guardian_charm_stacks():
    party = Party()
    low = PlayerBase()
    high = PlayerBase()
    low.hp = low.set_base_stat('max_hp', 50)
    high.hp = high.set_base_stat('max_hp', 100)
    party.members.extend([low, high])
    award_relic(party, "guardian_charm")
    award_relic(party, "guardian_charm")
    apply_relics(party)
    assert low.defense == int(50 * (1 + 0.2 * 2))
    assert high.defense == 50


def test_herbal_charm_heals_each_turn():
    event_bus_module.bus._subs.clear()
    party = Party()
    member = PlayerBase()
    member.hp = 50
    member.set_base_stat('max_hp', 100)
    party.members.append(member)
    award_relic(party, "herbal_charm")
    apply_relics(party)
    BUS.emit("turn_start")
    assert member.hp == 50 + int(100 * 0.005)


def test_herbal_charm_stacks():
    event_bus_module.bus._subs.clear()
    party = Party()
    member = PlayerBase()
    member.hp = 50
    member.set_base_stat('max_hp', 100)
    party.members.append(member)
    award_relic(party, "herbal_charm")
    award_relic(party, "herbal_charm")
    apply_relics(party)
    BUS.emit("turn_start")
    assert member.hp == 50 + 2 * int(100 * 0.005)


def test_tattered_flag_buffs_survivors_on_death():
    event_bus_module.bus._subs.clear()
    party = Party()
    survivor = PlayerBase()
    victim = PlayerBase()
    survivor.set_base_stat('atk', 100)
    victim.hp = victim.set_base_stat('max_hp', 10)
    party.members.extend([survivor, victim])
    award_relic(party, "tattered_flag")
    apply_relics(party)
    victim.hp = 0
    BUS.emit("damage_taken", victim, survivor, 10)
    assert survivor.atk == int(100 * 1.03)


def test_tattered_flag_stacks():
    event_bus_module.bus._subs.clear()
    party = Party()
    survivor = PlayerBase()
    victim = PlayerBase()
    survivor.set_base_stat('atk', 100)
    victim.hp = victim.set_base_stat('max_hp', 10)
    party.members.extend([survivor, victim])
    award_relic(party, "tattered_flag")
    award_relic(party, "tattered_flag")
    apply_relics(party)
    victim.hp = 0
    BUS.emit("damage_taken", victim, survivor, 10)
    assert survivor.atk == int(100 * 1.03 * 1.03)


def test_shiny_pebble_first_hit_mitigation():
    event_bus_module.bus._subs.clear()
    party = Party()
    ally = PlayerBase()
    enemy = PlayerBase()
    party.members.append(ally)
    award_relic(party, "shiny_pebble")
    apply_relics(party)
    events: list[tuple] = []
    BUS.subscribe("relic_effect", lambda *a: events.append(a))
    BUS.emit("damage_taken", ally, enemy, 10)
    assert isclose(ally.mitigation, 103)
    assert events[0][0] == "shiny_pebble"
    assert events[0][2] == "mitigation_burst"
    assert events[0][3] == 3
    assert isclose(events[0][4]["mitigation_multiplier"], 1.03)
    BUS.emit("turn_start")
    assert isclose(ally.mitigation, 100)


def test_shiny_pebble_stacks():
    event_bus_module.bus._subs.clear()
    party = Party()
    ally = PlayerBase()
    enemy = PlayerBase()
    party.members.append(ally)
    award_relic(party, "shiny_pebble")
    award_relic(party, "shiny_pebble")
    apply_relics(party)
    events: list[tuple] = []
    BUS.subscribe("relic_effect", lambda *a: events.append(a))
    BUS.emit("damage_taken", ally, enemy, 10)
    assert isclose(ally.mitigation, 106)
    assert events[0][0] == "shiny_pebble"
    assert events[0][2] == "mitigation_burst"
    assert events[0][3] == 6
    assert isclose(events[0][4]["mitigation_multiplier"], 1.06)
    BUS.emit("turn_start")
    assert isclose(ally.mitigation, 100)


def test_threadbare_cloak_shield_scales_with_stacks():
    party = Party()
    a = PlayerBase()
    a.hp = a.set_base_stat('max_hp', 100)
    party.members.append(a)

    award_relic(party, "threadbare_cloak")
    apply_relics(party)
    assert a.hp == 100 + int(100 * 0.03)

    award_relic(party, "threadbare_cloak")
    apply_relics(party)
    assert a.hp == 100 + int(100 * 0.03 * 2)


def test_threadbare_cloak_applies_each_battle():
    event_bus_module.bus._subs.clear()
    party = Party()
    a = PlayerBase()
    a.hp = a.set_base_stat('max_hp', 100)
    party.members.append(a)

    award_relic(party, "threadbare_cloak")
    apply_relics(party)
    assert a.hp == 100 + int(100 * 0.03)

    BUS.emit("battle_end", a)
    a.hp = a.set_base_stat('max_hp', 100)
    apply_relics(party)
    assert a.hp == 100 + int(100 * 0.03)


def test_lucky_button_missed_crit():
    event_bus_module.bus._subs.clear()
    party = Party()
    a = PlayerBase()
    a.set_base_stat('crit_rate', 0.1)
    a.set_base_stat('crit_damage', 2.0)
    party.members.append(a)
    award_relic(party, "lucky_button")
    apply_relics(party)
    BUS.emit("crit_missed", a, None)
    BUS.emit("turn_start")
    assert isclose(a.crit_rate, 0.1 * 1.03 + 0.005, rel_tol=1e-4)
    assert isclose(a.crit_damage, 2.0 + 0.05, rel_tol=1e-4)
    BUS.emit("turn_end")
    assert isclose(a.crit_rate, 0.1 * 1.03, rel_tol=1e-4)
    assert isclose(a.crit_damage, 2.0, rel_tol=1e-4)


def test_old_coin_gold_and_discount():
    event_bus_module.bus._subs.clear()
    party = Party()
    award_relic(party, "old_coin")
    apply_relics(party)
    BUS.emit("gold_earned", 100)
    assert party.gold == int(100 * 0.03)
    BUS.emit("shop_purchase", 100)
    assert party.gold == int(100 * 0.03) + int(100 * 0.03)
    BUS.emit("shop_purchase", 100)
    assert party.gold == int(100 * 0.03) + int(100 * 0.03)


def test_wooden_idol_resist_buff():
    event_bus_module.bus._subs.clear()
    party = Party()
    a = PlayerBase()
    a.set_base_stat('effect_resistance', 1.0)
    party.members.append(a)
    award_relic(party, "wooden_idol")
    apply_relics(party)
    BUS.emit("debuff_resisted", a)
    BUS.emit("turn_start")
    assert isclose(a.effect_resistance, 1.03 + 0.01)
    BUS.emit("turn_end")
    assert isclose(a.effect_resistance, 1.03)


def test_pocket_manual_tenth_hit(monkeypatch):
    event_bus_module.bus._subs.clear()
    party = Party()
    a = PlayerBase()
    b = PlayerBase()
    b.hp = b._base_max_hp = 100
    party.members.append(a)
    award_relic(party, "pocket_manual")
    apply_relics(party)

    monkeypatch.setattr(Aftertaste, "rolls", lambda self: [self.base_pot])

    async def fake_apply_damage(self, amount, attacker=None):
        self.hp -= amount
        return amount

    monkeypatch.setattr(Stats, "apply_damage", fake_apply_damage, raising=False)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    for _ in range(9):
        BUS.emit("hit_landed", a, b, 100)
        loop.run_until_complete(asyncio.sleep(0))
    assert b.hp == 100
    BUS.emit("hit_landed", a, b, 100)
    loop.run_until_complete(asyncio.sleep(0))
    assert b.hp == 100 - int(100 * 0.03)


def test_pocket_manual_tenth_hit_stacks(monkeypatch):
    event_bus_module.bus._subs.clear()
    party = Party()
    a = PlayerBase()
    b = PlayerBase()
    b.hp = b._base_max_hp = 100
    party.members.append(a)
    award_relic(party, "pocket_manual")
    award_relic(party, "pocket_manual")
    apply_relics(party)

    monkeypatch.setattr(Aftertaste, "rolls", lambda self: [self.base_pot])

    async def fake_apply_damage(self, amount, attacker=None):
        self.hp -= amount
        return amount

    monkeypatch.setattr(Stats, "apply_damage", fake_apply_damage, raising=False)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    for _ in range(9):
        BUS.emit("hit_landed", a, b, 100)
        loop.run_until_complete(asyncio.sleep(0))
    assert b.hp == 100
    BUS.emit("hit_landed", a, b, 100)
    loop.run_until_complete(asyncio.sleep(0))
    stacks = party.relics.count("pocket_manual")
    assert b.hp == 100 - int(100 * 0.03 * stacks) * stacks


def test_arcane_flask_shields():
    event_bus_module.bus._subs.clear()
    party = Party()
    a = DummyPlayer()
    a.hp = 50
    a._base_max_hp = 100
    party.members.append(a)
    award_relic(party, "arcane_flask")
    apply_relics(party)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def fire():
        a.add_ultimate_charge(15)
        await a.use_ultimate()
        await asyncio.sleep(0)

    loop.run_until_complete(fire())
    assert a.hp == 50 + int(100 * 0.2)


def test_echo_bell_repeats_first_action():
    event_bus_module.bus._subs.clear()
    party = Party()
    a = PlayerBase()
    b = PlayerBase()
    b.hp = 100
    party.members.append(a)
    award_relic(party, "echo_bell")
    apply_relics(party)
    BUS.emit("battle_start")
    b.hp -= 20
    BUS.emit("action_used", a, b, 20)
    assert b.hp == 100 - 20 - int(20 * 0.15)
    b.hp -= 20
    BUS.emit("action_used", a, b, 20)
    assert b.hp == 100 - 20 - int(20 * 0.15) - 20
