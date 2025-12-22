import asyncio

from autofighter.cards import apply_cards, award_card
from autofighter.party import Party
from autofighter.stats import Stats
from plugins import event_bus as event_bus_module


def setup_event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop


def test_honed_point_bonus_damage_once():
    event_bus_module.bus._subs.clear()
    loop = setup_event_loop()
    party = Party()
    attacker = Stats()
    target = Stats()

    attacker._base_atk = 100
    target._base_defense = 0
    target.set_base_stat('mitigation', 1)
    target._base_vitality = 1

    party.members.append(attacker)
    award_card(party, "honed_point")
    loop.run_until_complete(apply_cards(party))

    initial_hp = target.hp
    dmg = loop.run_until_complete(
        target.apply_damage(attacker.atk, attacker=attacker, action_name="attack")
    )
    loop.run_until_complete(asyncio.sleep(0))

    expected_first = dmg + int(dmg * 0.10)
    assert target.hp == initial_hp - expected_first

    hp_after_first = target.hp
    dmg2 = loop.run_until_complete(
        target.apply_damage(attacker.atk, attacker=attacker, action_name="attack")
    )
    loop.run_until_complete(asyncio.sleep(0))

    assert target.hp == hp_after_first - dmg2

