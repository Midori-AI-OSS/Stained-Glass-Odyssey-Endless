import types
from types import SimpleNamespace

import pytest

from plugins.damage_types.dark import Dark
from plugins.damage_types.light import Light


class _DrainDummy:
    def __init__(self, hp: int) -> None:
        self.hp = hp

    async def apply_cost_damage(self, amount: int) -> int:
        self.hp = max(self.hp - amount, 0)
        return amount


class _LightManager:
    def __init__(self) -> None:
        self.hots_added = 0

    async def add_hot(self, _hot) -> None:
        self.hots_added += 1


class _LightAlly:
    def __init__(self, *, hp: int, max_hp: int) -> None:
        self.hp = hp
        self.max_hp = max_hp
        self.effect_manager = _LightManager()
        self.heal_calls: list[int] = []

    async def apply_healing(self, amount: int, *, healer) -> int:
        self.heal_calls.append(amount)
        return amount


@pytest.mark.asyncio
async def test_dark_on_action_skips_invalid_targets(monkeypatch):
    recorded: list[SimpleNamespace] = []

    async def fake_pace(actor, *, duration=None):
        recorded.append(SimpleNamespace(actor=actor, duration=duration))

    monkeypatch.setattr(
        "autofighter.rooms.battle.pacing.pace_per_target",
        fake_pace,
        raising=True,
    )

    actor = SimpleNamespace()
    allies = [_DrainDummy(1), _DrainDummy(50), _DrainDummy(20)]

    dark = Dark()
    result = await dark.on_action(actor, allies, enemies=[])

    assert result is True
    assert len(recorded) == 2
    assert allies[1].hp == 45
    assert allies[2].hp == 18


@pytest.mark.asyncio
async def test_light_on_action_skips_defeated_allies(monkeypatch):
    recorded: list[types.SimpleNamespace] = []

    async def fake_pace(actor, *, duration=None):
        recorded.append(SimpleNamespace(actor=actor, duration=duration))

    monkeypatch.setattr(
        "autofighter.rooms.battle.pacing.pace_per_target",
        fake_pace,
        raising=True,
    )

    monkeypatch.setattr(
        "plugins.damage_effects.create_hot",
        lambda _element, _actor: object(),
        raising=True,
    )

    dead = _LightAlly(hp=0, max_hp=100)
    living = _LightAlly(hp=80, max_hp=100)
    actor = SimpleNamespace()

    light = Light()
    result = await light.on_action(actor, [dead, living], enemies=[])

    assert result is True
    assert len(recorded) == 2
    assert dead.effect_manager.hots_added == 0
    assert living.effect_manager.hots_added == 1
