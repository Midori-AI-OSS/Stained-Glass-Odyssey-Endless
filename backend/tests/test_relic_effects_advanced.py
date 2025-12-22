# ruff: noqa: E402
"""Advanced relic effect regression tests."""

import asyncio
from pathlib import Path
import random
import sys
from types import SimpleNamespace

import pytest

_PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if _PROJECT_ROOT not in sys.path:
    sys.path.append(_PROJECT_ROOT)

from autofighter.party import Party
from autofighter.relics import apply_relics, award_relic
from autofighter.rooms.battle.turn_loop import player_turn
from autofighter.stats import BUS, Stats, set_battle_active
from plugins.characters._base import PlayerBase
from plugins.effects.aftertaste import Aftertaste
import plugins.event_bus as event_bus_module
import plugins.relics._base as relic_base_module
import plugins.relics.echoing_drum as echoing_drum_module
from plugins.relics.greed_engine import GreedEngine
import plugins.relics.timekeepers_hourglass as hourglass_module


class DummyPlayer(Stats):
    async def use_ultimate(self) -> bool:
        if not self.ultimate_ready:
            return False
        self.ultimate_charge = 0
        self.ultimate_ready = False
        await BUS.emit_async("ultimate_used", self)
        return True


@pytest.mark.asyncio
async def test_echoing_drum_grants_temporary_attack_buff(monkeypatch):
    event_bus_module.bus._subs.clear()

    party = Party()
    attacker = PlayerBase()
    attacker.id = "echoing-hero"
    target = PlayerBase()
    party.members.append(attacker)

    award_relic(party, "echoing_drum")
    award_relic(party, "echoing_drum")
    await apply_relics(party)

    base_atk = attacker.get_base_stat("atk")
    assert attacker.atk == base_atk

    relic_events: list[tuple[int, dict[str, object]]] = []

    def _capture_relic_effect(
        relic_id: str,
        recipient: Stats,
        event_name: str,
        value: int,
        payload: dict[str, object],
        *_extra: object,
    ) -> None:
        if relic_id == "echoing_drum" and event_name == "aftertaste_attack_buff":
            relic_events.append((value, payload))

    BUS.subscribe("relic_effect", _capture_relic_effect)

    monkeypatch.setattr(echoing_drum_module.random, "random", lambda: 0.0)

    await BUS.emit_async("attack_used", attacker, target, 100)
    await asyncio.sleep(0)

    expected_buff = int(base_atk * 1.5 * 2)
    assert attacker.atk == base_atk + expected_buff

    matching_effects = [
        effect
        for effect in attacker.get_active_effects()
        if effect.name == "echoing_drum_aftertaste_atk_buff"
    ]
    assert len(matching_effects) == 1
    effect = matching_effects[0]
    assert effect.duration == 5
    assert effect.stat_modifiers["atk"] == expected_buff

    assert relic_events
    value, payload = relic_events[-1]
    assert value == expected_buff
    assert payload["stacks"] == 2
    assert payload["buff_amount"] == expected_buff
    assert payload["base_atk"] == base_atk
    assert payload["duration"] == 5
    assert payload["target"] == attacker.id

    for _ in range(4):
        attacker.tick_effects()
        assert attacker.atk == base_atk + expected_buff

    attacker.tick_effects()
    assert attacker.atk == base_atk
    assert not [
        effect
        for effect in attacker.get_active_effects()
        if effect.name == "echoing_drum_aftertaste_atk_buff"
    ]

    BUS.unsubscribe("relic_effect", _capture_relic_effect)


@pytest.mark.asyncio
async def test_frost_sigil_applies_chill(monkeypatch):
    event_bus_module.bus._subs.clear()
    party = Party()
    a = PlayerBase()
    b = PlayerBase()
    b.hp = b.set_base_stat('max_hp', 100)
    a.set_base_stat('atk', 100)
    party.members.append(a)
    award_relic(party, "frost_sigil")
    await apply_relics(party)

    monkeypatch.setattr(Aftertaste, "rolls", lambda self: [self.base_pot] * self.hits)

    async def fake_apply_damage(self, amount, attacker=None):
        self.hp -= amount
        return amount

    monkeypatch.setattr(Stats, "apply_damage", fake_apply_damage, raising=False)

    await BUS.emit_async("hit_landed", a, b, 10)
    await asyncio.sleep(0)

    assert b.hp == 100 - int(100 * 0.05)


@pytest.mark.asyncio
async def test_frost_sigil_stacks(monkeypatch):
    event_bus_module.bus._subs.clear()
    party = Party()
    a = PlayerBase()
    b = PlayerBase()
    b.hp = b.set_base_stat('max_hp', 100)
    a.set_base_stat('atk', 100)
    party.members.append(a)
    award_relic(party, "frost_sigil")
    award_relic(party, "frost_sigil")
    await apply_relics(party)

    monkeypatch.setattr(Aftertaste, "rolls", lambda self: [self.base_pot] * self.hits)

    async def fake_apply_damage(self, amount, attacker=None):
        self.hp -= amount
        return amount

    monkeypatch.setattr(Stats, "apply_damage", fake_apply_damage, raising=False)

    await BUS.emit_async("hit_landed", a, b, 10)
    await asyncio.sleep(0)

    assert b.hp == 100 - int(100 * 0.05) * 2


@pytest.mark.asyncio
async def test_killer_instinct_grants_extra_turn():
    event_bus_module.bus._subs.clear()
    party = Party()
    a = DummyPlayer()
    b = DummyPlayer()
    b.hp = 10
    a.spd = 20
    party.members.append(a)
    award_relic(party, "killer_instinct")
    await apply_relics(party)

    base_atk = a.atk
    base_spd = a.spd

    a.add_ultimate_charge(a.ultimate_charge_max)
    await a.use_ultimate()
    assert a.atk > base_atk

    turns: list[PlayerBase] = []
    BUS.subscribe("extra_turn", lambda m: turns.append(m))

    speed_events: list[tuple[int, dict[str, object]]] = []

    def _capture_relic_effect(
        relic_id,
        recipient,
        event_name,
        value,
        payload,
        *_extra,
    ):
        if relic_id != "killer_instinct":
            return
        if event_name == "kill_speed_boost":
            speed_events.append((value, payload))

    BUS.subscribe("relic_effect", _capture_relic_effect)

    b.hp = 0
    await BUS.emit_async("damage_taken", b, a, 10)

    expected_spd = int(base_spd * 1.5)
    assert turns == []
    assert a.spd == expected_spd
    assert speed_events
    boost_value, payload = speed_events[-1]
    assert boost_value == 50
    assert payload["spd_percentage"] == 50
    assert payload["duration"] == "2_turns"
    assert payload["speed_multiplier"] == pytest.approx(1.5)

    await BUS.emit_async("turn_end")
    assert a.atk == base_atk
    assert a.spd == expected_spd

    await a.effect_manager.tick()
    assert a.spd == expected_spd

    await a.effect_manager.tick()
    assert a.spd == base_spd


@pytest.mark.asyncio
async def test_travelers_charm_buff():
    event_bus_module.bus._subs.clear()
    party = Party()
    a = PlayerBase()
    attacker = PlayerBase()
    a.set_base_stat('defense', 100)
    a.set_base_stat('mitigation', 100)
    party.members.append(a)
    award_relic(party, "travelers_charm")
    await apply_relics(party)
    await BUS.emit_async("damage_taken", a, attacker, 10)
    await BUS.emit_async("turn_start")
    assert a.defense == 100 + int(100 * 0.25)
    assert a.mitigation == 110
    await BUS.emit_async("turn_end")
    assert a.defense == 100
    assert a.mitigation == 100


@pytest.mark.asyncio
async def test_timekeepers_hourglass_speed_buff():
    event_bus_module.bus._subs.clear()
    party = Party()
    a = PlayerBase()
    party.members.append(a)
    award_relic(party, "timekeepers_hourglass")
    await apply_relics(party)

    turns: list[PlayerBase] = []
    BUS.subscribe("extra_turn", lambda m: turns.append(m))

    orig = random.random
    random.random = lambda: 0.0
    try:
        await BUS.emit_async("turn_start")
    finally:
        random.random = orig

    assert turns == []

    mgr = getattr(a, "effect_manager", None)
    assert mgr is not None

    mods = [mod for mod in mgr.mods if mod.name == "timekeepers_hourglass_spd"]
    assert len(mods) == 1
    mod = mods[0]
    assert mod.turns == 2
    assert mod.multipliers is not None
    assert mod.multipliers.get("spd") == pytest.approx(1.20)

    effects = [eff for eff in a.get_active_effects() if eff.name == "timekeepers_hourglass_spd"]
    assert len(effects) == 1


@pytest.mark.asyncio
async def test_timekeepers_hourglass_many_stacks_no_stall(monkeypatch: pytest.MonkeyPatch) -> None:
    from autofighter.rooms.battle import pacing as battle_pacing
    from autofighter.rooms.battle.turns import EnrageState

    event_bus_module.bus._subs.clear()
    battle_pacing._EXTRA_TURNS.clear()

    party = Party()
    ko_member = PlayerBase()
    ko_member.id = "hourglass-ko"
    ko_member.hp = ko_member.set_base_stat("max_hp", 100)
    alive_member = PlayerBase()
    alive_member.id = "hourglass-alive"
    alive_member.hp = alive_member.set_base_stat("max_hp", 100)
    party.members.extend([ko_member, alive_member])

    for _ in range(120):
        award_relic(party, "timekeepers_hourglass")
    await apply_relics(party)

    ko_member.hp = 0
    alive_member.hp = alive_member.max_hp

    monkeypatch.setattr(hourglass_module.random, "random", lambda: 0.0)

    combat_party = Party(members=list(party.members))

    class DummyRegistry:
        async def trigger(self, *_: object, **__: object) -> None:
            return None

        async def trigger_turn_start(self, *_: object, **__: object) -> None:
            return None

        async def trigger_turn_end(self, *_: object, **__: object) -> None:
            return None

        async def trigger_hit_landed(self, *_: object, **__: object) -> None:
            return None

    async def _noop_async(*_: object, **__: object) -> None:
        return None

    monkeypatch.setattr(player_turn, "push_progress_update", _noop_async)
    monkeypatch.setattr(player_turn, "pace_sleep", _noop_async)
    monkeypatch.setattr(player_turn, "impact_pause", _noop_async)
    monkeypatch.setattr(player_turn, "_pace", _noop_async)
    monkeypatch.setattr(player_turn, "queue_log", lambda *_, **__: None)
    monkeypatch.setattr(player_turn, "_handle_ultimate", _noop_async)
    monkeypatch.setattr(player_turn, "apply_enrage_bleed", _noop_async)
    monkeypatch.setattr(player_turn, "credit_if_dead", lambda **kwargs: (kwargs["exp_reward"], kwargs["temp_rdr"]))
    monkeypatch.setattr(player_turn, "remove_dead_foes", lambda **__: None)
    monkeypatch.setattr(
        player_turn,
        "SummonManager",
        SimpleNamespace(add_summons_to_party=lambda *_: 0, get_summons=lambda *_: []),
    )
    monkeypatch.setattr(player_turn, "register_snapshot_entities", lambda *_, **__: None)
    monkeypatch.setattr(player_turn, "mutate_snapshot_overlay", lambda *_, **__: None)
    monkeypatch.setattr(player_turn, "calc_animation_time", lambda *_, **__: 0)
    monkeypatch.setattr(player_turn, "_abort_other_runs", _noop_async)

    context = player_turn.TurnLoopContext(
        room=SimpleNamespace(),
        party=party,
        combat_party=combat_party,
        registry=DummyRegistry(),
        foes=[],
        foe_effects=[],
        enrage_mods=[],
        enrage_state=EnrageState(threshold=999),
        progress=None,
        visual_queue=None,
        temp_rdr=0.0,
        exp_reward=0,
        run_id="hourglass-test",
        battle_tasks={},
        abort=lambda *_: None,
        credited_foe_ids=set(),
        turn=0,
    )

    await asyncio.wait_for(player_turn.execute_player_phase(context), timeout=1.0)

    assert battle_pacing._EXTRA_TURNS.get(id(ko_member), 0) == 0

    battle_pacing._EXTRA_TURNS.clear()
    await BUS.emit_async("battle_end", None)


@pytest.mark.asyncio
async def test_greed_engine_drains_and_rewards():
    event_bus_module.bus._subs.clear()
    party = Party()
    a = PlayerBase()
    a.hp = a.set_base_stat('max_hp', 200)
    party.members.append(a)
    award_relic(party, "greed_engine")
    await apply_relics(party)
    await BUS.emit_async("turn_start")
    assert a.hp == 200 - int(200 * 0.01)
    await BUS.emit_async("gold_earned", 100)
    assert party.gold == int(100 * 0.5)


@pytest.mark.asyncio
async def test_greed_engine_stacks():
    event_bus_module.bus._subs.clear()
    party = Party()
    a = PlayerBase()
    a.hp = a.set_base_stat('max_hp', 200)
    party.members.append(a)
    award_relic(party, "greed_engine")
    award_relic(party, "greed_engine")
    await apply_relics(party)
    await BUS.emit_async("turn_start")
    assert a.hp == 200 - int(200 * (0.01 + 0.005))
    await BUS.emit_async("gold_earned", 100)
    assert party.gold == int(100 * (0.5 + 0.25))


def test_greed_engine_text_updates():
    relic = GreedEngine()

    assert (
        relic.full_about
        == "Party loses 1% HP on every combat action but gains 50% more gold "
        "and increases rare drop rate by 0.5%. Stacks multiply benefits and costs."
    )

    assert (
        relic.describe(1)
        == "Party loses 1.0% HP on every combat action, gains 50% more gold, and "
        "increases rare drop rate by 0.5%."
    )


@pytest.mark.asyncio
async def test_stellar_compass_crit_bonus():
    event_bus_module.bus._subs.clear()
    party = Party()
    a = PlayerBase()
    a.set_base_stat('atk', 100)
    party.members.append(a)
    award_relic(party, "stellar_compass")
    await apply_relics(party)
    await BUS.emit_async("critical_hit", a, None, 0, "attack")
    assert a.atk == int(100 * (1 + 0.015))
    await BUS.emit_async("gold_earned", 100)
    assert party.gold == int(100 * 0.015)


@pytest.mark.asyncio
async def test_stellar_compass_stacks():
    event_bus_module.bus._subs.clear()
    party = Party()
    a = PlayerBase()
    a.set_base_stat('atk', 100)
    party.members.append(a)
    award_relic(party, "stellar_compass")
    award_relic(party, "stellar_compass")
    await apply_relics(party)
    await BUS.emit_async("critical_hit", a, None, 0, "attack")
    assert a.atk == int(100 * (1 + 0.015 * 2))
    await BUS.emit_async("gold_earned", 100)
    assert party.gold == int(100 * 0.03)


@pytest.mark.asyncio
async def test_stellar_compass_multiple_crits():
    event_bus_module.bus._subs.clear()
    party = Party()
    a = PlayerBase()
    a.set_base_stat('atk', 100)
    party.members.append(a)
    award_relic(party, "stellar_compass")
    await apply_relics(party)

    await BUS.emit_async("critical_hit", a, None, 0, "attack")
    await BUS.emit_async("gold_earned", 100)
    assert a.atk == int(100 * (1 + 0.015))
    assert party.gold == int(100 * 0.015)

    await BUS.emit_async("critical_hit", a, None, 0, "attack")
    await BUS.emit_async("gold_earned", 100)
    assert a.atk == int(100 * (1 + 0.015 * 2))
    assert party.gold == int(100 * 0.015) + int(100 * 0.03)


@pytest.mark.asyncio
async def test_echoing_drum_aftertaste_trigger(monkeypatch):
    event_bus_module.bus._subs.clear()
    party = Party()
    attacker = PlayerBase()
    target = PlayerBase()
    target.hp = 100
    party.members.append(attacker)
    award_relic(party, "echoing_drum")
    await apply_relics(party)

    triggered_hits: list[int] = []
    created_tasks: list[asyncio.Task] = []

    async def fake_apply(self, *_args, **_kwargs):
        triggered_hits.append(self.hits)
        return [0] * self.hits

    monkeypatch.setattr(Aftertaste, "apply", fake_apply, raising=False)
    monkeypatch.setattr(echoing_drum_module.random, "random", lambda: 0.0)
    monkeypatch.setattr(
        relic_base_module,
        "safe_async_task",
        lambda coro: created_tasks.append(asyncio.create_task(coro)) or created_tasks[-1],
    )

    await BUS.emit_async("battle_start")
    await BUS.emit_async("attack_used", attacker, target, 20)
    if created_tasks:
        await asyncio.gather(*created_tasks)
        created_tasks.clear()
    assert triggered_hits == [1]

    await BUS.emit_async("attack_used", attacker, target, 20)
    if created_tasks:
        await asyncio.gather(*created_tasks)
        created_tasks.clear()
    assert triggered_hits == [1]


@pytest.mark.asyncio
async def test_echoing_drum_roll_failure(monkeypatch):
    event_bus_module.bus._subs.clear()
    party = Party()
    attacker = PlayerBase()
    target = PlayerBase()
    target.hp = 100
    party.members.append(attacker)
    award_relic(party, "echoing_drum")
    award_relic(party, "echoing_drum")
    await apply_relics(party)

    triggered_hits: list[int] = []
    created_tasks: list[asyncio.Task] = []

    async def fake_apply(self, *_args, **_kwargs):
        triggered_hits.append(self.hits)
        return [0] * self.hits

    monkeypatch.setattr(Aftertaste, "apply", fake_apply, raising=False)
    monkeypatch.setattr(echoing_drum_module.random, "random", lambda: 0.75)
    monkeypatch.setattr(
        relic_base_module,
        "safe_async_task",
        lambda coro: created_tasks.append(asyncio.create_task(coro)) or created_tasks[-1],
    )

    await BUS.emit_async("battle_start")
    await BUS.emit_async("attack_used", attacker, target, 20)
    if created_tasks:
        await asyncio.gather(*created_tasks)
        created_tasks.clear()
    assert triggered_hits == []


@pytest.mark.asyncio
async def test_echoing_drum_overflow_aftertaste_hits(monkeypatch):
    event_bus_module.bus._subs.clear()
    party = Party()
    attacker = PlayerBase()
    target = PlayerBase()
    target.hp = 100
    party.members.append(attacker)
    for _ in range(5):
        award_relic(party, "echoing_drum")
    await apply_relics(party)

    triggered_hits: list[int] = []
    created_tasks: list[asyncio.Task] = []

    async def fake_apply(self, *_args, **_kwargs):
        triggered_hits.append(self.hits)
        return [0] * self.hits

    monkeypatch.setattr(Aftertaste, "apply", fake_apply, raising=False)
    monkeypatch.setattr(echoing_drum_module.random, "random", lambda: 0.2)
    monkeypatch.setattr(
        relic_base_module,
        "safe_async_task",
        lambda coro: created_tasks.append(asyncio.create_task(coro)) or created_tasks[-1],
    )

    await BUS.emit_async("battle_start")
    await BUS.emit_async("attack_used", attacker, target, 20)
    if created_tasks:
        await asyncio.gather(*created_tasks)
        created_tasks.clear()
    assert triggered_hits == [2]


@pytest.mark.asyncio
async def test_blood_debt_tithe_basic_defeat_tracking():
    """Test that Blood Debt Tithe tracks defeats and increases RDR."""
    event_bus_module.bus._subs.clear()

    from plugins.characters.foe_base import FoeBase

    party = Party()
    party.members.append(PlayerBase())

    # Start with known RDR
    initial_rdr = party.rdr

    # Award one stack
    award_relic(party, "blood_debt_tithe")
    await apply_relics(party)

    # Create a foe
    foe = FoeBase()
    foe.id = "test_foe_1"
    foe.hp = 0  # Defeated

    # Track relic effects
    relic_events = []

    def _capture_relic_effect(
        relic_id: str,
        recipient,
        event_name: str,
        value: int,
        payload: dict[str, object],
        *_extra: object,
    ) -> None:
        if relic_id == "blood_debt_tithe":
            relic_events.append((event_name, value, payload))

    BUS.subscribe("relic_effect", _capture_relic_effect)

    # Emit defeat and battle end
    await BUS.emit_async("entity_defeat", foe)
    await BUS.emit_async("battle_end", foe)

    # RDR should increase by 0.2% (0.002) per stack per defeat = 0.002 * 1 * 1
    expected_rdr = initial_rdr + 0.002
    assert party.rdr == pytest.approx(expected_rdr, rel=1e-5)

    # Check telemetry
    defeats_events = [e for e in relic_events if e[0] == "defeats_banked"]
    assert len(defeats_events) == 1
    _, value, payload = defeats_events[0]
    assert value == 1
    assert payload["new_defeats"] == 1
    assert payload["total_defeats"] == 1
    assert payload["stacks"] == 1


@pytest.mark.asyncio
async def test_blood_debt_tithe_duplicate_defeat_suppression():
    """Test that duplicate defeats in same battle don't inflate count."""
    event_bus_module.bus._subs.clear()

    from plugins.characters.foe_base import FoeBase

    party = Party()
    party.members.append(PlayerBase())
    initial_rdr = party.rdr

    award_relic(party, "blood_debt_tithe")
    await apply_relics(party)

    foe = FoeBase()
    foe.id = "test_foe_1"
    foe.hp = 0

    # Emit defeat multiple times (simulating multiple calls)
    await BUS.emit_async("entity_defeat", foe)
    await BUS.emit_async("entity_defeat", foe)
    await BUS.emit_async("entity_defeat", foe)
    await BUS.emit_async("battle_end", foe)

    # RDR should only increase once for the unique foe
    expected_rdr = initial_rdr + 0.002
    assert party.rdr == pytest.approx(expected_rdr, rel=1e-5)


@pytest.mark.asyncio
async def test_blood_debt_tithe_multiple_foes():
    """Test tracking multiple different foes in one battle."""
    event_bus_module.bus._subs.clear()

    from plugins.characters.foe_base import FoeBase

    party = Party()
    party.members.append(PlayerBase())
    initial_rdr = party.rdr

    award_relic(party, "blood_debt_tithe")
    await apply_relics(party)

    # Create three unique foes
    foe1 = FoeBase()
    foe1.id = "foe_1"
    foe1.hp = 0

    foe2 = FoeBase()
    foe2.id = "foe_2"
    foe2.hp = 0

    foe3 = FoeBase()
    foe3.id = "foe_3"
    foe3.hp = 0

    # Emit defeats for all three
    await BUS.emit_async("entity_defeat", foe1)
    await BUS.emit_async("entity_defeat", foe2)
    await BUS.emit_async("entity_defeat", foe3)
    await BUS.emit_async("battle_end", foe1)

    # RDR should increase by 0.002 * 3 = 0.006
    expected_rdr = initial_rdr + 0.006
    assert party.rdr == pytest.approx(expected_rdr, rel=1e-5)


@pytest.mark.asyncio
async def test_blood_debt_tithe_stacking():
    """Test that multiple stacks multiply the RDR bonus."""
    event_bus_module.bus._subs.clear()

    from plugins.characters.foe_base import FoeBase

    party = Party()
    party.members.append(PlayerBase())
    initial_rdr = party.rdr

    # Award two stacks
    award_relic(party, "blood_debt_tithe")
    award_relic(party, "blood_debt_tithe")
    await apply_relics(party)

    foe = FoeBase()
    foe.id = "test_foe"
    foe.hp = 0

    await BUS.emit_async("entity_defeat", foe)
    await BUS.emit_async("battle_end", foe)

    # RDR should increase by 0.002 * 2 stacks * 1 defeat = 0.004
    expected_rdr = initial_rdr + 0.004
    assert party.rdr == pytest.approx(expected_rdr, rel=1e-5)


@pytest.mark.asyncio
async def test_blood_debt_tithe_foe_buffing():
    """Test that foes are buffed based on stored defeats."""
    event_bus_module.bus._subs.clear()

    from plugins.characters.foe_base import FoeBase

    party = Party()
    party.members.append(PlayerBase())

    award_relic(party, "blood_debt_tithe")
    await apply_relics(party)

    # Simulate previous battles - manually set defeats
    state = party._blood_debt_tithe_state
    state["total_defeats"] = 5

    # Create a new foe for next battle
    foe = FoeBase()
    foe.id = "buffed_foe"
    base_atk = 100
    base_spd = 100
    foe.set_base_stat("atk", base_atk)
    foe.set_base_stat("spd", base_spd)

    relic_events = []

    def _capture_relic_effect(
        relic_id: str,
        recipient,
        event_name: str,
        value: int,
        payload: dict[str, object],
        *_extra: object,
    ) -> None:
        if relic_id == "blood_debt_tithe" and event_name == "foe_buffed":
            relic_events.append(payload)

    BUS.subscribe("relic_effect", _capture_relic_effect)

    initial_atk = foe.atk
    initial_spd = foe.spd

    await BUS.emit_async("battle_start", foe)

    # Foe stats should be buffed (exact values depend on diminishing returns)
    # Just check they increased
    assert foe.atk > initial_atk
    assert foe.spd > initial_spd

    # Check telemetry
    assert len(relic_events) == 1
    payload = relic_events[0]
    assert payload["total_defeats"] == 5
    assert payload["atk_multiplier"] == pytest.approx(1.15, rel=1e-5)
    assert payload["spd_multiplier"] == pytest.approx(1.10, rel=1e-5)


@pytest.mark.asyncio
async def test_blood_debt_tithe_cross_battle_persistence():
    """Test that defeat counter persists across battles."""
    event_bus_module.bus._subs.clear()

    from plugins.characters.foe_base import FoeBase

    party = Party()
    party.members.append(PlayerBase())
    initial_rdr = party.rdr

    award_relic(party, "blood_debt_tithe")
    await apply_relics(party)

    # First battle - 2 defeats
    foe1 = FoeBase()
    foe1.id = "battle1_foe1"
    foe1.hp = 0

    foe2 = FoeBase()
    foe2.id = "battle1_foe2"
    foe2.hp = 0

    await BUS.emit_async("entity_defeat", foe1)
    await BUS.emit_async("entity_defeat", foe2)
    await BUS.emit_async("battle_end", foe1)
    await BUS.emit_async("battle_end", foe2)

    rdr_after_battle1 = party.rdr
    assert rdr_after_battle1 == pytest.approx(initial_rdr + 0.004, rel=1e-5)

    # Re-apply relics for battle 2 (simulating new battle setup)
    await apply_relics(party)

    # Second battle - 1 defeat
    foe3 = FoeBase()
    foe3.id = "battle2_foe1"
    foe3.hp = 0

    await BUS.emit_async("entity_defeat", foe3)
    await BUS.emit_async("battle_end", foe3)

    # Total should be 3 defeats = 0.002 * 3 = 0.006
    expected_rdr = initial_rdr + 0.006
    assert party.rdr == pytest.approx(expected_rdr, rel=1e-5)

    # Check stored state
    assert party._blood_debt_tithe_state["total_defeats"] == 3


@pytest.mark.asyncio
async def test_blood_debt_tithe_foe_buff_scaling():
    """Test that foe buffs scale with both defeats and stacks."""
    event_bus_module.bus._subs.clear()

    from plugins.characters.foe_base import FoeBase

    party = Party()
    party.members.append(PlayerBase())

    # Award 2 stacks
    award_relic(party, "blood_debt_tithe")
    award_relic(party, "blood_debt_tithe")
    await apply_relics(party)

    # Set 3 stored defeats
    state = party._blood_debt_tithe_state
    state["total_defeats"] = 3

    foe = FoeBase()
    foe.id = "scaled_foe"
    foe.set_base_stat("atk", 100)
    foe.set_base_stat("spd", 100)

    initial_atk = foe.atk
    initial_spd = foe.spd

    await BUS.emit_async("battle_start", foe)

    # Foe stats should be significantly buffed (more than single stack case)
    # Expected multipliers: 1.18 for ATK, 1.12 for SPD
    # With diminishing returns, actual increase will be less but still substantial
    assert foe.atk > initial_atk
    assert foe.spd > initial_spd

    # The buff should be more than what a single stack would provide
    # Single stack with 3 defeats would be ~1.09 ATK, 1.06 SPD
    # So we should see noticeably more than 9% and 6% increases
    assert foe.atk >= initial_atk * 1.12  # At least 12% increase even with diminishing
    assert foe.spd >= initial_spd * 1.08  # At least 8% increase even with diminishing


@pytest.mark.asyncio
async def test_eclipse_reactor_initial_drain_clamps_to_one_hp():
    event_bus_module.bus._subs.clear()

    party = Party()
    ally = PlayerBase()
    ally.id = "eclipse-survivor"
    ally.set_base_stat("max_hp", 50)
    ally.hp = ally.max_hp
    ally.hp = 4
    party.members.append(ally)

    award_relic(party, "eclipse_reactor")
    await apply_relics(party)

    set_battle_active(True)
    try:
        await BUS.emit_async("battle_start", ally)
        await asyncio.sleep(0)

        assert ally.hp == 1
    finally:
        set_battle_active(False)


@pytest.mark.asyncio
async def test_eclipse_reactor_surge_duration_and_post_drain():
    event_bus_module.bus._subs.clear()

    party = Party()
    ally = PlayerBase()
    ally.id = "eclipse-burst"
    ally.set_base_stat("max_hp", 100)
    ally.hp = ally.max_hp
    ally.set_base_stat("atk", 100)
    ally.set_base_stat("spd", 50)
    ally.set_base_stat("crit_damage", 2.0)
    party.members.append(ally)

    award_relic(party, "eclipse_reactor")
    award_relic(party, "eclipse_reactor")
    await apply_relics(party)

    base_atk = ally.get_base_stat("atk")
    base_spd = ally.get_base_stat("spd")
    base_cd = ally.get_base_stat("crit_damage")

    set_battle_active(True)
    try:
        await BUS.emit_async("battle_start", ally)
        await asyncio.sleep(0)

        stacks = party.relics.count("eclipse_reactor")
        surge_atk_mult = 1 + 1.8 * stacks
        surge_spd_mult = 1 + 1.8 * stacks
        surge_cd_mult = 1 + 0.6 * stacks
        initial_drain = min(int(ally.max_hp * 0.18 * stacks), ally.max_hp - 1)

        assert ally.atk == int(base_atk * surge_atk_mult)
        assert ally.spd == int(base_spd * surge_spd_mult)
        assert ally.crit_damage == pytest.approx(base_cd * surge_cd_mult)
        assert ally.hp == ally.max_hp - initial_drain

        for _ in range(2):
            await BUS.emit_async("turn_start")
            await asyncio.sleep(0)
            assert ally.atk == int(base_atk * surge_atk_mult)
            assert ally.spd == int(base_spd * surge_spd_mult)
            assert ally.crit_damage == pytest.approx(base_cd * surge_cd_mult)

        await BUS.emit_async("turn_start")
        await asyncio.sleep(0)

        assert ally.atk == base_atk
        assert ally.spd == base_spd
        assert ally.crit_damage == pytest.approx(base_cd)
        assert ally.hp == ally.max_hp - initial_drain

        await BUS.emit_async("turn_start")
        await asyncio.sleep(0)

        post_drain = int(ally.max_hp * 0.02 * stacks)
        assert ally.hp == ally.max_hp - initial_drain - post_drain
    finally:
        set_battle_active(False)


@pytest.mark.asyncio
async def test_eclipse_reactor_cleans_up_on_battle_end():
    event_bus_module.bus._subs.clear()

    party = Party()
    ally = PlayerBase()
    ally.id = "eclipse-cleanup"
    ally.set_base_stat("max_hp", 100)
    ally.hp = ally.max_hp
    party.members.append(ally)

    award_relic(party, "eclipse_reactor")
    await apply_relics(party)

    set_battle_active(True)
    try:
        await BUS.emit_async("battle_start", ally)
        await asyncio.sleep(0)

        for _ in range(3):
            await BUS.emit_async("turn_start")
            await asyncio.sleep(0)

        await BUS.emit_async("turn_start")
        await asyncio.sleep(0)
        hp_after_drain = ally.hp

        from plugins.characters.foe_base import FoeBase

        await BUS.emit_async("battle_end", FoeBase())
        await asyncio.sleep(0)

        ally.hp = hp_after_drain
        await BUS.emit_async("turn_start")
        await asyncio.sleep(0)

        assert ally.hp == hp_after_drain
        assert ally.atk == ally.get_base_stat("atk")
    finally:
        set_battle_active(False)
