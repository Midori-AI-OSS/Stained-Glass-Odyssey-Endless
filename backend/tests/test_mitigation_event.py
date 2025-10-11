import asyncio

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
    if isinstance(batch_task, asyncio.Task) and batch_task.get_loop() is loop:
        loop.run_until_complete(batch_task)


def test_mitigation_event_not_triggered_by_shield_absorption():
    loop = setup_event_loop()
    BUS.set_loop(loop)
    set_battle_active(True)

    defender = PlayerBase()
    attacker = PlayerBase()

    defender.set_base_stat('max_hp', 500)
    defender.hp = defender.max_hp
    defender.set_base_stat('defense', 400)
    defender.shields = 100
    defender.dodge_odds = 0.0
    defender.damage_type = Generic()

    attacker.set_base_stat('max_hp', 500)
    attacker.hp = attacker.max_hp
    attacker.set_base_stat('defense', 1)
    attacker.set_base_stat('mitigation', 1)
    attacker.dodge_odds = 0.0
    attacker.crit_rate = 0.0
    attacker.crit_damage = 1.0
    attacker.damage_type = Generic()

    events: list[tuple] = []

    async def capture(*args):
        events.append(args)

    BUS.subscribe("mitigation_triggered", capture)

    try:
        loop.run_until_complete(defender.apply_damage(500, attacker=attacker))
        loop.run_until_complete(asyncio.sleep(0))
        assert events == []
    finally:
        flush_bus_tasks(loop)
        loop.run_until_complete(asyncio.sleep(0.05))
        BUS.unsubscribe("mitigation_triggered", capture)
        set_battle_active(False)
        BUS.set_loop(None)
        loop.close()


def test_mitigation_event_not_triggered_by_zero_damage():
    loop = setup_event_loop()
    BUS.set_loop(loop)
    set_battle_active(True)

    defender = PlayerBase()
    attacker = PlayerBase()

    defender.set_base_stat('max_hp', 500)
    defender.hp = defender.max_hp
    defender.set_base_stat('defense', 400)
    defender.dodge_odds = 0.0
    defender.damage_type = Generic()

    attacker.set_base_stat('max_hp', 500)
    attacker.hp = attacker.max_hp
    attacker.set_base_stat('defense', 1)
    attacker.set_base_stat('mitigation', 1)
    attacker.dodge_odds = 0.0
    attacker.crit_rate = 0.0
    attacker.crit_damage = 1.0
    attacker.damage_type = Generic()

    events: list[tuple] = []

    async def capture(*args):
        events.append(args)

    BUS.subscribe("mitigation_triggered", capture)

    try:
        loop.run_until_complete(defender.apply_damage(0, attacker=attacker))
        loop.run_until_complete(asyncio.sleep(0))
        assert events == []
    finally:
        flush_bus_tasks(loop)
        loop.run_until_complete(asyncio.sleep(0.05))
        BUS.unsubscribe("mitigation_triggered", capture)
        set_battle_active(False)
        BUS.set_loop(None)
        loop.close()
