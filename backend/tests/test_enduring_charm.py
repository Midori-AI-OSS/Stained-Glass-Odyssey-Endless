from __future__ import annotations

import asyncio

from autofighter.cards import apply_cards
from autofighter.cards import award_card
from autofighter.party import Party
from autofighter.stats import BUS
from autofighter.stats import set_battle_active
from plugins.characters._base import PlayerBase
from plugins.damage_types.generic import Generic
from plugins.event_bus import bus as _bus


def setup_event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop


def flush_bus_tasks(loop):
    batch_task = getattr(_bus, "_batch_timer", None)
    if isinstance(batch_task, asyncio.Task):
        loop.run_until_complete(batch_task)


def _active_enduring_charm_ids(player: PlayerBase) -> set[str]:
    effect_manager = getattr(player, "effect_manager", None)
    if effect_manager is None:
        return set()
    return {modifier.id for modifier in effect_manager.mods}


def test_enduring_charm_reapplies_after_expiration():
    loop = setup_event_loop()
    BUS.set_loop(loop)
    set_battle_active(True)

    party = Party()
    defender = PlayerBase()
    defender.id = "defender"
    defender.damage_type = Generic()
    defender.set_base_stat("max_hp", 1000)
    defender.set_base_stat("vitality", 1.0)
    defender.hp = defender.max_hp

    party.members.append(defender)
    award_card(party, "enduring_charm")
    loop.run_until_complete(apply_cards(party))

    expected_effect_id = f"enduring_charm_low_hp_vit_{id(defender)}"

    try:
        damage = int(defender.max_hp * 0.8)
        loop.run_until_complete(defender.apply_cost_damage(damage))
        flush_bus_tasks(loop)
        loop.run_until_complete(asyncio.sleep(0))

        active_mods = _active_enduring_charm_ids(defender)
        assert expected_effect_id in active_mods

        defender.hp = defender.max_hp

        effect_manager = defender.effect_manager
        assert effect_manager is not None
        loop.run_until_complete(effect_manager.tick())
        loop.run_until_complete(effect_manager.tick())
        flush_bus_tasks(loop)
        loop.run_until_complete(asyncio.sleep(0))

        active_mods = _active_enduring_charm_ids(defender)
        assert expected_effect_id not in active_mods

        loop.run_until_complete(defender.apply_cost_damage(damage))
        flush_bus_tasks(loop)
        loop.run_until_complete(asyncio.sleep(0))

        active_mods = _active_enduring_charm_ids(defender)
        assert expected_effect_id in active_mods
    finally:
        loop.run_until_complete(BUS.emit_async("battle_end", defender))
        flush_bus_tasks(loop)
        loop.run_until_complete(asyncio.sleep(0.05))
        set_battle_active(False)
        BUS.set_loop(None)
        loop.close()


def test_enduring_charm_reapplies_after_battle_end():
    loop = setup_event_loop()
    BUS.set_loop(loop)
    set_battle_active(True)

    party = Party()
    defender = PlayerBase()
    defender.id = "defender"
    defender.damage_type = Generic()
    defender.set_base_stat("max_hp", 1000)
    defender.set_base_stat("vitality", 1.0)
    defender.hp = defender.max_hp

    party.members.append(defender)
    award_card(party, "enduring_charm")
    loop.run_until_complete(apply_cards(party))

    expected_effect_id = f"enduring_charm_low_hp_vit_{id(defender)}"

    try:
        damage = int(defender.max_hp * 0.8)
        loop.run_until_complete(defender.apply_cost_damage(damage))
        flush_bus_tasks(loop)
        loop.run_until_complete(asyncio.sleep(0))

        active_mods = _active_enduring_charm_ids(defender)
        assert expected_effect_id in active_mods

        loop.run_until_complete(BUS.emit_async("battle_end", defender))
        flush_bus_tasks(loop)
        loop.run_until_complete(asyncio.sleep(0))
        set_battle_active(False)

        defender.hp = defender.max_hp

        set_battle_active(True)
        loop.run_until_complete(apply_cards(party))
        loop.run_until_complete(defender.apply_cost_damage(damage))
        flush_bus_tasks(loop)
        loop.run_until_complete(asyncio.sleep(0))

        active_mods = _active_enduring_charm_ids(defender)
        assert expected_effect_id in active_mods
    finally:
        loop.run_until_complete(BUS.emit_async("battle_end", defender))
        flush_bus_tasks(loop)
        loop.run_until_complete(asyncio.sleep(0.05))
        set_battle_active(False)
        BUS.set_loop(None)
        loop.close()
