import sys
import types
import asyncio

import pytest
from runs import lifecycle as lifecycle_module

from autofighter.mapgen import MapNode
from autofighter.party import Party
from autofighter.rooms import BattleRoom
from autofighter.rooms.battle import events as battle_events
from autofighter.rooms.battle import snapshots as battle_snapshots_module
import autofighter.stats as stats
from plugins.characters._base import PlayerBase
from plugins.characters.foe_base import FoeBase
from plugins.characters.player import Player
from plugins.effects.aftertaste import Aftertaste
import plugins.event_bus as event_bus_module
import plugins.relics.rusty_buckle as rb
from plugins.relics.rusty_buckle import RustyBuckle


@pytest.fixture
def bus(monkeypatch):
    event_bus_module.bus._subs.clear()
    event_bus_module.bus._batched_events.clear()
    event_bus_module.bus._batch_timer = None

    bus = event_bus_module.EventBus()
    monkeypatch.setattr(stats, "BUS", bus)
    monkeypatch.setattr(rb, "BUS", bus)
    monkeypatch.setattr(battle_events, "BUS", bus)

    llms = types.ModuleType("llms")
    torch_checker = types.ModuleType("llms.torch_checker")
    torch_checker.is_torch_available = lambda: False
    llms.torch_checker = torch_checker
    monkeypatch.setitem(sys.modules, "llms", llms)
    monkeypatch.setitem(sys.modules, "llms.torch_checker", torch_checker)

    async def simple_damage(self, amount, attacker=None, **kwargs):
        self.hp = max(self.hp - int(amount), 0)
        await bus.emit_async("damage_taken", self, attacker, amount)
        return int(amount)

    async def simple_heal(self, amount, healer=None):
        self.hp = min(self.hp + int(amount), self.max_hp)
        await bus.emit_async("heal_received", self, healer, amount, None, None)
        return int(amount)

    monkeypatch.setattr(PlayerBase, "apply_damage", simple_damage)
    monkeypatch.setattr(PlayerBase, "apply_healing", simple_heal)

    stats.set_battle_active(True)
    yield bus
    stats.set_battle_active(False)
    event_bus_module.bus._subs.clear()
    event_bus_module.bus._batched_events.clear()
    event_bus_module.bus._batch_timer = None


async def _drain_pending_tasks() -> None:
    await asyncio.sleep(0)
    await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_all_allies_bleed_each_turn(bus):
    first = PlayerBase()
    second = PlayerBase()
    second._base_max_hp = 800
    second.hp = 800
    party = Party(members=[first, second], relics=["rusty_buckle"])
    relic = RustyBuckle()
    await relic.apply(party)

    foe = FoeBase()
    await bus.emit_async("turn_start", foe)
    await _drain_pending_tasks()

    assert party.members[0].hp == 950
    assert party.members[1].hp == 760

    for member in party.members:
        await bus.emit_async("turn_start", member)
    await _drain_pending_tasks()

    assert party.members[0].hp == 850
    assert party.members[1].hp == 680

    for member in party.members:
        await bus.emit_async("turn_start", member)
    await _drain_pending_tasks()

    assert party.members[0].hp == 750
    assert party.members[1].hp == 600


@pytest.mark.asyncio
async def test_aftertaste_triggers_on_cumulative_loss(monkeypatch, bus):
    party = Party(members=[PlayerBase(), PlayerBase()], relics=["rusty_buckle"])
    for member in party.members:
        member._base_max_hp = 100
        member.hp = member.max_hp
    relic = RustyBuckle()
    await relic.apply(party)

    foe = FoeBase()
    await bus.emit_async("turn_start", foe)
    for member in party.members:
        await bus.emit_async("turn_start", member)
    await _drain_pending_tasks()

    hits = 0

    async def fake_apply(self, attacker, target):
        nonlocal hits
        hits += 1
        return []

    monkeypatch.setattr(Aftertaste, "apply", fake_apply)

    async def drain_party_once() -> None:
        for member in party.members:
            await member.apply_damage(member.max_hp)
        await _drain_pending_tasks()

    async def restore_party() -> None:
        for member in party.members:
            await member.apply_healing(member.max_hp)
        await _drain_pending_tasks()

    for _ in range(49):
        await drain_party_once()
        await restore_party()
        assert hits == 0

    await drain_party_once()
    assert hits == 5


@pytest.mark.asyncio
async def test_stacks_increase_threshold(monkeypatch, bus):
    first = PlayerBase()
    second = PlayerBase()
    first._base_max_hp = 100
    first.hp = first.max_hp
    second._base_max_hp = 100
    second.hp = second.max_hp
    party = Party(members=[first, second], relics=["rusty_buckle", "rusty_buckle"])
    relic = RustyBuckle()
    await relic.apply(party)

    foe = FoeBase()
    await bus.emit_async("turn_start", foe)
    for member in party.members:
        await bus.emit_async("turn_start", member)
    await _drain_pending_tasks()

    hits = 0

    async def fake_apply(self, attacker, target):
        nonlocal hits
        hits += 1
        return []

    monkeypatch.setattr(Aftertaste, "apply", fake_apply)

    async def drain_party_once() -> None:
        for member in party.members:
            await member.apply_damage(member.max_hp)
        await _drain_pending_tasks()

    async def restore_party() -> None:
        for member in party.members:
            await member.apply_healing(member.max_hp)
        await _drain_pending_tasks()

    for _ in range(59):
        await drain_party_once()
        await restore_party()
        assert hits == 0

    await drain_party_once()
    assert hits == 8


@pytest.mark.asyncio
async def test_reapply_refreshes_prev_hp_snapshot(bus):
    party = Party(members=[PlayerBase(), PlayerBase()], relics=["rusty_buckle"])
    relic = RustyBuckle()
    await relic.apply(party)

    foe = FoeBase()
    await bus.emit_async("turn_start", foe)
    for member in party.members:
        await bus.emit_async("turn_start", member)
    await _drain_pending_tasks()

    party.members[0].hp = 600
    party.members[1].hp = 400

    party.relics.append("rusty_buckle")
    await relic.apply(party)

    state = party._rusty_buckle_state
    assert state["prev_hp"][id(party.members[0])] == 600
    assert state["prev_hp"][id(party.members[1])] == 400

    pre_hp_lost = state["hp_lost"]
    await party.members[0].apply_damage(100)
    await _drain_pending_tasks()
    assert state["hp_lost"] == pre_hp_lost + 100


@pytest.mark.asyncio
async def test_apply_no_type_error(bus):
    party = Party(members=[PlayerBase(), PlayerBase()], relics=["rusty_buckle"])
    relic = RustyBuckle()
    await relic.apply(party)


@pytest.mark.asyncio
async def test_effect_charge_snapshot_updates_and_clears(bus):
    lifecycle_module.battle_snapshots.clear()
    run_id = "rusty-effects"

    first = PlayerBase()
    second = PlayerBase()
    first._base_max_hp = 1_000
    second._base_max_hp = 1_000
    first.hp = first.max_hp
    second.hp = second.max_hp

    party = Party(members=[first, second], relics=["rusty_buckle"])
    battle_snapshots_module.prepare_snapshot_overlay(run_id, [party, first, second])

    relic = RustyBuckle()
    await relic.apply(party)

    snapshot = lifecycle_module.battle_snapshots[run_id]
    charges = snapshot.get("effects_charge")
    assert charges is not None and len(charges) == 1
    assert charges[0]["progress"] == pytest.approx(0.0)

    await party.members[0].apply_damage(500)
    await _drain_pending_tasks()

    charges = lifecycle_module.battle_snapshots[run_id].get("effects_charge")
    assert charges is not None and len(charges) == 1
    entry = charges[0]
    assert entry["id"] == "rusty_buckle"
    assert entry["hits"] == 5
    assert entry["estimated_damage_per_hit"] == 2
    assert entry["estimated_total_damage"] == 10
    expected_threshold = int((first.max_hp + second.max_hp) * RustyBuckle._threshold_multiplier(1))
    assert entry["threshold_per_charge"] == expected_threshold
    assert entry["progress"] == pytest.approx(0.005, rel=1e-6)

    await battle_events.handle_battle_end([], party.members)

    assert "effects_charge" not in lifecycle_module.battle_snapshots[run_id]
    lifecycle_module.battle_snapshots.clear()


@pytest.mark.asyncio
async def test_battle_result_omits_stale_rusty_buckle_progress(monkeypatch, bus):
    lifecycle_module.battle_snapshots.clear()
    run_id = "rusty-battle-run"

    node = MapNode(room_id=0, room_type="battle", floor=1, index=0, loop=1, pressure=0)
    room = BattleRoom(node)

    player = Player()
    party = Party(members=[player], relics=["rusty_buckle"])

    class DummyFoe(FoeBase):
        id = "dummy"
        name = "Dummy"

    foe = DummyFoe()
    foe.hp = 1
    foe.max_hp = 1
    foe.actions_per_turn = 0

    monkeypatch.setattr("autofighter.rooms.utils._scale_stats", lambda *args, **kwargs: None)

    captured_charges: list[list[dict[str, object]]] = []

    async def fake_run_turn_loop(
        *,
        room,
        party,
        combat_party,
        registry,
        foes,
        foe_effects,
        enrage_mods,
        enrage_state,
        progress,
        visual_queue,
        temp_rdr,
        exp_reward,
        run_id,
        battle_tasks,
        abort,
    ) -> tuple[int, float, int]:
        battle_snapshots_module.prepare_snapshot_overlay(
            run_id,
            [combat_party, *combat_party.members, *foes],
        )
        battle_snapshots_module.register_snapshot_entities(
            run_id,
            [combat_party, *combat_party.members, *foes],
        )
        battle_snapshots_module.set_effect_charges(
            run_id,
            [
                {
                    "id": "rusty_buckle",
                    "name": "Rusty Buckle",
                    "stacks": 1,
                    "progress": 0.5,
                }
            ],
        )
        snapshot = battle_snapshots_module.get_effect_charges(run_id)
        if snapshot:
            captured_charges.append(snapshot)
        for foe_obj in foes:
            foe_obj.hp = 0
        return 1, temp_rdr, exp_reward

    monkeypatch.setattr(
        "autofighter.rooms.battle.engine.run_turn_loop",
        fake_run_turn_loop,
    )

    card_counter = {"count": 0}

    def fake_card_choices(*_args, **_kwargs):
        card_counter["count"] += 1
        return [
            types.SimpleNamespace(
                id=f"card_{card_counter['count']}",
                name=f"Card {card_counter['count']}",
                stars=1,
                about="Test card",
            )
        ]

    monkeypatch.setattr(
        "autofighter.rooms.battle.resolution.card_choices",
        fake_card_choices,
    )
    monkeypatch.setattr(
        "autofighter.rooms.battle.resolution._pick_card_stars",
        lambda _room: 1,
    )
    monkeypatch.setattr(
        "autofighter.rooms.battle.resolution._apply_rdr_to_stars",
        lambda stars, _rdr: stars,
    )
    monkeypatch.setattr(
        "autofighter.rooms.battle.resolution._calc_gold",
        lambda _room, _temp_rdr: 0,
    )
    monkeypatch.setattr(
        "autofighter.rooms.battle.resolution._pick_item_stars",
        lambda _room: 0,
    )
    monkeypatch.setattr(
        "autofighter.rooms.battle.resolution._roll_relic_drop",
        lambda _room, _rdr: False,
    )
    monkeypatch.setattr(
        "autofighter.rooms.battle.resolution.random.random",
        lambda: 0.0,
    )

    result = await room.resolve(party, {}, foe=foe, run_id=run_id)

    assert captured_charges, "expected rusty buckle progress to be cached before cleanup"
    assert battle_snapshots_module.get_effect_charges(run_id) is None
    assert "effects_charge" not in result

    lifecycle_module.battle_snapshots.pop(run_id, None)
