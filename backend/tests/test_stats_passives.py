import random

import pytest

from autofighter.passives import PassiveRegistry
from autofighter.stat_effect import StatEffect
from autofighter.stats import Stats


def test_fractional_level_up_gains(monkeypatch):
    monkeypatch.setattr(random, "uniform", lambda a, b: 0)
    stats = Stats(level_up_gains={"atk": 0.5})
    stats.level += 1
    stats._on_level_up()
    assert stats.get_base_stat("atk") == pytest.approx(200 + 0.5 * stats.level)


@pytest.mark.asyncio
async def test_player_level_up_bonus_no_type_error(monkeypatch):
    monkeypatch.setattr(random, "uniform", lambda a, b: 0)
    stats = Stats()
    stats.passives.append("player_level_up_bonus")
    stats.level += 1
    stats._on_level_up()
    registry = PassiveRegistry()
    await registry.trigger_level_up(stats, new_level=stats.level)
    assert any(
        e.name == "player_level_up_bonus_level_bonus" for e in stats.get_active_effects()
    )


class NewPassive:
    plugin_type = "passive"
    id = "new_dummy"
    name = "New Dummy"
    trigger = "level_up"

    async def apply(self, target: Stats, new_level: int) -> None:
        effect = StatEffect(
            name="new_dummy_effect",
            stat_modifiers={"atk": 1.0},
            source=self.id,
        )
        target.add_effect(effect)


class LegacyPassive:
    plugin_type = "passive"
    id = "legacy_dummy"
    name = "Legacy Dummy"
    trigger = "level_up"

    async def apply(self, target: Stats) -> None:
        effect = StatEffect(
            name="legacy_dummy_effect",
            stat_modifiers={"atk": 1.0},
            source=self.id,
        )
        target.add_effect(effect)


@pytest.mark.asyncio
async def test_trigger_level_up_handles_new_and_legacy_passives():
    stats = Stats()
    stats.passives = ["new_dummy", "legacy_dummy"]
    registry = PassiveRegistry()
    registry._registry = {
        "new_dummy": NewPassive,
        "legacy_dummy": LegacyPassive,
    }
    await registry.trigger_level_up(stats, new_level=2)
    effect_names = [e.name for e in stats.get_active_effects()]
    assert "new_dummy_effect" in effect_names
    assert "legacy_dummy_effect" in effect_names
