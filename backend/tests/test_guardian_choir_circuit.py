import asyncio
import math
import sys
import types

from autofighter.cards import apply_cards, award_card
from autofighter.party import Party
from autofighter.stats import BUS
from plugins.characters._base import PlayerBase


def _setup_event_loop() -> asyncio.AbstractEventLoop:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop


def _build_member(member_id: str, max_hp: int, hp: int) -> PlayerBase:
    member = PlayerBase()
    member.id = member_id
    member.set_base_stat("max_hp", max_hp)
    member.set_base_stat("defense", 100)
    member.set_base_stat("mitigation", 1.0)
    member.set_base_stat("regain", 1.0)
    member.hp = hp
    return member


def test_guardian_choir_redirects_lowest_and_throttles_multi_target() -> None:
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = _setup_event_loop()
    party = Party()

    healer = _build_member("healer", 1200, 1200)
    ally_low = _build_member("ally_low", 1000, 350)
    ally_high = _build_member("ally_high", 1000, 900)

    party.members.extend([healer, ally_low, ally_high])

    award_card(party, "guardian_choir_circuit")
    loop.run_until_complete(apply_cards(party))

    loop.run_until_complete(BUS.emit_async("turn_start", healer))

    assert getattr(ally_low, "shields", 0) == 0

    loop.run_until_complete(ally_high.apply_healing(200, healer=healer))
    loop.run_until_complete(asyncio.sleep(0.05))

    expected_shield = math.ceil(200 * 0.15)
    assert ally_low.shields == expected_shield

    effect_manager = getattr(ally_low, "effect_manager", None)
    assert effect_manager is not None
    assert any(
        mod.id == "guardian_choir_circuit_mitigation" for mod in getattr(effect_manager, "mods", [])
    )

    loop.run_until_complete(ally_low.apply_healing(150, healer=healer))
    loop.run_until_complete(asyncio.sleep(0.05))
    assert ally_low.shields == expected_shield

    loop.run_until_complete(BUS.emit_async("battle_end"))
    loop.close()


def test_guardian_choir_overheal_uses_diminishing_returns_for_shields() -> None:
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = _setup_event_loop()
    party = Party()

    healer = _build_member("healer", 1100, 1100)
    ally_low = _build_member("ally_low", 1000, 400)
    ally_high = _build_member("ally_high", 1000, 950)

    party.members.extend([healer, ally_low, ally_high])

    award_card(party, "guardian_choir_circuit")
    loop.run_until_complete(apply_cards(party))

    ally_low.enable_overheal()
    ally_low.shields = 40

    loop.run_until_complete(BUS.emit_async("turn_start", healer))
    loop.run_until_complete(ally_high.apply_healing(200, healer=healer))
    loop.run_until_complete(asyncio.sleep(0.05))

    added = max(1, int(math.ceil(200 * 0.15) * 0.2))
    assert ally_low.shields == 40 + added

    loop.run_until_complete(BUS.emit_async("battle_end"))
    loop.close()


def test_guardian_choir_shield_and_mitigation_reset_on_recipient_turn() -> None:
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = _setup_event_loop()
    party = Party()

    healer = _build_member("healer", 1200, 1200)
    ally_low = _build_member("ally_low", 900, 300)
    ally_high = _build_member("ally_high", 1000, 950)

    party.members.extend([healer, ally_low, ally_high])

    award_card(party, "guardian_choir_circuit")
    loop.run_until_complete(apply_cards(party))

    loop.run_until_complete(BUS.emit_async("turn_start", healer))
    loop.run_until_complete(ally_high.apply_healing(180, healer=healer))
    loop.run_until_complete(asyncio.sleep(0.05))

    assert ally_low.shields == math.ceil(180 * 0.15)

    loop.run_until_complete(BUS.emit_async("turn_start", ally_low))
    loop.run_until_complete(asyncio.sleep(0.05))

    assert ally_low.shields == 0
    effect_manager = getattr(ally_low, "effect_manager", None)
    if effect_manager is not None:
        assert all(
            mod.id != "guardian_choir_circuit_mitigation" for mod in getattr(effect_manager, "mods", [])
        )

    loop.run_until_complete(BUS.emit_async("turn_start", healer))
    loop.run_until_complete(ally_high.apply_healing(100, healer=healer))
    loop.run_until_complete(asyncio.sleep(0.05))
    assert ally_low.shields == math.ceil(100 * 0.15)

    loop.run_until_complete(BUS.emit_async("battle_end"))
    loop.close()
