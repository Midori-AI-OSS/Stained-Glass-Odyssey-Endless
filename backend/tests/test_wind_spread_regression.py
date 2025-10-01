from __future__ import annotations

from types import SimpleNamespace

import pytest

from autofighter.rooms.battle.turn_loop.player_turn import _handle_wind_spread


class DummyFoe:
    def __init__(self, foe_id: str, hp: float) -> None:
        self.id = foe_id
        self.hp = hp
        self.level = 1

    async def apply_damage(self, amount: float, *, attacker, action_name: str) -> float:
        self.hp -= amount
        return amount


class DummyEffectManager:
    def __init__(self) -> None:
        self.dot_calls: list[tuple[object, float]] = []

    def maybe_inflict_dot(self, member, damage: float) -> None:
        self.dot_calls.append((member, damage))


class DummyRegistry:
    def __init__(self) -> None:
        self.hit_calls: list[tuple[tuple, dict]] = []

    async def trigger_hit_landed(self, *args, **kwargs) -> None:
        self.hit_calls.append((args, kwargs))


class DummyMember:
    def __init__(self, atk: float) -> None:
        self.atk = atk
        self.id = "player"
        self.damage_type = SimpleNamespace(id="wind")


@pytest.mark.asyncio
async def test_wind_spread_applies_damage_after_first_extra_foe_dies():
    target = DummyFoe("target", hp=999.0)
    first_extra = DummyFoe("extra-1", hp=10.0)
    second_extra = DummyFoe("extra-2", hp=50.0)

    member = DummyMember(atk=120.0)

    context = SimpleNamespace()
    context.foes = [target, first_extra, second_extra]
    context.foe_effects = [DummyEffectManager() for _ in context.foes]
    context.enrage_mods = [None for _ in context.foes]
    context.registry = DummyRegistry()
    context.combat_party = SimpleNamespace(members=[])
    context.credit_kwargs = {
        "credited_foe_ids": set(),
        "combat_party": SimpleNamespace(members=[]),
        "party": SimpleNamespace(members=[]),
        "room": SimpleNamespace(node=SimpleNamespace(index=0)),
    }
    context.exp_reward = 0
    context.temp_rdr = 0.0

    additional_hits = await _handle_wind_spread(context, member, target_index=0)

    assert additional_hits == 2
    assert first_extra not in context.foes
    assert second_extra in context.foes
    assert second_extra.hp < 50.0
    assert any(second_extra is args[1] for args, _ in context.registry.hit_calls)
    assert len(context.foes) == len(context.foe_effects)
