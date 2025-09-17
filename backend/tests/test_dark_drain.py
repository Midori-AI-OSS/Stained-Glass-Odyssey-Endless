import pytest

from autofighter.stats import BUS
from autofighter.stats import Stats
from autofighter.stats import set_battle_active
from plugins.damage_types.dark import Dark


@pytest.mark.asyncio
async def test_dark_drain_reduces_hp_and_sets_bonus():
    dark = Dark()
    actor = Stats(damage_type=dark)
    ally = Stats()
    actor.id = "actor"
    ally.id = "ally"

    set_battle_active(True)
    try:
        await dark.on_action(actor, [actor, ally], [])
    finally:
        set_battle_active(False)

    assert actor.hp == 900
    assert ally.hp == 900
    bonus = getattr(actor, "_pending_dark_bonus", 1.0)
    assert bonus > 1.0
    cleanup = getattr(actor, "_pending_dark_cleanup", [])
    assert len(cleanup) == 3


@pytest.mark.asyncio
async def test_dark_drain_skips_without_active_battle():
    dark = Dark()
    actor = Stats(damage_type=dark)
    ally = Stats()

    actor.hp = 500
    ally.hp = 500

    await dark.on_action(actor, [actor, ally], [])

    assert actor.hp == 500
    assert ally.hp == 500
    assert not hasattr(actor, "_pending_dark_bonus")
    assert not hasattr(actor, "_pending_dark_cleanup")


@pytest.mark.asyncio
async def test_dark_drain_bonus_clears_after_action_event():
    dark = Dark()
    actor = Stats(damage_type=dark)
    ally = Stats()

    set_battle_active(True)
    try:
        await dark.on_action(actor, [actor, ally], [])
        assert hasattr(actor, "_pending_dark_bonus")
        await BUS.emit_async("action_used", actor)
    finally:
        set_battle_active(False)

    assert not hasattr(actor, "_pending_dark_bonus")
    assert not hasattr(actor, "_pending_dark_cleanup")
