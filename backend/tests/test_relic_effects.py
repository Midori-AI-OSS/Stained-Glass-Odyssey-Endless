import asyncio
from math import isclose

import pytest

import autofighter.stats as stats_module
from autofighter.party import Party
from autofighter.relics import apply_relics
from autofighter.relics import award_relic
from autofighter.stats import BUS
from autofighter.stats import Stats
from autofighter.summons.manager import SummonManager
from plugins.effects.aftertaste import Aftertaste
import plugins.event_bus as event_bus_module
from plugins.characters._base import PlayerBase
from plugins.characters.becca import Becca
from plugins.characters.luna import Luna
import plugins.relics._base as relic_base_module
import plugins.relics.echo_bell as echo_bell_module


class DummyPlayer(Stats):
    async def use_ultimate(self) -> bool:
        if not self.ultimate_ready:
            return False
        self.ultimate_charge = 0
        self.ultimate_ready = False
        await BUS.emit_async("ultimate_used", self)
        return True


@pytest.mark.asyncio
async def test_bent_dagger_kill_trigger():
    event_bus_module.bus._subs.clear()
    party = Party()
    member = PlayerBase()
    enemy = PlayerBase()
    member.set_base_stat('atk', 100)
    enemy.hp = enemy.set_base_stat('max_hp', 10)
    party.members.append(member)
    award_relic(party, "bent_dagger")
    await apply_relics(party)
    enemy.hp = 0
    await BUS.emit_async("damage_taken", enemy, member, 10)
    assert member.atk == int(100 * 1.03 * 1.01)


@pytest.mark.asyncio
async def test_bent_dagger_kill_trigger_stacks():
    event_bus_module.bus._subs.clear()
    party = Party()
    member = PlayerBase()
    enemy = PlayerBase()
    member.set_base_stat('atk', 100)
    enemy.hp = enemy.set_base_stat('max_hp', 10)
    party.members.append(member)
    award_relic(party, "bent_dagger")
    award_relic(party, "bent_dagger")
    await apply_relics(party)
    enemy.hp = 0
    await BUS.emit_async("damage_taken", enemy, member, 10)
    expected = int(100 * 1.03 * 1.03 * 1.01 * 1.01)
    assert member.atk == expected


@pytest.mark.asyncio
async def test_lucky_button_stacks():
    party = Party()
    member = PlayerBase()
    member.set_base_stat('crit_rate', 0.1)
    party.members.append(member)
    award_relic(party, "lucky_button")
    award_relic(party, "lucky_button")
    await apply_relics(party)
    assert isclose(party.members[0].crit_rate, 0.1 * 1.03 * 1.03)


@pytest.mark.parametrize("copies", [1, 2, 3])
@pytest.mark.asyncio
async def test_vengeful_pendant_reflects(copies: int) -> None:
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
    await apply_relics(party)
    events: list[tuple] = []

    def capture(*args: object) -> None:
        events.append(args)

    BUS.subscribe("relic_effect", capture)
    original_state = stats_module._BATTLE_ACTIVE
    stats_module._BATTLE_ACTIVE = True
    try:
        await BUS.emit_async("damage_taken", ally, enemy, 20)
        await asyncio.sleep(0)
    finally:
        BUS.unsubscribe("relic_effect", capture)
        stats_module._BATTLE_ACTIVE = original_state
    assert events
    assert events[0][0] == "vengeful_pendant"
    assert events[0][2] == "damage_reflection"
    assert events[0][3] == max(1, int(20 * 0.15 * copies))


@pytest.mark.asyncio
async def test_vengeful_pendant_reflects_minimum_damage() -> None:
    event_bus_module.bus._subs.clear()
    party = Party()
    ally = PlayerBase()
    enemy = PlayerBase()
    ally.id = "ally"
    enemy.id = "enemy"
    ally.hp = 100
    enemy.hp = 100
    party.members.append(ally)
    award_relic(party, "vengeful_pendant")
    await apply_relics(party)
    events: list[tuple] = []

    def capture(*args: object) -> None:
        events.append(args)

    BUS.subscribe("relic_effect", capture)
    original_state = stats_module._BATTLE_ACTIVE
    stats_module._BATTLE_ACTIVE = True
    try:
        await BUS.emit_async("damage_taken", ally, enemy, 1)
        await asyncio.sleep(0)
    finally:
        BUS.unsubscribe("relic_effect", capture)
        stats_module._BATTLE_ACTIVE = original_state

    assert events
    assert events[0][0] == "vengeful_pendant"
    assert events[0][2] == "damage_reflection"
    assert events[0][3] == 1
    assert enemy.hp == 99


@pytest.mark.asyncio
async def test_guardian_charm_targets_lowest_hp():
    party = Party()
    low = PlayerBase()
    high = PlayerBase()
    low.hp = low.set_base_stat('max_hp', 50)
    high.hp = high.set_base_stat('max_hp', 100)
    party.members.extend([low, high])
    award_relic(party, "guardian_charm")
    await apply_relics(party)
    assert low.defense == int(50 * 1.2)
    assert high.defense == 50


@pytest.mark.asyncio
async def test_guardian_charm_stacks():
    party = Party()
    low = PlayerBase()
    high = PlayerBase()
    low.hp = low.set_base_stat('max_hp', 50)
    high.hp = high.set_base_stat('max_hp', 100)
    party.members.extend([low, high])
    award_relic(party, "guardian_charm")
    award_relic(party, "guardian_charm")
    await apply_relics(party)
    assert low.defense == int(50 * (1 + 0.2 * 2))
    assert high.defense == 50


@pytest.mark.asyncio
async def test_herbal_charm_heals_each_turn():
    event_bus_module.bus._subs.clear()
    party = Party()
    member = PlayerBase()
    member.hp = 50
    member.set_base_stat('max_hp', 100)
    party.members.append(member)
    award_relic(party, "herbal_charm")
    await apply_relics(party)
    await BUS.emit_async("turn_start")
    assert member.hp == 50 + int(100 * 0.005)


@pytest.mark.asyncio
async def test_herbal_charm_stacks():
    event_bus_module.bus._subs.clear()
    party = Party()
    member = PlayerBase()
    member.hp = 50
    member.set_base_stat('max_hp', 100)
    party.members.append(member)
    award_relic(party, "herbal_charm")
    award_relic(party, "herbal_charm")
    await apply_relics(party)
    await BUS.emit_async("turn_start")
    assert member.hp == 50 + 2 * int(100 * 0.005)


@pytest.mark.asyncio
async def test_tattered_flag_buffs_survivors_on_death():
    event_bus_module.bus._subs.clear()
    party = Party()
    survivor = PlayerBase()
    victim = PlayerBase()
    survivor.set_base_stat('atk', 100)
    victim.hp = victim.set_base_stat('max_hp', 10)
    party.members.extend([survivor, victim])
    award_relic(party, "tattered_flag")
    await apply_relics(party)
    victim.hp = 0
    await BUS.emit_async("damage_taken", victim, survivor, 10)
    assert survivor.atk == int(100 * 1.03)


@pytest.mark.asyncio
async def test_tattered_flag_stacks():
    event_bus_module.bus._subs.clear()
    party = Party()
    survivor = PlayerBase()
    victim = PlayerBase()
    survivor.set_base_stat('atk', 100)
    victim.hp = victim.set_base_stat('max_hp', 10)
    party.members.extend([survivor, victim])
    award_relic(party, "tattered_flag")
    award_relic(party, "tattered_flag")
    await apply_relics(party)
    victim.hp = 0
    await BUS.emit_async("damage_taken", victim, survivor, 10)
    assert survivor.atk == int(100 * 1.03 * 1.03)


@pytest.mark.asyncio
async def test_shiny_pebble_first_hit_mitigation():
    event_bus_module.bus._subs.clear()
    party = Party()
    ally = PlayerBase()
    enemy = PlayerBase()
    party.members.append(ally)
    award_relic(party, "shiny_pebble")
    await apply_relics(party)
    events: list[tuple] = []
    BUS.subscribe("relic_effect", lambda *a: events.append(a))
    await BUS.emit_async("damage_taken", ally, enemy, 10)
    assert isclose(ally.mitigation, 103)
    assert events[0][0] == "shiny_pebble"
    assert events[0][2] == "mitigation_burst"
    assert events[0][3] == 3
    assert isclose(events[0][4]["mitigation_multiplier"], 1.03)
    await BUS.emit_async("turn_start")
    assert isclose(ally.mitigation, 100)


@pytest.mark.asyncio
async def test_shiny_pebble_stacks():
    event_bus_module.bus._subs.clear()
    party = Party()
    ally = PlayerBase()
    enemy = PlayerBase()
    party.members.append(ally)
    award_relic(party, "shiny_pebble")
    award_relic(party, "shiny_pebble")
    await apply_relics(party)
    events: list[tuple] = []
    BUS.subscribe("relic_effect", lambda *a: events.append(a))
    await BUS.emit_async("damage_taken", ally, enemy, 10)
    assert isclose(ally.mitigation, 106)
    assert events[0][0] == "shiny_pebble"
    assert events[0][2] == "mitigation_burst"
    assert events[0][3] == 6
    assert isclose(events[0][4]["mitigation_multiplier"], 1.06)
    await BUS.emit_async("turn_start")
    assert isclose(ally.mitigation, 100)


@pytest.mark.asyncio
async def test_threadbare_cloak_shield_scales_with_stacks():
    party = Party()
    a = PlayerBase()
    a.hp = a.set_base_stat('max_hp', 100)
    party.members.append(a)

    award_relic(party, "threadbare_cloak")
    await apply_relics(party)
    assert a.hp == 100 + int(100 * 0.03)

    award_relic(party, "threadbare_cloak")
    await apply_relics(party)
    assert a.hp == 100 + int(100 * 0.03 * 2)


@pytest.mark.asyncio
async def test_threadbare_cloak_applies_each_battle():
    event_bus_module.bus._subs.clear()
    party = Party()
    a = PlayerBase()
    a.hp = a.set_base_stat('max_hp', 100)
    party.members.append(a)

    award_relic(party, "threadbare_cloak")
    await apply_relics(party)
    assert a.hp == 100 + int(100 * 0.03)

    await BUS.emit_async("battle_end", a)
    a.hp = a.set_base_stat('max_hp', 100)
    await apply_relics(party)
    assert a.hp == 100 + int(100 * 0.03)


@pytest.mark.asyncio
async def test_lucky_button_missed_crit():
    event_bus_module.bus._subs.clear()
    party = Party()
    a = PlayerBase()
    a.set_base_stat('crit_rate', 0.1)
    a.set_base_stat('crit_damage', 2.0)
    party.members.append(a)
    award_relic(party, "lucky_button")
    await apply_relics(party)
    await BUS.emit_async("crit_missed", a, None)
    await BUS.emit_async("turn_start")
    assert isclose(a.crit_rate, 0.1 * 1.03 + 0.005, rel_tol=1e-4)
    assert isclose(a.crit_damage, 2.0 + 0.05, rel_tol=1e-4)
    await BUS.emit_async("turn_end")
    assert isclose(a.crit_rate, 0.1 * 1.03, rel_tol=1e-4)
    assert isclose(a.crit_damage, 2.0, rel_tol=1e-4)


@pytest.mark.asyncio
async def test_old_coin_gold_and_discount():
    event_bus_module.bus._subs.clear()
    party = Party()
    award_relic(party, "old_coin")
    await apply_relics(party)
    await BUS.emit_async("gold_earned", 100)
    assert party.gold == int(100 * 0.03)
    await BUS.emit_async("shop_purchase", 100)
    assert party.gold == int(100 * 0.03) + int(100 * 0.03)
    await BUS.emit_async("shop_purchase", 100)
    assert party.gold == int(100 * 0.03) + int(100 * 0.03)


@pytest.mark.asyncio
async def test_wooden_idol_resist_buff():
    event_bus_module.bus._subs.clear()
    party = Party()
    a = PlayerBase()
    a.set_base_stat('effect_resistance', 1.0)
    party.members.append(a)
    award_relic(party, "wooden_idol")
    await apply_relics(party)
    await BUS.emit_async("debuff_resisted", a)
    await BUS.emit_async("turn_start")
    assert isclose(a.effect_resistance, 1.03 + 0.01)
    await BUS.emit_async("turn_end")
    assert isclose(a.effect_resistance, 1.03)


@pytest.mark.asyncio
async def test_pocket_manual_tenth_hit(monkeypatch):
    event_bus_module.bus._subs.clear()
    party = Party()
    a = PlayerBase()
    b = PlayerBase()
    b.hp = b._base_max_hp = 100
    party.members.append(a)
    award_relic(party, "pocket_manual")
    await apply_relics(party)

    monkeypatch.setattr(Aftertaste, "rolls", lambda self: [self.base_pot])

    async def fake_apply_damage(self, amount, attacker=None):
        self.hp -= amount
        return amount

    monkeypatch.setattr(Stats, "apply_damage", fake_apply_damage, raising=False)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    for _ in range(9):
        await BUS.emit_async("hit_landed", a, b, 100)
        loop.run_until_complete(asyncio.sleep(0))
    assert b.hp == 100
    await BUS.emit_async("hit_landed", a, b, 100)
    loop.run_until_complete(asyncio.sleep(0))
    assert b.hp == 100 - int(100 * 0.03)


@pytest.mark.asyncio
async def test_pocket_manual_tenth_hit_stacks(monkeypatch):
    event_bus_module.bus._subs.clear()
    party = Party()
    a = PlayerBase()
    b = PlayerBase()
    b.hp = b._base_max_hp = 100
    party.members.append(a)
    award_relic(party, "pocket_manual")
    award_relic(party, "pocket_manual")
    await apply_relics(party)

    monkeypatch.setattr(Aftertaste, "rolls", lambda self: [self.base_pot])

    async def fake_apply_damage(self, amount, attacker=None):
        self.hp -= amount
        return amount

    monkeypatch.setattr(Stats, "apply_damage", fake_apply_damage, raising=False)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    for _ in range(9):
        await BUS.emit_async("hit_landed", a, b, 100)
        loop.run_until_complete(asyncio.sleep(0))
    assert b.hp == 100
    await BUS.emit_async("hit_landed", a, b, 100)
    loop.run_until_complete(asyncio.sleep(0))
    stacks = party.relics.count("pocket_manual")
    assert b.hp == 100 - int(100 * 0.03 * stacks) * stacks


@pytest.mark.asyncio
async def test_arcane_flask_shields():
    event_bus_module.bus._subs.clear()
    party = Party()
    a = DummyPlayer()
    a.hp = 50
    a._base_max_hp = 100
    party.members.append(a)
    award_relic(party, "arcane_flask")
    await apply_relics(party)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def fire():
        a.add_ultimate_charge(a.ultimate_charge_max)
        await a.use_ultimate()
        await asyncio.sleep(0)

    loop.run_until_complete(fire())
    assert a.hp == 50 + int(100 * 0.2)


@pytest.mark.asyncio
async def test_echo_bell_aftertaste_trigger(monkeypatch):
    event_bus_module.bus._subs.clear()
    party = Party()
    actor = PlayerBase()
    target = PlayerBase()
    target.hp = 100
    party.members.append(actor)
    award_relic(party, "echo_bell")
    await apply_relics(party)

    triggered_hits: list[int] = []
    created_tasks: list[asyncio.Task] = []

    async def fake_apply(self, *_args, **_kwargs):
        triggered_hits.append(self.hits)
        return [0] * self.hits

    monkeypatch.setattr(Aftertaste, "apply", fake_apply, raising=False)
    monkeypatch.setattr(echo_bell_module.random, "random", lambda: 0.0)
    monkeypatch.setattr(
        relic_base_module,
        "safe_async_task",
        lambda coro: created_tasks.append(asyncio.create_task(coro)) or created_tasks[-1],
    )

    await BUS.emit_async("battle_start")
    await BUS.emit_async("action_used", actor, target, 20)
    if created_tasks:
        await asyncio.gather(*created_tasks)
        created_tasks.clear()
    assert triggered_hits == [1]

    await BUS.emit_async("action_used", actor, target, 20)
    if created_tasks:
        await asyncio.gather(*created_tasks)
        created_tasks.clear()
    assert triggered_hits == [1]


@pytest.mark.asyncio
async def test_arcane_flask_ignores_foe_summons():
    event_bus_module.bus._subs.clear()
    SummonManager.initialize()
    party = Party()
    ally = PlayerBase()
    ally.set_base_stat('max_hp', 500)
    ally.hp = ally.max_hp
    party.members.append(ally)
    award_relic(party, "arcane_flask")
    await apply_relics(party)

    foe = Luna()
    foe.set_base_stat('max_hp', 800)
    foe.hp = foe.max_hp
    foe.hp -= 100
    sword = await SummonManager.create_summon(
        foe,
        summon_type="luna_sword_test",
        source="luna_sword",
        stat_multiplier=1.0,
        force_create=True,
    )
    assert sword is not None
    foe_hp_before = foe.hp
    sword_hp_before = sword.hp
    events: list[tuple] = []

    def capture(*args: object) -> None:
        events.append(args)

    BUS.subscribe("relic_effect", capture)
    try:
        await BUS.emit_async("ultimate_used", foe)
        await asyncio.sleep(0)
    finally:
        BUS.unsubscribe("relic_effect", capture)
        await SummonManager.remove_summon(sword, "test_cleanup")

    assert not events
    assert foe.hp == foe_hp_before
    assert sword.hp == sword_hp_before


@pytest.mark.asyncio
async def test_echoing_drum_ignores_foe_attack_buffs():
    event_bus_module.bus._subs.clear()
    SummonManager.initialize()
    party = Party()
    ally = PlayerBase()
    party.members.append(ally)
    award_relic(party, "echoing_drum")
    await apply_relics(party)

    foe = Becca()
    foe.set_base_stat('atk', 120)
    target = PlayerBase()
    target.set_base_stat('max_hp', 300)
    target.hp = target.max_hp

    events: list[tuple] = []

    def capture(*args: object) -> None:
        events.append(args)

    BUS.subscribe("relic_effect", capture)
    try:
        await BUS.emit_async("attack_used", foe, target, 80)
        await BUS.emit_async("action_used", foe, target, 80)
        await asyncio.sleep(0)
    finally:
        BUS.unsubscribe("relic_effect", capture)

    assert not events

    foe_effects = getattr(foe, "_active_effects", [])
    assert not any(
        getattr(effect, "name", "").startswith("echoing_drum") for effect in foe_effects
    )
    foe_manager = getattr(foe, "effect_manager", None)
    if foe_manager is not None:
        assert not any(
            getattr(mod, "name", "").startswith("echoing_drum") for mod in foe_manager.mods
        )

    summon = await SummonManager.create_summon(
        foe,
        summon_type="becca_jellyfish_test",
        source="becca_menagerie_bond",
        stat_multiplier=1.0,
        force_create=True,
    )
    assert summon is not None
    try:
        summon_effects = getattr(summon, "_active_effects", [])
        assert not any(
            getattr(effect, "name", "").startswith("echoing_drum") for effect in summon_effects
        )
        summon_manager = getattr(summon, "effect_manager", None)
        if summon_manager is not None:
            assert not any(
                getattr(mod, "name", "").startswith("echoing_drum")
                for mod in getattr(summon_manager, "mods", [])
            )
    finally:
        await SummonManager.remove_summon(summon, "test_cleanup")

