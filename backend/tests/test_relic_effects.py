import asyncio
from math import isclose

import pytest

from autofighter.party import Party
from autofighter.relics import apply_relics
from autofighter.relics import award_relic
import autofighter.stats as stats_module
from autofighter.stats import BUS
from autofighter.stats import Stats
from autofighter.summons.manager import SummonManager
from plugins.characters._base import PlayerBase
from plugins.characters.becca import Becca
from plugins.characters.luna import Luna
from plugins.effects.aftertaste import Aftertaste
import plugins.event_bus as event_bus_module
import plugins.relics._base as relic_base_module
import plugins.relics.echo_bell as echo_bell_module


@pytest.mark.asyncio
async def test_copper_siphon_lifesteal():
    """Test that Copper Siphon heals attacker for 2% of damage dealt."""
    event_bus_module.bus._subs.clear()
    party = Party()
    attacker = PlayerBase()
    target = PlayerBase()
    attacker.hp = attacker.set_base_stat('max_hp', 1000)
    attacker.set_base_stat('atk', 100)
    target.hp = target.set_base_stat('max_hp', 1000)
    party.members.append(attacker)

    # Reduce attacker HP to allow healing
    attacker.hp = 900

    # Award relic and apply
    award_relic(party, "copper_siphon")
    await apply_relics(party)

    # Simulate dealing 100 damage - should heal for 2% = 2 HP
    await BUS.emit_async("action_used", attacker, target, 100)
    await asyncio.sleep(0.01)  # Allow async healing to complete

    # Check that HP increased by 2
    assert attacker.hp == 902, f"Expected HP 902, got {attacker.hp}"


@pytest.mark.asyncio
async def test_copper_siphon_minimum_healing():
    """Test that Copper Siphon heals at least 1 HP even for small damage."""
    event_bus_module.bus._subs.clear()
    party = Party()
    attacker = PlayerBase()
    target = PlayerBase()
    attacker.hp = attacker.set_base_stat('max_hp', 1000)
    attacker.set_base_stat('atk', 100)
    target.hp = target.set_base_stat('max_hp', 1000)
    party.members.append(attacker)

    # Reduce attacker HP to allow healing
    attacker.hp = 900

    # Award relic and apply
    award_relic(party, "copper_siphon")
    await apply_relics(party)

    # Simulate dealing 10 damage - 2% = 0.2, but minimum is 1 HP
    await BUS.emit_async("action_used", attacker, target, 10)
    await asyncio.sleep(0.01)  # Allow async healing to complete

    # Check that HP increased by at least 1
    assert attacker.hp == 901, f"Expected HP 901, got {attacker.hp}"


@pytest.mark.asyncio
async def test_copper_siphon_stacks():
    """Test that multiple Copper Siphon stacks increase lifesteal."""
    event_bus_module.bus._subs.clear()
    party = Party()
    attacker = PlayerBase()
    target = PlayerBase()
    attacker.hp = attacker.set_base_stat('max_hp', 1000)
    attacker.set_base_stat('atk', 100)
    target.hp = target.set_base_stat('max_hp', 1000)
    party.members.append(attacker)

    # Reduce attacker HP to allow healing
    attacker.hp = 900

    # Award 2 stacks of copper_siphon (4% lifesteal)
    award_relic(party, "copper_siphon")
    award_relic(party, "copper_siphon")
    await apply_relics(party)

    # Simulate dealing 100 damage - should heal for 4% = 4 HP
    await BUS.emit_async("action_used", attacker, target, 100)
    await asyncio.sleep(0.01)  # Allow async healing to complete

    # Check that HP increased by 4
    assert attacker.hp == 904, f"Expected HP 904, got {attacker.hp}"


@pytest.mark.asyncio
async def test_copper_siphon_overheal_shields():
    """Test that Copper Siphon converts excess healing to shields."""
    event_bus_module.bus._subs.clear()
    party = Party()
    attacker = PlayerBase()
    target = PlayerBase()
    attacker.hp = attacker.set_base_stat('max_hp', 1000)
    attacker.set_base_stat('atk', 100)
    target.hp = target.set_base_stat('max_hp', 1000)
    party.members.append(attacker)

    # Attacker is at full HP
    attacker.hp = 1000

    # Award relic and apply
    award_relic(party, "copper_siphon")
    await apply_relics(party)

    # Simulate dealing 100 damage - should heal for 2 HP, which becomes shield
    await BUS.emit_async("action_used", attacker, target, 100)
    await asyncio.sleep(0.01)  # Allow async healing to complete

    # Check that shields were applied (HP stays at max, shields increase)
    assert attacker.hp == 1000, f"Expected HP 1000, got {attacker.hp}"
    assert attacker.shields == 2, f"Expected shields 2, got {attacker.shields}"


@pytest.mark.asyncio
async def test_copper_siphon_ignores_zero_damage():
    """Test that Copper Siphon doesn't trigger on zero or negative damage."""
    event_bus_module.bus._subs.clear()
    party = Party()
    attacker = PlayerBase()
    target = PlayerBase()
    attacker.hp = attacker.set_base_stat('max_hp', 1000)
    attacker.set_base_stat('atk', 100)
    target.hp = target.set_base_stat('max_hp', 1000)
    party.members.append(attacker)

    # Reduce attacker HP
    attacker.hp = 900

    # Award relic and apply
    award_relic(party, "copper_siphon")
    await apply_relics(party)

    # Simulate dealing 0 damage - should not heal
    await BUS.emit_async("action_used", attacker, target, 0)
    await asyncio.sleep(0.01)

    # HP should not change
    assert attacker.hp == 900, f"Expected HP 900, got {attacker.hp}"


@pytest.mark.asyncio
async def test_copper_siphon_telemetry():
    """Test that Copper Siphon emits proper telemetry events."""
    event_bus_module.bus._subs.clear()
    party = Party()
    attacker = PlayerBase()
    target = PlayerBase()
    attacker.hp = attacker.set_base_stat('max_hp', 1000)
    attacker.set_base_stat('atk', 100)
    target.hp = target.set_base_stat('max_hp', 1000)
    party.members.append(attacker)

    # Reduce attacker HP
    attacker.hp = 900

    # Award relic and apply
    award_relic(party, "copper_siphon")
    await apply_relics(party)

    # Capture telemetry events
    events: list[tuple] = []

    def capture(*args: object) -> None:
        events.append(args)

    BUS.subscribe("relic_effect", capture)

    # Simulate dealing 100 damage
    await BUS.emit_async("action_used", attacker, target, 100)
    await asyncio.sleep(0.01)

    # Check that telemetry was emitted
    assert len(events) > 0, "Expected telemetry event"
    relic_id, actor, effect_type, value, metadata = events[0]
    assert relic_id == "copper_siphon"
    assert effect_type == "lifesteal"
    assert value == 2  # 2% of 100 damage
    assert metadata["damage_dealt"] == 100
    assert metadata["lifesteal_percentage"] == 2
    assert metadata["stacks"] == 1


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


@pytest.mark.asyncio
async def test_catalyst_vials_dot_healing():
    """Test that Catalyst Vials heals attacker when DoT ticks."""
    event_bus_module.bus._subs.clear()
    party = Party()
    attacker = PlayerBase()
    target = PlayerBase()
    attacker.hp = attacker.set_base_stat('max_hp', 1000)
    attacker.set_base_stat('atk', 100)
    target.hp = target.set_base_stat('max_hp', 1000)
    party.members.append(attacker)

    # Reduce attacker HP to allow healing
    attacker.hp = 900

    # Award relic and apply
    award_relic(party, "catalyst_vials")
    await apply_relics(party)

    # Simulate DoT tick for 20 damage - should heal for 5% = 1 HP (min 1)
    await BUS.emit_async("dot_tick", attacker, target, 20)
    await asyncio.sleep(0.01)  # Allow async healing to complete

    # Check that HP increased by 1
    assert attacker.hp == 901, f"Expected HP 901, got {attacker.hp}"


@pytest.mark.asyncio
async def test_catalyst_vials_effect_hit_buff():
    """Test that Catalyst Vials grants effect hit rate buff."""
    event_bus_module.bus._subs.clear()
    party = Party()
    attacker = PlayerBase()
    target = PlayerBase()
    attacker.hp = attacker.set_base_stat('max_hp', 1000)
    attacker.set_base_stat('atk', 100)
    attacker.set_base_stat('effect_hit_rate', 1.0)
    target.hp = target.set_base_stat('max_hp', 1000)
    party.members.append(attacker)

    # Award relic and apply
    award_relic(party, "catalyst_vials")
    await apply_relics(party)

    # Get initial effect hit rate
    initial_ehr = attacker.effect_hit_rate

    # Simulate DoT tick for 100 damage - should grant +5% effect hit rate
    await BUS.emit_async("dot_tick", attacker, target, 100)
    await asyncio.sleep(0.01)

    # Check that effect hit rate increased
    assert attacker.effect_hit_rate > initial_ehr, f"Expected effect hit rate > {initial_ehr}, got {attacker.effect_hit_rate}"


@pytest.mark.asyncio
async def test_catalyst_vials_stacks():
    """Test that multiple Catalyst Vials stacks increase healing and buff."""
    event_bus_module.bus._subs.clear()
    party = Party()
    attacker = PlayerBase()
    target = PlayerBase()
    attacker.hp = attacker.set_base_stat('max_hp', 1000)
    attacker.set_base_stat('atk', 100)
    target.hp = target.set_base_stat('max_hp', 1000)
    party.members.append(attacker)

    # Reduce attacker HP to allow healing
    attacker.hp = 900

    # Award 2 stacks of catalyst_vials (10% healing)
    award_relic(party, "catalyst_vials")
    award_relic(party, "catalyst_vials")
    await apply_relics(party)

    # Simulate DoT tick for 100 damage - should heal for 10% = 10 HP
    await BUS.emit_async("dot_tick", attacker, target, 100)
    await asyncio.sleep(0.01)

    # Check that HP increased by 10
    assert attacker.hp == 910, f"Expected HP 910, got {attacker.hp}"


@pytest.mark.asyncio
async def test_catalyst_vials_ignores_non_party():
    """Test that Catalyst Vials ignores DoT ticks from non-party members."""
    event_bus_module.bus._subs.clear()
    party = Party()
    attacker = PlayerBase()
    enemy_attacker = PlayerBase()
    target = PlayerBase()
    attacker.hp = attacker.set_base_stat('max_hp', 1000)
    enemy_attacker.hp = enemy_attacker.set_base_stat('max_hp', 1000)
    target.hp = target.set_base_stat('max_hp', 1000)
    party.members.append(attacker)
    # enemy_attacker is NOT in party

    # Reduce enemy_attacker HP
    enemy_attacker.hp = 900

    # Award relic and apply
    award_relic(party, "catalyst_vials")
    await apply_relics(party)

    # Simulate DoT tick from enemy - should not heal
    await BUS.emit_async("dot_tick", enemy_attacker, target, 100)
    await asyncio.sleep(0.01)

    # HP should not change
    assert enemy_attacker.hp == 900, f"Expected HP 900, got {enemy_attacker.hp}"


@pytest.mark.asyncio
async def test_catalyst_vials_ignores_zero_damage():
    """Test that Catalyst Vials doesn't trigger on zero damage."""
    event_bus_module.bus._subs.clear()
    party = Party()
    attacker = PlayerBase()
    target = PlayerBase()
    attacker.hp = attacker.set_base_stat('max_hp', 1000)
    target.hp = target.set_base_stat('max_hp', 1000)
    party.members.append(attacker)

    # Reduce attacker HP
    attacker.hp = 900

    # Award relic and apply
    award_relic(party, "catalyst_vials")
    await apply_relics(party)

    # Simulate DoT tick with 0 damage - should not heal
    await BUS.emit_async("dot_tick", attacker, target, 0)
    await asyncio.sleep(0.01)

    # HP should not change
    assert attacker.hp == 900, f"Expected HP 900, got {attacker.hp}"


@pytest.mark.asyncio
async def test_catalyst_vials_telemetry():
    """Test that Catalyst Vials emits proper telemetry events."""
    event_bus_module.bus._subs.clear()
    party = Party()
    attacker = PlayerBase()
    target = PlayerBase()
    attacker.hp = attacker.set_base_stat('max_hp', 1000)
    target.hp = target.set_base_stat('max_hp', 1000)
    party.members.append(attacker)

    # Reduce attacker HP
    attacker.hp = 900

    # Award relic and apply
    award_relic(party, "catalyst_vials")
    await apply_relics(party)

    # Capture telemetry events
    events: list[tuple] = []

    def capture(*args: object) -> None:
        events.append(args)

    BUS.subscribe("relic_effect", capture)

    # Simulate DoT tick for 100 damage
    await BUS.emit_async("dot_tick", attacker, target, 100)
    await asyncio.sleep(0.01)

    # Check that telemetry was emitted
    assert len(events) > 0, "Expected telemetry event"
    relic_id, actor, effect_type, value, metadata = events[0]
    assert relic_id == "catalyst_vials"
    assert effect_type == "dot_siphon"
    assert value == 5  # 5% of 100 damage
    assert metadata["dot_damage"] == 100
    assert metadata["heal_percentage"] == 5
    assert metadata["stacks"] == 1


@pytest.mark.asyncio
async def test_safeguard_prism_shield_on_low_hp():
    """Test that Safeguard Prism grants shield when ally drops below 60% HP."""
    event_bus_module.bus._subs.clear()
    party = Party()
    ally = PlayerBase()
    enemy = PlayerBase()
    ally.hp = ally.set_base_stat('max_hp', 1000)
    ally.set_base_stat('atk', 100)
    enemy.hp = enemy.set_base_stat('max_hp', 1000)
    party.members.append(ally)

    # Award relic and apply
    award_relic(party, "safeguard_prism")
    await apply_relics(party)

    # Set HP below threshold (below 60% = below 600)
    ally.hp = 500

    # Simulate damage event
    await BUS.emit_async("damage_taken", ally, enemy, 100)
    await asyncio.sleep(0.01)

    # Should have received shield (15% of 1000 = 150)
    assert ally.shields == 150, f"Expected shields 150, got {ally.shields}"


@pytest.mark.asyncio
async def test_safeguard_prism_mitigation_buff():
    """Test that Safeguard Prism grants mitigation buff."""
    event_bus_module.bus._subs.clear()
    party = Party()
    ally = PlayerBase()
    enemy = PlayerBase()
    ally.hp = ally.set_base_stat('max_hp', 1000)
    ally.set_base_stat('atk', 100)
    ally.set_base_stat('mitigation', 1.0)
    enemy.hp = enemy.set_base_stat('max_hp', 1000)
    party.members.append(ally)

    # Award relic and apply
    award_relic(party, "safeguard_prism")
    await apply_relics(party)

    # Set HP below threshold
    ally.hp = 500

    # Get initial mitigation
    initial_mitigation = ally.mitigation

    # Simulate damage to trigger safeguard
    await BUS.emit_async("damage_taken", ally, enemy, 100)
    await asyncio.sleep(0.01)

    # Should have increased mitigation (+12%)
    assert ally.mitigation > initial_mitigation, f"Expected mitigation > {initial_mitigation}, got {ally.mitigation}"


@pytest.mark.asyncio
async def test_safeguard_prism_stacks():
    """Test that multiple Safeguard Prism stacks increase shield and mitigation."""
    event_bus_module.bus._subs.clear()
    party = Party()
    ally = PlayerBase()
    enemy = PlayerBase()
    ally.hp = ally.set_base_stat('max_hp', 1000)
    enemy.hp = enemy.set_base_stat('max_hp', 1000)
    party.members.append(ally)

    # Award 2 stacks (30% shield, 24% mitigation)
    award_relic(party, "safeguard_prism")
    award_relic(party, "safeguard_prism")
    await apply_relics(party)

    # Set HP below threshold
    ally.hp = 500

    # Simulate damage to trigger safeguard
    await BUS.emit_async("damage_taken", ally, enemy, 100)
    await asyncio.sleep(0.01)

    # Should have received double shield (30% of 1000 = 300)
    assert ally.shields == 300, f"Expected shields 300, got {ally.shields}"


@pytest.mark.asyncio
async def test_safeguard_prism_limited_triggers():
    """Test that Safeguard Prism has limited triggers per stack."""
    event_bus_module.bus._subs.clear()
    party = Party()
    ally = PlayerBase()
    enemy = PlayerBase()
    ally.hp = ally.set_base_stat('max_hp', 1000)
    enemy.hp = enemy.set_base_stat('max_hp', 1000)
    party.members.append(ally)

    # Award 1 stack (1 trigger per ally per battle)
    award_relic(party, "safeguard_prism")
    await apply_relics(party)

    # Trigger safeguard first time
    ally.hp = 500
    await BUS.emit_async("damage_taken", ally, enemy, 100)
    await asyncio.sleep(0.01)

    # Should have received shield
    assert ally.shields == 150, f"Expected shields 150, got {ally.shields}"

    # Reset shields and try to trigger again
    ally.shields = 0
    ally.hp = 400

    await BUS.emit_async("damage_taken", ally, enemy, 100)
    await asyncio.sleep(0.01)

    # Should NOT have received shield (already used 1 trigger)
    assert ally.shields == 0, f"Expected shields 0, got {ally.shields}"


@pytest.mark.asyncio
async def test_safeguard_prism_multiple_stacks_multiple_triggers():
    """Test that multiple stacks allow multiple triggers per ally."""
    event_bus_module.bus._subs.clear()
    party = Party()
    ally = PlayerBase()
    enemy = PlayerBase()
    ally.hp = ally.set_base_stat('max_hp', 1000)
    enemy.hp = enemy.set_base_stat('max_hp', 1000)
    party.members.append(ally)

    # Award 2 stacks (2 triggers per ally per battle)
    award_relic(party, "safeguard_prism")
    award_relic(party, "safeguard_prism")
    await apply_relics(party)

    # Trigger safeguard first time
    ally.hp = 500
    await BUS.emit_async("damage_taken", ally, enemy, 100)
    await asyncio.sleep(0.01)

    # Should have received shield (30% = 300)
    assert ally.shields == 300, f"Expected shields 300, got {ally.shields}"

    # Reset shields and trigger again
    ally.shields = 0
    ally.hp = 400

    await BUS.emit_async("damage_taken", ally, enemy, 100)
    await asyncio.sleep(0.01)

    # Should have received shield again (still have 1 trigger left)
    assert ally.shields == 300, f"Expected shields 300, got {ally.shields}"

    # Reset shields and try a third time
    ally.shields = 0
    ally.hp = 300

    await BUS.emit_async("damage_taken", ally, enemy, 100)
    await asyncio.sleep(0.01)

    # Should NOT have received shield (used all 2 triggers)
    assert ally.shields == 0, f"Expected shields 0, got {ally.shields}"


@pytest.mark.asyncio
async def test_safeguard_prism_above_threshold():
    """Test that Safeguard Prism doesn't trigger above 60% HP."""
    event_bus_module.bus._subs.clear()
    party = Party()
    ally = PlayerBase()
    enemy = PlayerBase()
    ally.hp = ally.set_base_stat('max_hp', 1000)
    enemy.hp = enemy.set_base_stat('max_hp', 1000)
    party.members.append(ally)

    # Award relic and apply
    award_relic(party, "safeguard_prism")
    await apply_relics(party)

    # Set HP to 700 (70% - above threshold)
    ally.hp = 700

    # Simulate damage that keeps HP above 60% (to 650 HP)
    await BUS.emit_async("damage_taken", ally, enemy, 50)
    await asyncio.sleep(0.01)

    # Should NOT have received shield
    assert ally.shields == 0, f"Expected shields 0, got {ally.shields}"


@pytest.mark.asyncio
async def test_safeguard_prism_telemetry():
    """Test that Safeguard Prism emits proper telemetry events."""
    event_bus_module.bus._subs.clear()
    party = Party()
    ally = PlayerBase()
    enemy = PlayerBase()
    ally.hp = ally.set_base_stat('max_hp', 1000)
    enemy.hp = enemy.set_base_stat('max_hp', 1000)
    party.members.append(ally)

    # Award relic and apply
    award_relic(party, "safeguard_prism")
    await apply_relics(party)

    # Capture telemetry events
    events: list[tuple] = []

    def capture(*args: object) -> None:
        events.append(args)

    BUS.subscribe("relic_effect", capture)

    # Trigger safeguard
    ally.hp = 500
    await BUS.emit_async("damage_taken", ally, enemy, 100)
    await asyncio.sleep(0.01)

    # Check that telemetry was emitted
    assert len(events) > 0, "Expected telemetry event"
    relic_id, actor, effect_type, value, metadata = events[0]
    assert relic_id == "safeguard_prism"
    assert effect_type == "emergency_shield"
    assert value == 150  # 15% of 1000
    assert metadata["hp_threshold_percentage"] == 60
    assert metadata["shield_percentage"] == 15
    assert metadata["mitigation_bonus_percentage"] == 12
    assert metadata["trigger_count"] == 1
    assert metadata["max_triggers"] == 1
    assert metadata["stacks"] == 1

