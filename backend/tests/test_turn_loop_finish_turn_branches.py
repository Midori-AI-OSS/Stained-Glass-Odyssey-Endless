# ruff: noqa: E402
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

_PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if _PROJECT_ROOT not in sys.path:
    sys.path.append(_PROJECT_ROOT)

from autofighter.rooms.battle.turn_loop import foe_turn  # noqa: E402
from autofighter.rooms.battle.turn_loop import player_turn  # noqa: E402
from autofighter.rooms.battle.turn_loop.initialization import (
    TurnLoopContext,  # noqa: E402
)


class DummyRegistry:
    async def trigger(self, *args, **kwargs):
        return None

    async def trigger_turn_start(self, *args, **kwargs):
        return None

    async def trigger_turn_end(self, *args, **kwargs):
        return None

    async def trigger_hit_landed(self, *args, **kwargs):
        return None


class DummyParty(SimpleNamespace):
    members: list


class DummyEffectManager:
    async def tick(self, *_args, **_kwargs):
        return None

    async def on_action(self):
        return True


class DummyActor:
    def __init__(self, actor_id: str, hp: int = 10):
        self.id = actor_id
        self.hp = hp
        self.action_points = 1
        self.actions_per_turn = 1
        self.effect_manager = DummyEffectManager()

    async def maybe_regain(self, _turn: int) -> None:
        return None

    def add_ultimate_charge(self, _amount: int) -> None:
        return None

    def handle_ally_action(self, _ally: "DummyActor") -> None:
        return None


@pytest.mark.asyncio
async def test_player_turn_finishes_when_no_foes(monkeypatch: pytest.MonkeyPatch) -> None:
    finish_calls: list[tuple[DummyActor, str | None]] = []

    async def fake_finish(
        context: TurnLoopContext,
        actor: DummyActor,
        action_start: float,
        *,
        include_summon_foes: bool = False,
        active_target_id: str | None = None,
    ) -> None:
        finish_calls.append((actor, active_target_id))

    async def fake_update_enrage_state(*_args, **_kwargs):
        return False

    async def fake_emit(*_args, **_kwargs):
        return None

    monkeypatch.setattr(player_turn, "finish_turn", fake_finish)
    monkeypatch.setattr(player_turn, "update_enrage_state", fake_update_enrage_state)
    monkeypatch.setattr(player_turn.BUS, "emit_async", fake_emit)

    member = DummyActor("hero")
    context = TurnLoopContext(
        room=SimpleNamespace(),
        party=DummyParty(members=[member]),
        combat_party=DummyParty(members=[member]),
        registry=DummyRegistry(),
        foes=[SimpleNamespace(id="foe-1", hp=0)],
        foe_effects=[],
        enrage_mods=[],
        enrage_state=SimpleNamespace(active=False),
        progress=None,
        visual_queue=None,
        temp_rdr=0.0,
        exp_reward=0,
        run_id=None,
        battle_tasks={},
        abort=lambda _run_id: None,
        credited_foe_ids=set(),
        turn=0,
    )

    result = await player_turn._run_player_turn_iteration(
        context,
        member,
        member.effect_manager,
    )

    assert finish_calls == [(member, None)]
    assert result.battle_over is True
    assert result.repeat is False


@pytest.mark.asyncio
async def test_player_turn_finishes_when_targets_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    finish_calls: list[tuple[DummyActor, str | None]] = []

    async def fake_finish(
        context: TurnLoopContext,
        actor: DummyActor,
        action_start: float,
        *,
        include_summon_foes: bool = False,
        active_target_id: str | None = None,
    ) -> None:
        finish_calls.append((actor, active_target_id))

    async def fake_update_enrage_state(*_args, **_kwargs):
        return False

    async def fake_emit(*_args, **_kwargs):
        return None

    monkeypatch.setattr(player_turn, "finish_turn", fake_finish)
    monkeypatch.setattr(player_turn, "update_enrage_state", fake_update_enrage_state)
    monkeypatch.setattr(player_turn.BUS, "emit_async", fake_emit)
    monkeypatch.setattr(player_turn, "_any_foes_alive", lambda _foes: True)

    member = DummyActor("hero")
    context = TurnLoopContext(
        room=SimpleNamespace(),
        party=DummyParty(members=[member]),
        combat_party=DummyParty(members=[member]),
        registry=DummyRegistry(),
        foes=[SimpleNamespace(id="foe-1", hp=0)],
        foe_effects=[],
        enrage_mods=[],
        enrage_state=SimpleNamespace(active=False),
        progress=None,
        visual_queue=None,
        temp_rdr=0.0,
        exp_reward=0,
        run_id=None,
        battle_tasks={},
        abort=lambda _run_id: None,
        credited_foe_ids=set(),
        turn=0,
    )

    result = await player_turn._run_player_turn_iteration(
        context,
        member,
        member.effect_manager,
    )

    assert finish_calls == [(member, None)]
    assert result.battle_over is True
    assert result.repeat is False


@pytest.mark.asyncio
async def test_player_turn_finishes_after_removing_dead(monkeypatch: pytest.MonkeyPatch) -> None:
    finish_calls: list[tuple[DummyActor, str | None]] = []

    async def fake_finish(
        context: TurnLoopContext,
        actor: DummyActor,
        action_start: float,
        *,
        include_summon_foes: bool = False,
        active_target_id: str | None = None,
    ) -> None:
        finish_calls.append((actor, active_target_id))

    async def fake_update_enrage_state(*_args, **_kwargs):
        return False

    async def fake_emit(*_args, **_kwargs):
        return None

    async def fake_credit_if_dead(*_args, **_kwargs):
        return (0, 0.0)

    def fake_remove_dead_foes(*, foes, foe_effects, enrage_mods):
        foes.clear()
        foe_effects.clear()
        enrage_mods.clear()

    monkeypatch.setattr(player_turn, "finish_turn", fake_finish)
    monkeypatch.setattr(player_turn, "update_enrage_state", fake_update_enrage_state)
    monkeypatch.setattr(player_turn.BUS, "emit_async", fake_emit)
    monkeypatch.setattr(player_turn, "credit_if_dead", fake_credit_if_dead)
    monkeypatch.setattr(player_turn, "remove_dead_foes", fake_remove_dead_foes)
    monkeypatch.setattr(player_turn, "mutate_snapshot_overlay", lambda *args, **kwargs: None)

    member = DummyActor("hero")
    target = SimpleNamespace(id="foe-1", hp=10)

    class RemovingEffectManager(DummyEffectManager):
        async def tick(self, *_args, **_kwargs):
            target.hp = 0

    member_effect = RemovingEffectManager()
    target_manager = SimpleNamespace()

    context = TurnLoopContext(
        room=SimpleNamespace(),
        party=DummyParty(members=[member]),
        combat_party=DummyParty(members=[member]),
        registry=DummyRegistry(),
        foes=[target],
        foe_effects=[target_manager],
        enrage_mods=[None],
        enrage_state=SimpleNamespace(active=False),
        progress=None,
        visual_queue=None,
        temp_rdr=0.0,
        exp_reward=0,
        run_id=None,
        battle_tasks={},
        abort=lambda _run_id: None,
        credited_foe_ids=set(),
        turn=0,
    )

    result = await player_turn._run_player_turn_iteration(
        context,
        member,
        member_effect,
    )

    assert finish_calls == [(member, "foe-1")]
    assert result.battle_over is True
    assert result.repeat is False


@pytest.mark.asyncio
async def test_foe_turn_finishes_when_all_foes_dead(monkeypatch: pytest.MonkeyPatch) -> None:
    finish_calls: list[tuple[DummyActor, str | None]] = []

    async def fake_finish(
        context: TurnLoopContext,
        actor: DummyActor,
        action_start: float,
        *,
        include_summon_foes: bool = False,
        active_target_id: str | None = None,
    ) -> None:
        finish_calls.append((actor, active_target_id))

    async def fake_emit(*_args, **_kwargs):
        return None

    async def fake_credit_if_dead(*_args, **_kwargs):
        return (0, 0.0)

    monkeypatch.setattr(foe_turn, "finish_turn", fake_finish)
    monkeypatch.setattr(foe_turn.BUS, "emit_async", fake_emit)
    monkeypatch.setattr(foe_turn, "credit_if_dead", fake_credit_if_dead)
    monkeypatch.setattr(foe_turn, "mutate_snapshot_overlay", lambda *args, **kwargs: None)

    acting_foe = DummyActor("foe-actor", hp=10)
    target = DummyActor("hero", hp=10)

    class RemovingFoeManager(DummyEffectManager):
        async def tick(self, *_args, **_kwargs):
            acting_foe.hp = 0

    foe_manager = RemovingFoeManager()
    target.effect_manager = DummyEffectManager()

    context = TurnLoopContext(
        room=SimpleNamespace(),
        party=DummyParty(members=[target]),
        combat_party=DummyParty(members=[target]),
        registry=DummyRegistry(),
        foes=[acting_foe],
        foe_effects=[foe_manager],
        enrage_mods=[None],
        enrage_state=SimpleNamespace(active=False),
        progress=None,
        visual_queue=None,
        temp_rdr=0.0,
        exp_reward=0,
        run_id=None,
        battle_tasks={},
        abort=lambda _run_id: None,
        credited_foe_ids=set(),
        turn=0,
    )

    result = await foe_turn._run_foe_turn_iteration(
        context,
        0,
        acting_foe,
    )

    assert finish_calls == [(acting_foe, "hero")]
    assert result.battle_over is True
    assert result.repeat is False
