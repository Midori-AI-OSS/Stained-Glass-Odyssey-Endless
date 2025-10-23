import types

import pytest

from autofighter.action_queue import TURN_COUNTER_ID
from autofighter.rooms.battle import pacing
from autofighter.rooms.battle.turn_loop import initialization as init


class DummyParty:
    def __init__(self, members):
        self.members = members


class DummyQueue:
    def __init__(self, ids):
        self.combatants = [types.SimpleNamespace(id=ident) for ident in ids]


def make_context(queue, progress=None):
    return init.TurnLoopContext(
        room=object(),
        party=DummyParty([]),
        combat_party=DummyParty([]),
        registry=None,
        foes=[],
        foe_effects=[],
        enrage_mods=[],
        enrage_state=None,
        progress=progress,
        visual_queue=queue,
        temp_rdr=0.0,
        exp_reward=0,
        run_id=None,
        battle_tasks={},
        abort=lambda _: None,
        credited_foe_ids=set(),
    )


def test_intro_pause_skips_without_visual_queue():
    context = make_context(None)
    assert init._intro_pause_seconds(context) == 0.0


def test_intro_pause_ignores_turn_counter_only():
    queue = DummyQueue([TURN_COUNTER_ID])
    context = make_context(queue)
    assert init._intro_pause_seconds(context) == 0.0


def test_intro_pause_scales_with_visible_combatants():
    queue = DummyQueue([TURN_COUNTER_ID, "hero", "foe", "summon"])
    context = make_context(queue)
    duration = init._intro_pause_seconds(context)
    assert duration > 0
    assert duration <= init._INTRO_MAX_SECONDS
    expected = init._INTRO_BASE_SECONDS + init._INTRO_PER_ACTOR_SECONDS
    assert duration == pytest.approx(expected)


@pytest.mark.asyncio
async def test_send_initial_progress_skips_pause_when_queue_missing(monkeypatch):
    recorded = []

    async def fake_push(*args, **kwargs):
        return None

    async def fake_pace(multiplier):
        recorded.append(multiplier)

    monkeypatch.setattr(init, "push_progress_update", fake_push)
    monkeypatch.setattr(init, "pace_sleep", fake_pace)

    async def progress(_payload):
        return None

    context = make_context(None, progress=progress)
    context.combat_party = DummyParty([])
    context.foes = []
    context.enrage_state = object()

    await init._send_initial_progress(context)

    assert recorded == []


@pytest.mark.asyncio
async def test_send_initial_progress_applies_intro_pause(monkeypatch):
    multipliers = []

    async def fake_push(*args, **kwargs):
        return None

    async def fake_pace(multiplier):
        multipliers.append(multiplier)

    monkeypatch.setattr(init, "push_progress_update", fake_push)
    monkeypatch.setattr(init, "pace_sleep", fake_pace)

    async def progress(_payload):
        return None

    queue = DummyQueue([TURN_COUNTER_ID, "hero", "foe"])
    context = make_context(queue, progress=progress)
    context.combat_party = DummyParty([types.SimpleNamespace(id="hero")])
    context.foes = [types.SimpleNamespace(id="foe")]
    context.enrage_state = object()

    pacing.set_turn_pacing(pacing.DEFAULT_TURN_PACING)
    await init._send_initial_progress(context)

    assert multipliers
    expected_seconds = init._intro_pause_seconds(context)
    expected_multiplier = expected_seconds / pacing.TURN_PACING
    assert multipliers[0] == pytest.approx(expected_multiplier)

