"""Unit tests for enrage helpers."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from autofighter.rooms.battle.enrage import EnrageState
from autofighter.rooms.battle.enrage import apply_enrage_bleed
from autofighter.rooms.battle.enrage import update_enrage_state


class DummyMod:
    """Simple modifier stub used by tests."""

    def __init__(self, atk_mult: float) -> None:
        self.id = "enrage_atk"
        self.atk_mult = atk_mult
        self.removed = False

    def remove(self) -> None:
        self.removed = True


class DummyEffectManager:
    """Minimal effect manager stub."""

    def __init__(self, stats: Any | None = None) -> None:
        self.stats = stats or SimpleNamespace(max_hp=1)
        self.mods: list[Any] = []
        self.dots: list[Any] = []

    async def add_modifier(self, mod: Any) -> None:
        self.mods.append(mod)

    def add_dot(self, dot: Any) -> None:
        self.dots.append(dot)


class DummyCombatant:
    """Stats-like object for both party members and foes."""

    def __init__(self, max_hp: int = 1000) -> None:
        self.hp = max_hp
        self.max_hp = max_hp
        self.passives: list[str] = []
        self.mods: list[str] = []
        self.effect_manager = DummyEffectManager(self)
        self.received_damage: list[int] = []

    async def apply_damage(self, amount: int) -> None:
        self.received_damage.append(amount)


@pytest.mark.asyncio()
async def test_update_enrage_state_activates_and_adds_modifier() -> None:
    """Cross-turn enrage activation should add modifiers via dependency hooks."""

    state = EnrageState(threshold=5)
    foe = DummyCombatant(max_hp=800)
    foe_effect = DummyEffectManager()
    enrage_mods: list[Any | None] = [None]
    party_members = [DummyCombatant(max_hp=900)]

    set_calls: list[float] = []

    def fake_set_enrage(value: float) -> None:
        set_calls.append(value)

    created_mods: list[DummyMod] = []

    def fake_create_stat_buff(*_args: Any, atk_mult: float, **_kwargs: Any) -> DummyMod:
        mod = DummyMod(atk_mult=atk_mult)
        created_mods.append(mod)
        return mod

    payload = await update_enrage_state(
        turn=8,
        state=state,
        foes=[foe],
        foe_effects=[foe_effect],
        enrage_mods=enrage_mods,
        party_members=party_members,
        set_enrage_percent=fake_set_enrage,
        create_stat_buff=fake_create_stat_buff,
    )

    assert payload == {"active": True, "stacks": 3, "turns": 3}
    assert state.active is True
    assert state.stacks == 3
    assert set_calls and set_calls[0] == pytest.approx(4.05)
    assert enrage_mods[0] is created_mods[0]
    assert created_mods[0].atk_mult == pytest.approx(7.0)
    assert foe_effect.mods == created_mods
    assert "Enraged" in foe.passives


@pytest.mark.asyncio()
async def test_apply_enrage_bleed_stacks_for_both_sides() -> None:
    """Bleed application should respect provided DoT factory and ratios."""

    state = EnrageState(threshold=0, active=True, stacks=10)
    party_member = DummyCombatant(max_hp=1200)
    foe = DummyCombatant(max_hp=600)
    foe_effect = DummyEffectManager(SimpleNamespace(max_hp=foe.max_hp))

    created_effects: list[tuple[str, int, int, str]] = []

    def fake_damage_over_time(name: str, dmg: int, turns: int, key: str) -> dict[str, Any]:
        created_effects.append((name, dmg, turns, key))
        return {"name": name, "damage": dmg, "turns": turns, "key": key}

    await apply_enrage_bleed(
        state,
        party_members=[party_member],
        foes=[foe],
        foe_effects=[foe_effect],
        damage_over_time_factory=fake_damage_over_time,
        party_bleed_ratio=0.5,
        foe_bleed_ratio=0.25,
    )

    assert state.bleed_applies == 1
    assert party_member.effect_manager.dots == [
        {"name": "Enrage Bleed", "damage": 600, "turns": 10, "key": "enrage_bleed"}
    ]
    assert foe_effect.dots == [
        {"name": "Enrage Bleed", "damage": 150, "turns": 10, "key": "enrage_bleed"}
    ]
    assert created_effects == [
        ("Enrage Bleed", 600, 10, "enrage_bleed"),
        ("Enrage Bleed", 150, 10, "enrage_bleed"),
    ]
