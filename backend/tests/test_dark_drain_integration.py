import asyncio

import pytest

from autofighter.stats import BUS
from autofighter.stats import Stats
from autofighter.stats import set_battle_active
from plugins.damage_types.dark import Dark


@pytest.mark.asyncio
async def test_dark_drain_async_context_sets_independent_bonuses():
    dark = Dark()
    attackers: list[Stats] = []
    parties: list[list[Stats]] = []

    for i in range(3):
        actor = Stats(damage_type=dark)
        actor.id = f"attacker_{i}"
        ally = Stats()
        ally.id = f"ally_{i}"
        attackers.append(actor)
        parties.append([actor, ally])

    set_battle_active(True)
    try:
        await asyncio.gather(
            *(dark.on_action(actor, party, []) for actor, party in zip(attackers, parties))
        )
    finally:
        set_battle_active(False)

    for actor, party in zip(attackers, parties):
        bonus = getattr(actor, "_pending_dark_bonus", 1.0)
        assert bonus > 1.0
        cleanup = getattr(actor, "_pending_dark_cleanup", [])
        assert len(cleanup) == 3
        for member in party:
            assert member.hp < 1000
        await BUS.emit_async("action_used", actor)
        assert not hasattr(actor, "_pending_dark_bonus")
        assert not hasattr(actor, "_pending_dark_cleanup")


@pytest.mark.asyncio
async def test_dark_drain_returns_true_even_without_enemies():
    dark = Dark()
    actor = Stats(damage_type=dark)
    ally = Stats()

    set_battle_active(True)
    try:
        result = await dark.on_action(actor, [actor, ally], [])
    finally:
        set_battle_active(False)

    assert result is True
