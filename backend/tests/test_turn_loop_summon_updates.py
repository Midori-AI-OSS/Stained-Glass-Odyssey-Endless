"""Tests ensuring summon additions trigger immediate progress updates."""

from __future__ import annotations

import sys
from types import SimpleNamespace
from pathlib import Path

import pytest

_PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if _PROJECT_ROOT not in sys.path:
    sys.path.append(_PROJECT_ROOT)

from autofighter.rooms.battle.turn_loop import foe_turn
from autofighter.rooms.battle.turn_loop import player_turn


class DummyEffectManager:
    """Minimal effect manager stub used for turn loop tests."""

    def __init__(self, owner):
        self.owner = owner

    async def tick(self, *_):
        return None

    async def on_action(self):
        return True

    def maybe_inflict_dot(self, *_):  # pragma: no cover - simple stub
        return None


class SimpleEntity:
    """Lightweight battle entity with just the required attributes."""

    def __init__(self, entity_id: str, atk: int = 5, hp: int = 10):
        self.id = entity_id
        self.atk = atk
        self.hp = hp
        self.max_hp = hp
        self.action_points = 1
        self.actions_per_turn = 1
        self.damage_type = SimpleNamespace(id="test", on_action=_always_true)
        self.effect_manager = DummyEffectManager(self)
        self.ultimate_charge = 0
        self.ultimate_ready = False

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


def _setup_common_player_patches(monkeypatch: pytest.MonkeyPatch, module) -> list[dict]:
    """Patch expensive collaborators with light stubs and capture updates."""

    updates: list[dict] = []

    async def record_progress(
        progress_cb,
        party_members,
        foes,
        enrage_state,
        rdr,
        extra_turns,
        *,
        run_id,
        active_id,
        active_target_id=None,
        include_summon_foes=False,
        ended=None,
    ):
        updates.append(
            {
                "party": [getattr(member, "id", None) for member in party_members],
                "foes": [getattr(foe, "id", None) for foe in foes],
                "include_summon_foes": include_summon_foes,
                "active_id": active_id,
                "active_target_id": active_target_id,
            }
        )
        if progress_cb is not None:
            await progress_cb({})

    monkeypatch.setattr(module, "push_progress_update", record_progress)
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
