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


def test_coated_armor_heals_after_mitigation():
    loop = setup_event_loop()
    BUS.set_loop(loop)
    set_battle_active(True)

    party = Party()
    defender = PlayerBase()
    attacker = PlayerBase()

    defender.set_base_stat('max_hp', 1000)
    defender.hp = defender.max_hp
    defender.set_base_stat('defense', 5)
    defender.set_base_stat('atk', 50)
    defender.dodge_odds = 0.0
    defender.damage_type = Generic()

    attacker.set_base_stat('max_hp', 1000)
    attacker.hp = attacker.max_hp
    attacker.set_base_stat('defense', 1)
    attacker.set_base_stat('mitigation', 1)
    attacker.dodge_odds = 0.0
    attacker.crit_rate = 0.0
    attacker.crit_damage = 1.0
    attacker.damage_type = Generic()

    party.members.append(defender)
    award_card(party, "coated_armor")
    loop.run_until_complete(apply_cards(party))

    heal_amount = int(defender.max_hp * 0.01)
    initial_hp = defender.hp

    try:
        damage_taken = loop.run_until_complete(
            defender.apply_damage(500, attacker=attacker)
        )
        assert damage_taken > heal_amount

        loop.run_until_complete(asyncio.sleep(0))

        expected_hp = min(defender.max_hp, initial_hp - damage_taken + heal_amount)
        assert defender.hp == expected_hp
    finally:
        loop.run_until_complete(BUS.emit_async("battle_end", defender))
        flush_bus_tasks(loop)
        loop.run_until_complete(asyncio.sleep(0.05))
        set_battle_active(False)
        BUS.set_loop(None)
        loop.close()
