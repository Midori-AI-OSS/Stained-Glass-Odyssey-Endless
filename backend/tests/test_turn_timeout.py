"""Regression tests for the battle turn timeout safeguards."""

from __future__ import annotations

import asyncio
from datetime import datetime
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

_PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if _PROJECT_ROOT not in sys.path:
    sys.path.append(_PROJECT_ROOT)

from battle_logging.summary import BattleEvent  # noqa: E402

from autofighter.rooms.battle.turn_loop import TurnTimeoutError  # noqa: E402
from autofighter.rooms.battle.turn_loop import player_turn  # noqa: E402
from autofighter.rooms.battle.turn_loop import timeouts as turn_timeouts  # noqa: E402


class DummyEffectManager:
    """Minimal effect manager stub that can be customized per test."""

    def __init__(self, owner):
        self.owner = owner

    async def tick(self, *_):  # pragma: no cover - replaced in tests
        return None

    async def on_action(self):
        return True

    async def maybe_inflict_dot(self, *_):  # pragma: no cover - simple stub
        return None


class SimpleEntity:
    """Lightweight battle entity implementing the required attributes."""

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


def _noop(*_, **__):  # pragma: no cover - trivial helper
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


@pytest.mark.asyncio
async def test_player_turn_timeout_creates_log(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """A stalled player iteration should raise TurnTimeoutError and record actions."""

    monkeypatch.setattr(player_turn, "push_progress_update", _noop_async)
    monkeypatch.setattr(player_turn, "pace_sleep", _noop_async)
    monkeypatch.setattr(player_turn, "impact_pause", _noop_async)
    monkeypatch.setattr(player_turn, "_pace", _noop_async)
    monkeypatch.setattr(player_turn, "calc_animation_time", lambda *_, **__: 0)
    monkeypatch.setattr(player_turn, "queue_log", _noop)
    async def _credit_if_dead_stub(**kwargs):
        return kwargs["exp_reward"], kwargs["temp_rdr"]

    monkeypatch.setattr(player_turn, "credit_if_dead", _credit_if_dead_stub)
    monkeypatch.setattr(player_turn, "remove_dead_foes", _noop)
    monkeypatch.setattr(player_turn, "apply_enrage_bleed", _noop_async)
    monkeypatch.setattr(player_turn, "update_enrage_state", _noop_async)
    monkeypatch.setattr(player_turn, "finish_turn", _noop_async)
    monkeypatch.setattr(player_turn, "register_snapshot_entities", _noop)
    monkeypatch.setattr(player_turn, "mutate_snapshot_overlay", _noop)
    monkeypatch.setattr(player_turn, "BUS", SimpleNamespace(emit_async=_noop_async))
    monkeypatch.setattr(player_turn, "EffectManager", DummyEffectManager)
    monkeypatch.setattr(
        player_turn,
        "SummonManager",
        SimpleNamespace(add_summons_to_party=lambda *_: 0, get_summons=lambda *_: []),
    )

    member = SimpleEntity("hero")
    foe = SimpleEntity("foe")
    foe.effect_manager = DummyEffectManager(foe)

    async def slow_tick(*_, **__):
        await asyncio.sleep(40)

    member.effect_manager = DummyEffectManager(member)
    monkeypatch.setattr(member.effect_manager, "tick", slow_tick, raising=False)

    context = player_turn.TurnLoopContext(
        room=SimpleNamespace(),
        party=_Party([member]),
        combat_party=_Party([member]),
        registry=_RegistryStub(),
        foes=[foe],
        foe_effects=[foe.effect_manager],
        enrage_mods=[None],
        enrage_state=SimpleNamespace(active=False),
        progress=_noop_async,
        visual_queue=None,
        temp_rdr=0.0,
        exp_reward=0,
        run_id="run-test",
        battle_tasks={},
        abort=lambda *_: None,
        credited_foe_ids=set(),
        turn=0,
    )

    events = [
        BattleEvent(
            timestamp=datetime.now(),
            event_type="test_event",
            attacker_id=member.id,
            target_id=None,
            amount=5,
        )
    ]
    battle_logger = SimpleNamespace(
        summary=SimpleNamespace(events=events),
        summary_path=tmp_path,
    )
    run_logger = SimpleNamespace(current_battle_logger=battle_logger)
    monkeypatch.setattr(turn_timeouts, "get_current_run_logger", lambda: run_logger)

    monkeypatch.setattr(player_turn, "TURN_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(turn_timeouts, "TURN_TIMEOUT_SECONDS", 0.01)

    with pytest.raises(TurnTimeoutError) as excinfo:
        await player_turn.execute_player_phase(context)

    error = excinfo.value
    timeout_path = Path(error.file_path)
    assert timeout_path.exists(), "Timeout log file should be created"
    payload = json.loads(timeout_path.read_text())
    assert payload["actor_id"] == member.id
    assert payload["events"], "Expected captured events for the stalled actor"
