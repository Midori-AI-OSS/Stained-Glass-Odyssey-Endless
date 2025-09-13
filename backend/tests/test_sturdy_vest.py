import asyncio
import sys
import types

from autofighter.cards import apply_cards
from autofighter.cards import award_card
from autofighter.party import Party
from autofighter.stats import BUS
from plugins.players._base import PlayerBase


def setup_event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop


def test_sturdy_vest_grants_two_turn_hot():
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    party = Party()
    member = PlayerBase()
    member.id = "member"
    member.set_base_stat("max_hp", 100)
    member.hp = 100
    party.members.append(member)
    award_card(party, "sturdy_vest")
    loop.run_until_complete(apply_cards(party))

    member.hp = 30
    loop.run_until_complete(BUS.emit_async("damage_taken", member, None, 0))

    loop.run_until_complete(BUS.emit_async("turn_start"))
    loop.run_until_complete(asyncio.sleep(0))
    assert member.hp == 33

    loop.run_until_complete(BUS.emit_async("turn_start"))
    loop.run_until_complete(asyncio.sleep(0))
    assert member.hp == 36

    loop.run_until_complete(BUS.emit_async("turn_start"))
    loop.run_until_complete(asyncio.sleep(0))
    assert member.hp == 39

