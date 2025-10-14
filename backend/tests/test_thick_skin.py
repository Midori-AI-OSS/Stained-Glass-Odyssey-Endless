import asyncio
from unittest.mock import patch

from autofighter.cards import apply_cards
from autofighter.cards import award_card
from autofighter.party import Party
from autofighter.stats import BUS
from autofighter.stats import set_battle_active
from plugins.characters._base import PlayerBase
from plugins.damage_types.generic import Generic
from plugins.dots.bleed import Bleed
from plugins.event_bus import bus as _bus


def setup_event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop


def flush_bus_tasks(loop):
    batch_task = getattr(_bus, "_batch_timer", None)
    if isinstance(batch_task, asyncio.Task):
        loop.run_until_complete(batch_task)


def test_thick_skin_reduces_bleed_duration_on_trigger():
    loop = setup_event_loop()
    BUS.set_loop(loop)
    set_battle_active(True)

    party = Party()
    defender = PlayerBase()
    defender.id = "defender"
    defender.damage_type = Generic()
    defender.set_base_stat("max_hp", 1000)
    defender.hp = defender.max_hp

    party.members.append(defender)
    award_card(party, "thick_skin")
    loop.run_until_complete(apply_cards(party))

    effect_manager = defender.effect_manager
    assert effect_manager is not None

    bleed = Bleed(damage=10, turns=3)
    bleed.source = defender

    try:
        with patch("plugins.cards.thick_skin.random.random", return_value=0.25):
            loop.run_until_complete(effect_manager.add_dot(bleed))
            flush_bus_tasks(loop)
            loop.run_until_complete(asyncio.sleep(0))

        assert bleed.turns == 2

        new_bleed = Bleed(damage=10, turns=4)
        new_bleed.source = defender

        with patch("plugins.cards.thick_skin.random.random", return_value=0.75):
            loop.run_until_complete(effect_manager.add_dot(new_bleed))
            flush_bus_tasks(loop)
            loop.run_until_complete(asyncio.sleep(0))

        assert new_bleed.turns == 4
    finally:
        loop.run_until_complete(BUS.emit_async("battle_end", defender))
        flush_bus_tasks(loop)
        loop.run_until_complete(asyncio.sleep(0.05))
        set_battle_active(False)
        BUS.set_loop(None)
        loop.close()
