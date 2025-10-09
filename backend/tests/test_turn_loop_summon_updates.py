"""Tests ensuring summon additions trigger immediate progress updates."""

from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Any

import pytest

_PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if _PROJECT_ROOT not in sys.path:
    sys.path.append(_PROJECT_ROOT)

from autofighter.rooms.battle.turn_loop import foe_turn  # noqa: E402
from autofighter.rooms.battle.turn_loop import player_turn  # noqa: E402
from autofighter.rooms.battle import events as battle_events  # noqa: E402
from autofighter.rooms.battle import progress as battle_progress  # noqa: E402
from autofighter.rooms.battle import snapshots as battle_snapshots  # noqa: E402
from autofighter.summons.base import Summon  # noqa: E402
from autofighter.summons.manager import SummonManager  # noqa: E402


class DummyEffectManager:
    """Minimal effect manager stub used for turn loop tests."""

    def __init__(self, owner):
        self.owner = owner
        self.hots: list[Any] = []
        self.mods: list[Any] = []

    async def tick(self, *_):
        return None

    async def on_action(self):
        return True

    def maybe_inflict_dot(self, *_):  # pragma: no cover - simple stub
        return None

    def add_hot(self, *_):  # pragma: no cover - simple stub
        return None

    def add_modifier(self, *_):  # pragma: no cover - simple stub
        return None


class SimpleEntity:
    """Lightweight battle entity with just the required attributes."""

    def __init__(self, entity_id: str, atk: int = 5, hp: int = 10):
        self.id = entity_id
        self.atk = atk
        self.hp = hp
        self.max_hp = hp
        self.summon_slot_capacity = 3
        self.action_points = 1
        self.actions_per_turn = 1
        self.damage_type = SimpleNamespace(id="test", on_action=_always_true)
        self.effect_manager = DummyEffectManager(self)
        self.ultimate_charge = 0
        self.ultimate_ready = False
        self._base_defense = 0
        self.crit_rate = 0.05
        self.crit_damage = 1.5
        self.effect_hit_rate = 0.0
        self.effect_resistance = 0.0
        self._base_mitigation = 0.0
        self._base_vitality = 0.0
        self.passives: list[str] = []
        self._active_effects: list[Any] = []

    async def maybe_regain(self, *_):
        return None

    def add_ultimate_charge(self, amount: int):
        self.ultimate_charge += amount

    def handle_ally_action(self, *_):  # pragma: no cover - simple stub
        return None

    async def apply_damage(self, amount: int, **_):
        self.hp = max(0, self.hp - amount)
        return amount


async def _always_true(*_, **__):
    return True


async def _noop_async(*_, **__):
    return None


def _noop(*_, **__):
    return None


class _RegistryStub:
    async def trigger(self, *_, **__):
        return None

    async def trigger_turn_start(self, *_, **__):
        return None

    async def trigger_turn_end(self, *_, **__):
        return None

    async def trigger_hit_landed(self, *_, **__):
        return None


class _Party:
    def __init__(self, members):
        self.members = list(members)


def _setup_common_player_patches(
    monkeypatch: pytest.MonkeyPatch,
    module,
    *,
    patch_finish_turn: bool = True,
) -> list[dict]:
    """Patch expensive collaborators with light stubs and capture updates."""

    updates: list[dict] = []

    async def record_progress(
        progress_cb,
        party_members,
        foes,
        enrage_state,
        rdr,
        extra_turns,
        turn,
        *,
        run_id,
        active_id,
        active_target_id=None,
        legacy_active_id=None,
        legacy_active_target_id=None,
        include_summon_foes=False,
        ended=None,
        visual_queue=None,
        turn_phase: str | None = None,
    ):
        updates.append(
            {
                "party": [getattr(member, "id", None) for member in party_members],
                "foes": [getattr(foe, "id", None) for foe in foes],
                "include_summon_foes": include_summon_foes,
                "active_id": active_id,
                "active_target_id": active_target_id,
                "legacy_active_id": legacy_active_id,
                "legacy_active_target_id": legacy_active_target_id,
                "turn": turn,
                "turn_phase": turn_phase,
                "party_hp": [getattr(member, "hp", None) for member in party_members],
                "foe_hp": [getattr(foe, "hp", None) for foe in foes],
            }
        )
        if progress_cb is not None:
            await progress_cb({})

    monkeypatch.setattr(module, "push_progress_update", record_progress)
    from autofighter.rooms.battle import turns as _turns
    from autofighter.rooms.battle.turn_loop import turn_end as _turn_end

    monkeypatch.setattr(_turn_end, "push_progress_update", record_progress)
    monkeypatch.setattr(_turns, "push_progress_update", record_progress)
    monkeypatch.setattr(_turn_end, "pace_sleep", _noop_async)
    monkeypatch.setattr(_turn_end, "_pace", _noop_async)
    monkeypatch.setattr(module, "pace_sleep", _noop_async)
    monkeypatch.setattr(module, "impact_pause", _noop_async)
    monkeypatch.setattr(module, "_pace", _noop_async)
    monkeypatch.setattr(module, "calc_animation_time", lambda *_, **__: 0)
    monkeypatch.setattr(module, "queue_log", _noop)
    async def _credit_if_dead_stub(**kwargs):
        return kwargs["exp_reward"], kwargs["temp_rdr"]

    monkeypatch.setattr(module, "credit_if_dead", _credit_if_dead_stub)
    if hasattr(module, "remove_dead_foes"):
        monkeypatch.setattr(module, "remove_dead_foes", _noop)
    if hasattr(module, "apply_enrage_bleed"):
        monkeypatch.setattr(module, "apply_enrage_bleed", _noop_async)
    if hasattr(module, "update_enrage_state"):
        monkeypatch.setattr(module, "update_enrage_state", _noop_async)
    if patch_finish_turn:
        monkeypatch.setattr(module, "finish_turn", _noop_async)
    monkeypatch.setattr(module, "register_snapshot_entities", _noop)
    monkeypatch.setattr(module, "mutate_snapshot_overlay", _noop)
    monkeypatch.setattr(module, "BUS", SimpleNamespace(emit_async=_noop_async))
    monkeypatch.setattr(module, "EffectManager", DummyEffectManager)
    monkeypatch.setattr(module, "SummonManager", SimpleNamespace())
    setattr(module.SummonManager, "get_summons", lambda *_: [])
    setattr(module.SummonManager, "add_summons_to_party", lambda *_: 0)

    return updates


@pytest.mark.asyncio
async def test_player_phase_pushes_update_for_new_summons(monkeypatch):
    updates = _setup_common_player_patches(monkeypatch, player_turn)

    party_member = SimpleEntity("ally")
    foe = SimpleEntity("foe")
    foe.effect_manager = DummyEffectManager(foe)

    summoned_foe = SimpleEntity("foe_summon")
    party_summon = SimpleEntity("ally_summon")

    summon_added = {"foe": False}

    def fake_add_summons_to_party(party):
        party.members.append(party_summon)
        return 1

    def fake_get_summons(owner_id):
        if owner_id == foe.id and not summon_added["foe"]:
            summon_added["foe"] = True
            return [summoned_foe]
        return []

    setattr(player_turn.SummonManager, "add_summons_to_party", fake_add_summons_to_party)
    setattr(player_turn.SummonManager, "get_summons", fake_get_summons)

    context = player_turn.TurnLoopContext(
        room=SimpleNamespace(),
        party=_Party([party_member]),
        combat_party=_Party([party_member]),
        registry=_RegistryStub(),
        foes=[foe],
        foe_effects=[foe.effect_manager],
        enrage_mods=[None],
        enrage_state=SimpleNamespace(active=False),
        progress=_noop_async,
        visual_queue=None,
        temp_rdr=0.0,
        exp_reward=0,
        run_id="run",
        battle_tasks={},
        abort=lambda _: None,
        credited_foe_ids=set(),
        turn=0,
    )

    result = await player_turn.execute_player_phase(context)

    assert result is True
    assert updates, "Expected at least one progress update call"
    summon_update = updates[-1]
    assert summon_update["include_summon_foes"] is True
    assert "ally_summon" in summon_update["party"]
    assert "foe_summon" in summon_update["foes"]
    assert summon_update["turn_phase"] == "resolve"


@pytest.mark.asyncio
async def test_player_turn_emits_start_before_damage(monkeypatch):
    updates = _setup_common_player_patches(
        monkeypatch,
        player_turn,
        patch_finish_turn=False,
    )

    party_member = SimpleEntity("ally")
    foe = SimpleEntity("foe")
    foe.effect_manager = DummyEffectManager(foe)

    context = player_turn.TurnLoopContext(
        room=SimpleNamespace(),
        party=_Party([party_member]),
        combat_party=_Party([party_member]),
        registry=_RegistryStub(),
        foes=[foe],
        foe_effects=[foe.effect_manager],
        enrage_mods=[None],
        enrage_state=SimpleNamespace(active=False),
        progress=_noop_async,
        visual_queue=None,
        temp_rdr=0.0,
        exp_reward=0,
        run_id="run",
        battle_tasks={},
        abort=lambda _: None,
        credited_foe_ids=set(),
        turn=0,
    )

    initial_hp = foe.hp

    result = await player_turn.execute_player_phase(context)

    assert result is True
    assert updates, "Expected at least one progress update call"

    start_index = next(
        (idx for idx, update in enumerate(updates) if update["turn_phase"] == "start"),
        None,
    )
    assert start_index is not None, "Missing start phase update"

    damage_index = next(
        (
            idx
            for idx, update in enumerate(updates)
            if update["foe_hp"] and any(hp != initial_hp for hp in update["foe_hp"])
        ),
        None,
    )
    assert damage_index is not None, "No update captured HP change"
    assert start_index < damage_index, "Start update should precede damage resolution"
    assert updates[damage_index]["turn_phase"] == "resolve"

    end_index = next(
        (idx for idx, update in enumerate(updates) if update["turn_phase"] == "end"),
        None,
    )
    assert end_index is not None, "Missing turn end update"
    assert damage_index < end_index, "Turn end should follow damage resolution"

    phases = [
        update["turn_phase"]
        for update in updates
        if update["turn_phase"] is not None
    ]
    assert phases, "Expected at least one phase-tagged update"
    assert phases[0] == "start"
    assert phases[-1] == "turn_end"
    mid_phases = phases[1:-1]
    assert any(phase == "resolve" for phase in mid_phases)
    if "end" in mid_phases:
        assert mid_phases[-1] == "end"
        assert all(phase == "resolve" for phase in mid_phases[:-1])
    else:
        assert all(phase == "resolve" for phase in mid_phases)


@pytest.mark.asyncio
async def test_foe_turn_emits_start_before_damage(monkeypatch):
    updates = _setup_common_player_patches(
        monkeypatch,
        foe_turn,
        patch_finish_turn=False,
    )

    acting_foe = SimpleEntity("foe")
    target = SimpleEntity("ally")
    target.effect_manager = DummyEffectManager(target)

    context = foe_turn.TurnLoopContext(
        room=SimpleNamespace(),
        party=_Party([target]),
        combat_party=_Party([target]),
        registry=_RegistryStub(),
        foes=[acting_foe],
        foe_effects=[acting_foe.effect_manager],
        enrage_mods=[None],
        enrage_state=SimpleNamespace(active=False),
        progress=_noop_async,
        visual_queue=None,
        temp_rdr=0.0,
        exp_reward=0,
        run_id="run",
        battle_tasks={},
        abort=lambda _: None,
        credited_foe_ids=set(),
        turn=0,
    )

    initial_hp = target.hp

    result = await foe_turn._run_foe_turn_iteration(
        context,
        0,
        acting_foe,
    )

    assert result.repeat is False
    assert result.battle_over is False
    assert updates, "Expected progress updates during foe action"

    start_index = next(
        (idx for idx, update in enumerate(updates) if update["turn_phase"] == "start"),
        None,
    )
    assert start_index is not None, "Missing start phase update"

    damage_index = next(
        (
            idx
            for idx, update in enumerate(updates)
            if update["party_hp"]
            and any(hp != initial_hp for hp in update["party_hp"])
        ),
        None,
    )
    assert damage_index is not None, "No update captured HP change"
    assert start_index < damage_index, "Start update should precede damage resolution"
    assert updates[damage_index]["turn_phase"] == "resolve"

    end_index = next(
        (idx for idx, update in enumerate(updates) if update["turn_phase"] == "end"),
        None,
    )
    assert end_index is not None, "Missing turn end update"
    assert damage_index < end_index, "Turn end should follow damage resolution"

    phases = [
        update["turn_phase"]
        for update in updates
        if update["turn_phase"] is not None
    ]
    assert phases, "Expected at least one phase-tagged update"
    assert phases[0] == "start"
    assert phases[-1] == "turn_end"
    mid_phases = phases[1:-1]
    assert any(phase == "resolve" for phase in mid_phases)
    if "end" in mid_phases:
        assert mid_phases[-1] == "end"
        assert all(phase == "resolve" for phase in mid_phases[:-1])
    else:
        assert all(phase == "resolve" for phase in mid_phases)


@pytest.mark.asyncio
async def test_summon_instance_ids_used_in_progress_and_events(monkeypatch):
    run_id = "run-instance"

    monkeypatch.setattr(SummonManager, "_active_summons", {}, raising=False)
    monkeypatch.setattr(SummonManager, "_summoner_refs", {}, raising=False)
    monkeypatch.setattr(SummonManager, "_instance_counters", {}, raising=False)
    monkeypatch.setattr(SummonManager, "_initialized", False, raising=False)
    monkeypatch.setattr(SummonManager, "initialize", classmethod(lambda cls: None))

    class _FakeSummon(SimpleNamespace):
        def __init__(self, summoner_id: str, summon_type: str):
            super().__init__(
                id=summon_type,
                instance_id="",
                summoner_id=summoner_id,
                summon_type=summon_type,
                summon_source="test",
                hp=10,
                max_hp=10,
                damage_type=SimpleNamespace(id="light"),
                effect_manager=DummyEffectManager(self),
                action_gauge=0,
                action_value=0.0,
                base_action_value=0.0,
            )

    def _fake_create_from_summoner(cls, summoner, summon_type, *_, **__):
        summoner_id = getattr(summoner, "id", str(id(summoner)))
        return _FakeSummon(summoner_id, summon_type)

    monkeypatch.setattr(Summon, "create_from_summoner", classmethod(_fake_create_from_summoner))

    summoner = SimpleEntity("luna")
    summoner.summon_slot_capacity = 4

    sword_one = SummonManager.create_summon(
        summoner,
        summon_type="luna_sword_lightstream",
        source="test",
        force_create=True,
    )
    sword_two = SummonManager.create_summon(
        summoner,
        summon_type="luna_sword_lightstream",
        source="test",
        force_create=True,
    )

    assert sword_one is not None
    assert sword_two is not None
    assert sword_one.instance_id != sword_two.instance_id

    battle_snapshots.prepare_snapshot_overlay(run_id, [summoner, sword_one, sword_two])

    battle_events._record_event(
        run_id,
        event_type="damage_taken",
        source=sword_one,
        target=sword_two,
        amount=5,
        metadata=None,
    )

    events = battle_snapshots.get_recent_events(run_id)
    assert events, "Expected recorded events for summon interaction"
    recorded = events[-1]
    assert recorded["source_id"] == sword_one.instance_id
    assert recorded.get("legacy_source_id") == sword_one.id
    assert recorded["target_id"] == sword_two.instance_id
    assert recorded.get("legacy_target_id") == sword_two.id

    active_id, legacy_active_id = battle_snapshots.canonical_entity_pair(sword_one)
    target_id, legacy_target_id = battle_snapshots.canonical_entity_pair(sword_two)

    payload = await battle_progress.build_battle_progress_payload(
        [summoner, sword_one],
        [sword_two],
        SimpleNamespace(as_payload=lambda: {}),
        rdr=0.0,
        extra_turns={},
        turn=3,
        run_id=run_id,
        active_id=active_id,
        active_target_id=target_id,
        legacy_active_id=legacy_active_id,
        legacy_active_target_id=legacy_target_id,
        include_summon_foes=True,
    )

    assert payload["active_id"] == sword_one.instance_id
    assert payload.get("legacy_active_id") == sword_one.id
    assert payload["active_target_id"] == sword_two.instance_id
    assert payload.get("legacy_active_target_id") == sword_two.id
    recent_events = payload.get("recent_events") or []
    assert recent_events, "Expected progress payload to include events"
    assert recent_events[-1]["source_id"] == sword_one.instance_id
    assert recent_events[-1].get("legacy_source_id") == sword_one.id


@pytest.mark.asyncio
async def test_foe_phase_pushes_update_for_new_summons(monkeypatch):
    updates = _setup_common_player_patches(monkeypatch, foe_turn)

    acting_foe = SimpleEntity("foe")
    target = SimpleEntity("ally")
    target.effect_manager = DummyEffectManager(target)

    summoned_foe = SimpleEntity("foe_summon")
    party_summon = SimpleEntity("ally_summon")

    summon_added = {"foe": False}

    def fake_add_summons_to_party(party):
        party.members.append(party_summon)
        return 1

    def fake_get_summons(owner_id):
        if owner_id == acting_foe.id and not summon_added["foe"]:
            summon_added["foe"] = True
            return [summoned_foe]
        return []

    setattr(foe_turn.SummonManager, "add_summons_to_party", fake_add_summons_to_party)
    setattr(foe_turn.SummonManager, "get_summons", fake_get_summons)

    context = foe_turn.TurnLoopContext(
        room=SimpleNamespace(),
        party=_Party([target]),
        combat_party=_Party([target]),
        registry=_RegistryStub(),
        foes=[acting_foe],
        foe_effects=[acting_foe.effect_manager],
        enrage_mods=[None],
        enrage_state=SimpleNamespace(active=False),
        progress=_noop_async,
        visual_queue=None,
        temp_rdr=0.0,
        exp_reward=0,
        run_id="run",
        battle_tasks={},
        abort=lambda _: None,
        credited_foe_ids=set(),
        turn=0,
    )

    result = await foe_turn.execute_foe_phase(context)

    assert result is True
    assert updates, "Expected at least one progress update call"
    summon_update = updates[-1]
    assert summon_update["include_summon_foes"] is True
    assert "ally_summon" in summon_update["party"]
    assert "foe_summon" in summon_update["foes"]
    assert summon_update["turn_phase"] == "resolve"
