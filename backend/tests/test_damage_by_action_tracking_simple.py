import asyncio
from collections import defaultdict
from typing import DefaultDict

import pytest

from autofighter.stats import BUS
from autofighter.stats import Stats
from autofighter.stats import set_battle_active
from plugins.characters.carly import Carly


def _entity_key(entity: Stats) -> str:
    return (
        getattr(entity, "id", None)
        or getattr(entity, "name", None)
        or entity.__class__.__name__
    )


def _capture_damage_and_healing():
    data: DefaultDict[str, DefaultDict[str, int]] = defaultdict(
        lambda: defaultdict(int)
    )

    async def on_damage_dealt(attacker, _target, amount, _source_type, *extra):
        action_name = extra[2] if len(extra) >= 3 else None
        details = extra[3] if len(extra) >= 4 and isinstance(extra[3], dict) else {}
        label = action_name or details.get("action_name") or "Unknown"
        data[_entity_key(attacker)][label] += int(amount)

    async def on_heal(healer, _target, amount, source_type, source_name=None):
        if source_name:
            label = f"{source_name} Healing"
        else:
            label = source_type.replace("_", " ").title()
        data[_entity_key(healer)][label] += int(amount)

    BUS.subscribe("damage_dealt", on_damage_dealt)
    BUS.subscribe("heal", on_heal)
    return data, on_damage_dealt, on_heal


@pytest.mark.asyncio
async def test_healing_in_damage_by_action():
    """Test that healing appears in damage_by_action tracking."""
    player = Carly()
    player.id = "healer"

    damage_by_action, damage_cb, heal_cb = _capture_damage_and_healing()
    try:
        set_battle_active(True)
        await player.apply_damage(50, attacker=None)
        await player.apply_healing(
            25,
            healer=player,
            source_type="heal",
            source_name="Test Heal",
        )
        await asyncio.sleep(0.05)
    finally:
        set_battle_active(False)
        BUS.unsubscribe("damage_dealt", damage_cb)
        BUS.unsubscribe("heal", heal_cb)

    healer_key = _entity_key(player)
    assert healer_key in damage_by_action

    player_actions = damage_by_action[healer_key]
    assert "Test Heal Healing" in player_actions
    assert player_actions["Test Heal Healing"] == 25


@pytest.mark.asyncio
async def test_damage_action_names_preserved():
    """Test that different action names are preserved separately."""
    attacker = Carly()
    attacker.id = "test_attacker"
    target = Stats(hp=1000)
    target.id = "test_target"

    damage_by_action, damage_cb, heal_cb = _capture_damage_and_healing()
    try:
        set_battle_active(True)
        await target.apply_damage(100, attacker=attacker, action_name="Normal Attack")
        await target.apply_damage(75, attacker=attacker, action_name="Ice Ultimate")
        await target.apply_damage(50, attacker=attacker, action_name="Wind Spread")
        await asyncio.sleep(0.05)
    finally:
        set_battle_active(False)
        BUS.unsubscribe("damage_dealt", damage_cb)
        BUS.unsubscribe("heal", heal_cb)

    attacker_key = _entity_key(attacker)
    assert attacker_key in damage_by_action

    attacker_actions = damage_by_action[attacker_key]
    assert attacker_actions["Normal Attack"] > 0
    assert attacker_actions["Ice Ultimate"] > 0
    assert attacker_actions["Wind Spread"] > 0
