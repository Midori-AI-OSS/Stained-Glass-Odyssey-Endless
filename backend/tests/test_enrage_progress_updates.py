# ruff: noqa: E402, I001
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if _PROJECT_ROOT not in sys.path:
    sys.path.append(_PROJECT_ROOT)

from autofighter.rooms.battle import turns
from autofighter.rooms.battle.turn_loop import player_turn
from autofighter.rooms.battle.turns import EnrageState


class DummyMod:
    def __init__(self, mod_id: str = "enrage_atk"):
        self.id = mod_id
        self.removed = False

    def remove(self) -> None:  # pragma: no cover - simple flag for diagnostics
        self.removed = True


class DummyEffectManager:
    def __init__(self) -> None:
        self.mods: list[DummyMod] = []

    async def tick(self, *_: object) -> None:  # pragma: no cover - unused
        return None

    async def on_action(self, *_: object) -> bool:  # pragma: no cover - unused
        return True

    def add_modifier(self, mod: DummyMod) -> None:
        self.mods.append(mod)


class DummyRegistry:
    async def trigger(self, *_: object, **__: object) -> None:
        return None

    async def trigger_turn_start(self, *_: object, **__: object) -> None:
        return None

    async def trigger_turn_end(self, *_: object, **__: object) -> None:
        return None

    async def trigger_hit_landed(self, *_: object, **__: object) -> None:
        return None


class DummyParty:
    def __init__(self, members: list[DummyMember]) -> None:
        self.members = list(members)


class DummyDamageType:
    id = "test"

    async def on_action(self, *_: object, **__: object) -> bool:
        return True


class DummyMember:
    def __init__(self, member_id: str = "ally") -> None:
        self.id = member_id
        self.hp = 10
        self.max_hp = 10
        self.action_points = 1
        self.actions_per_turn = 1
        self.damage_type = DummyDamageType()
        self.effect_manager = DummyEffectManager()
        self.ultimate_charge = 0
        self.ultimate_ready = False

    async def maybe_regain(self, *_: object) -> None:
        return None

    async def apply_damage(self, amount: int, **_: object) -> int:  # pragma: no cover
        self.hp = max(0, self.hp - amount)
        return amount

    def add_ultimate_charge(self, amount: int) -> None:  # pragma: no cover - unused
        self.ultimate_charge += amount

    def handle_ally_action(self, *_: object) -> None:  # pragma: no cover - unused
        return None


class DummyFoe:
    def __init__(self, foe_id: str = "foe") -> None:
        self.id = foe_id
        self.hp = 10
        self.max_hp = 10
        self.passives: list[str] = []
        self.mods: list[str] = []

    async def apply_damage(self, amount: int, **_: object) -> int:  # pragma: no cover
        self.hp = max(0, self.hp - amount)
        return amount


async def _noop_async(*_: object, **__: object) -> None:
    return None


@pytest.mark.asyncio
async def test_update_enrage_state_returns_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    """Enrage activation should report changes for snapshot updates."""

    monkeypatch.setattr(turns, "create_stat_buff", lambda *_, **__: DummyMod())
    monkeypatch.setattr(turns, "set_enrage_percent", lambda value: None)

    state = EnrageState(threshold=0)
    foe = DummyFoe()
    manager = DummyEffectManager()
    enrage_mods: list[DummyMod | None] = [None]

    payload = await turns.update_enrage_state(
        turn=1,
        state=state,
        foes=[foe],
        foe_effects=[manager],
        enrage_mods=enrage_mods,
        party_members=[],
    )

    assert payload == state.as_payload()
    assert state.active is True
    assert state.stacks == 1
    assert "Enraged" in foe.passives
    assert isinstance(enrage_mods[0], DummyMod)


@pytest.mark.asyncio
async def test_player_phase_emits_snapshot_on_enrage(monkeypatch: pytest.MonkeyPatch) -> None:
    """Player turns should push an update immediately when enrage changes."""

    monkeypatch.setattr(turns, "create_stat_buff", lambda *_, **__: DummyMod())
    monkeypatch.setattr(turns, "set_enrage_percent", lambda value: None)

    updates: list[dict[str, object]] = []
    pace_calls: list[float] = []

    async def record_progress(
        _progress_cb,
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
        include_summon_foes=False,
        ended=None,
        turn_phase: str | None = None,
    ) -> None:
        updates.append(
            {
                "party": [getattr(member, "id", None) for member in party_members],
                "foes": [getattr(foe, "id", None) for foe in foes],
                "enrage": enrage_state.as_payload(),
                "active_id": active_id,
                "active_target_id": active_target_id,
                "include_summon_foes": include_summon_foes,
                "ended": ended,
                "turn": turn,
                "turn_phase": turn_phase,
            }
        )

    async def capture_sleep(delay: float) -> None:
        pace_calls.append(delay)

    monkeypatch.setattr(player_turn, "push_progress_update", record_progress)
    monkeypatch.setattr(player_turn, "pace_sleep", capture_sleep)
    monkeypatch.setattr(player_turn, "impact_pause", _noop_async)
    monkeypatch.setattr(player_turn, "_pace", _noop_async)
    monkeypatch.setattr(player_turn, "queue_log", lambda *_, **__: None)
    monkeypatch.setattr(player_turn, "_handle_ultimate", _noop_async)
    monkeypatch.setattr(player_turn, "apply_enrage_bleed", _noop_async)
    monkeypatch.setattr(player_turn, "credit_if_dead", lambda **kwargs: (kwargs["exp_reward"], kwargs["temp_rdr"]))
    monkeypatch.setattr(player_turn, "remove_dead_foes", lambda **__: None)
    monkeypatch.setattr(player_turn, "SummonManager", SimpleNamespace(add_summons_to_party=lambda *_: 0, get_summons=lambda *_: []))
    monkeypatch.setattr(player_turn, "register_snapshot_entities", lambda *_, **__: None)
    monkeypatch.setattr(player_turn, "mutate_snapshot_overlay", lambda *_, **__: None)
    monkeypatch.setattr(player_turn, "BUS", SimpleNamespace(emit_async=_noop_async))
    monkeypatch.setattr(player_turn, "calc_animation_time", lambda *_, **__: 0)
    monkeypatch.setattr(player_turn, "_any_foes_alive", lambda *_: False)

    member = DummyMember()
    foe = DummyFoe()
    manager = DummyEffectManager()
    context = player_turn.TurnLoopContext(
        room=SimpleNamespace(),
        party=DummyParty([member]),
        combat_party=DummyParty([member]),
        registry=DummyRegistry(),
        foes=[foe],
        foe_effects=[manager],
        enrage_mods=[None],
        enrage_state=EnrageState(threshold=0),
        progress=None,
        visual_queue=None,
        temp_rdr=0.0,
        exp_reward=0,
        run_id="run",
        battle_tasks={},
        abort=lambda *_: None,
        credited_foe_ids=set(),
        turn=0,
    )

    result = await player_turn.execute_player_phase(context)

    assert result is True
    assert updates, "Expected progress update when enrage activates"
    snapshot = updates[0]
    assert snapshot["enrage"]["active"] is True
    assert snapshot["enrage"]["stacks"] == 1
    assert snapshot["active_id"] == member.id
    assert snapshot["active_target_id"] is None
    assert pace_calls == [player_turn.YIELD_MULTIPLIER]
    assert context.enrage_mods[0] is not None
