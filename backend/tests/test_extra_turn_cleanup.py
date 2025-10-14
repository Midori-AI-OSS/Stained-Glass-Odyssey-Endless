from __future__ import annotations

from types import SimpleNamespace

import pytest

from autofighter.rooms.battle import pacing as battle_pacing
from autofighter.rooms.battle.turn_helpers import remove_dead_foes
from autofighter.rooms.battle.turn_loop import player_turn
from autofighter.stats import BUS
from autofighter.summons.manager import SummonManager
import plugins.event_bus as event_bus_module


def test_remove_dead_foes_clears_extra_turns() -> None:
    battle_pacing._EXTRA_TURNS.clear()

    foe = SimpleNamespace(hp=0)
    foe_effect = object()
    enrage_mod = object()
    battle_pacing._EXTRA_TURNS[id(foe)] = 2

    remove_dead_foes(
        foes=[foe],
        foe_effects=[foe_effect],
        enrage_mods=[enrage_mod],
    )

    assert battle_pacing._EXTRA_TURNS.get(id(foe)) is None


@pytest.mark.asyncio
async def test_player_iteration_dead_member_clears_extra_turns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    battle_pacing._EXTRA_TURNS.clear()

    member = SimpleNamespace(hp=0)
    member_effect = object()
    battle_pacing._EXTRA_TURNS[id(member)] = 3

    async def _noop(*_: object, **__: object) -> None:
        return None

    monkeypatch.setattr(player_turn, "pace_sleep", _noop)

    result = await player_turn._run_player_turn_iteration(
        SimpleNamespace(),
        member,
        member_effect,
    )

    assert result.repeat is False
    assert result.battle_over is False
    assert battle_pacing._EXTRA_TURNS.get(id(member)) is None


@pytest.mark.asyncio
async def test_remove_summon_clears_extra_turns(monkeypatch: pytest.MonkeyPatch) -> None:
    event_bus_module.bus._subs.clear()
    SummonManager.cleanup()
    battle_pacing._EXTRA_TURNS.clear()

    async def _noop_emit(*_: object, **__: object) -> None:
        return None

    monkeypatch.setattr(BUS, "emit_batched_async", _noop_emit)

    summoner = SimpleNamespace(id="summoner")
    summon = SimpleNamespace(id="summon", summoner_id="summoner", is_temporary=True)
    SummonManager._active_summons[summoner.id] = [summon]
    SummonManager._summoner_refs[summoner.id] = summoner
    battle_pacing._EXTRA_TURNS[id(summon)] = 1

    removed = await SummonManager.remove_summon(summon, "test_reason")

    assert removed is True
    assert battle_pacing._EXTRA_TURNS.get(id(summon)) is None
    SummonManager.cleanup()
