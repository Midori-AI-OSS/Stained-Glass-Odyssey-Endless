from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from autofighter.rooms.battle.pacing import YIELD_MULTIPLIER
from autofighter.rooms.battle.pacing import impact_pause
from autofighter.stats import Stats
from autofighter.stats import calc_animation_time


def test_animation_time_scaling() -> None:
    actor = Stats()
    actor.animation_duration = 0.5
    actor.animation_per_target = 0.25
    assert calc_animation_time(actor, 1) == 0.5
    assert calc_animation_time(actor, 3) == 1.0


@pytest.mark.asyncio
async def test_impact_pause_yields_without_animation(monkeypatch) -> None:
    actor = Stats()
    actor.animation_duration = 0.0
    actor.animation_per_target = 0.0

    calls: list[float] = []

    async def fake_sleep(multiplier: float = 1.0) -> None:
        calls.append(multiplier)

    monkeypatch.setattr(
        "autofighter.rooms.battle.pacing.pace_sleep",
        fake_sleep,
        raising=True,
    )

    await impact_pause(actor, 1)

    assert calls == [YIELD_MULTIPLIER]


@pytest.mark.asyncio
async def test_impact_pause_skips_when_animation_present(monkeypatch) -> None:
    actor = Stats()
    actor.animation_duration = 0.3
    actor.animation_per_target = 0.0

    async def fake_sleep(multiplier: float = 1.0) -> None:  # pragma: no cover - should not run
        raise AssertionError("pace_sleep should not be awaited for animated actions")

    monkeypatch.setattr(
        "autofighter.rooms.battle.pacing.pace_sleep",
        fake_sleep,
        raising=True,
    )

    await impact_pause(actor, 1, duration=0.3)
