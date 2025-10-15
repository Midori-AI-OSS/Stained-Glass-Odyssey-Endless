import asyncio
import sys
import types

from autofighter.party import Party
from autofighter.relics import apply_relics
from autofighter.relics import award_relic
from autofighter.stats import BUS
from plugins.characters._base import PlayerBase


def setup_event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop


def test_field_rations_heals_after_battle():
    """Test that Field Rations heals party members after battle."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    party = Party()

    member = PlayerBase()
    member.id = "test_member"
    member.set_base_stat("max_hp", 1000)
    member.hp = 500  # Start with damaged HP
    party.members.append(member)

    # Award and apply Field Rations
    award_relic(party, "field_rations")
    loop.run_until_complete(apply_relics(party))

    # Trigger battle end
    loop.run_until_complete(BUS.emit_async("battle_end"))

    # Verify healing occurred (2% of 1000 = 20 HP)
    expected_hp = 500 + 20
    assert member.hp == expected_hp, f"Expected HP {expected_hp}, got {member.hp}"

    loop.close()


def test_field_rations_grants_ultimate_charge():
    """Test that Field Rations grants ultimate charge after battle."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    party = Party()

    member = PlayerBase()
    member.id = "test_member"
    member.set_base_stat("max_hp", 1000)
    member.hp = 1000
    member.ultimate_charge = 0
    member.ultimate_charge_capacity = 15
    party.members.append(member)

    # Award and apply Field Rations
    award_relic(party, "field_rations")
    loop.run_until_complete(apply_relics(party))

    # Trigger battle end
    loop.run_until_complete(BUS.emit_async("battle_end"))

    # Verify ultimate charge was granted (+1 per stack = +1)
    assert member.ultimate_charge == 1, f"Expected charge 1, got {member.ultimate_charge}"

    loop.close()


def test_field_rations_respects_ultimate_charge_cap():
    """Test that Field Rations respects ultimate charge capacity."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    party = Party()

    member = PlayerBase()
    member.id = "test_member"
    member.set_base_stat("max_hp", 1000)
    member.hp = 1000
    member.ultimate_charge = 14  # Near cap
    member.ultimate_charge_capacity = 15
    party.members.append(member)

    # Award and apply Field Rations
    award_relic(party, "field_rations")
    loop.run_until_complete(apply_relics(party))

    # Trigger battle end
    loop.run_until_complete(BUS.emit_async("battle_end"))

    # Verify ultimate charge is capped at capacity
    assert (
        member.ultimate_charge == 15
    ), f"Expected charge 15 (capped), got {member.ultimate_charge}"

    loop.close()


def test_field_rations_sets_ultimate_ready_flag():
    """Test that Field Rations properly sets ultimate_ready flag when reaching capacity."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    party = Party()

    member = PlayerBase()
    member.id = "test_member"
    member.set_base_stat("max_hp", 1000)
    member.hp = 1000
    member.ultimate_charge = 14  # One point away from full
    member.ultimate_charge_capacity = 15
    member.ultimate_ready = False  # Not ready initially
    party.members.append(member)

    # Award and apply Field Rations
    award_relic(party, "field_rations")
    loop.run_until_complete(apply_relics(party))

    # Trigger battle end - should grant +1 charge, reaching capacity
    loop.run_until_complete(BUS.emit_async("battle_end"))

    # Verify ultimate charge reached capacity
    assert (
        member.ultimate_charge == 15
    ), f"Expected charge 15, got {member.ultimate_charge}"

    # Verify ultimate_ready flag is set
    assert (
        member.ultimate_ready is True
    ), "ultimate_ready should be True when charge reaches capacity"

    loop.close()


def test_field_rations_multiple_stacks():
    """Test that Field Rations stacks additively for healing and charge."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    party = Party()

    member = PlayerBase()
    member.id = "test_member"
    member.set_base_stat("max_hp", 1000)
    member.hp = 500
    member.ultimate_charge = 0
    member.ultimate_charge_capacity = 15
    party.members.append(member)

    # Award 3 stacks
    award_relic(party, "field_rations")
    award_relic(party, "field_rations")
    award_relic(party, "field_rations")
    loop.run_until_complete(apply_relics(party))

    # Trigger battle end
    loop.run_until_complete(BUS.emit_async("battle_end"))

    # Verify healing: 2% * 3 stacks = 6% of 1000 = 60 HP
    expected_hp = 500 + 60
    assert member.hp == expected_hp, f"Expected HP {expected_hp}, got {member.hp}"

    # Verify charge: +1 * 3 stacks = +3
    assert (
        member.ultimate_charge == 3
    ), f"Expected charge 3, got {member.ultimate_charge}"

    loop.close()


def test_field_rations_affects_all_party_members():
    """Test that Field Rations heals and charges all party members."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    party = Party()

    member1 = PlayerBase()
    member1.id = "member1"
    member1.set_base_stat("max_hp", 1000)
    member1.hp = 500
    member1.ultimate_charge = 0
    member1.ultimate_charge_capacity = 15
    party.members.append(member1)

    member2 = PlayerBase()
    member2.id = "member2"
    member2.set_base_stat("max_hp", 2000)
    member2.hp = 1000
    member2.ultimate_charge = 5
    member2.ultimate_charge_capacity = 15
    party.members.append(member2)

    # Award and apply Field Rations
    award_relic(party, "field_rations")
    loop.run_until_complete(apply_relics(party))

    # Trigger battle end
    loop.run_until_complete(BUS.emit_async("battle_end"))

    # Verify member1: 2% of 1000 = 20 HP
    assert member1.hp == 520, f"Expected member1 HP 520, got {member1.hp}"
    assert (
        member1.ultimate_charge == 1
    ), f"Expected member1 charge 1, got {member1.ultimate_charge}"

    # Verify member2: 2% of 2000 = 40 HP
    assert member2.hp == 1040, f"Expected member2 HP 1040, got {member2.hp}"
    assert (
        member2.ultimate_charge == 6
    ), f"Expected member2 charge 6, got {member2.ultimate_charge}"

    loop.close()


def test_field_rations_skips_dead_members():
    """Test that Field Rations does not heal or charge dead members."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    party = Party()

    alive_member = PlayerBase()
    alive_member.id = "alive"
    alive_member.set_base_stat("max_hp", 1000)
    alive_member.hp = 500
    alive_member.ultimate_charge = 0
    alive_member.ultimate_charge_capacity = 15
    party.members.append(alive_member)

    dead_member = PlayerBase()
    dead_member.id = "dead"
    dead_member.set_base_stat("max_hp", 1000)
    dead_member.hp = 0  # Dead
    dead_member.ultimate_charge = 0
    dead_member.ultimate_charge_capacity = 15
    party.members.append(dead_member)

    # Award and apply Field Rations
    award_relic(party, "field_rations")
    loop.run_until_complete(apply_relics(party))

    # Trigger battle end
    loop.run_until_complete(BUS.emit_async("battle_end"))

    # Verify alive member was healed and charged
    assert alive_member.hp == 520, f"Expected alive HP 520, got {alive_member.hp}"
    assert (
        alive_member.ultimate_charge == 1
    ), f"Expected alive charge 1, got {alive_member.ultimate_charge}"

    # Verify dead member was not affected
    assert dead_member.hp == 0, f"Expected dead HP 0, got {dead_member.hp}"
    assert (
        dead_member.ultimate_charge == 0
    ), f"Expected dead charge 0, got {dead_member.ultimate_charge}"

    loop.close()


def test_field_rations_triggers_multiple_battles():
    """Test that Field Rations triggers after each battle."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    party = Party()

    member = PlayerBase()
    member.id = "test_member"
    member.set_base_stat("max_hp", 1000)
    member.hp = 500
    member.ultimate_charge = 0
    member.ultimate_charge_capacity = 15
    party.members.append(member)

    # Award and apply Field Rations
    award_relic(party, "field_rations")
    loop.run_until_complete(apply_relics(party))

    # First battle end
    loop.run_until_complete(BUS.emit_async("battle_end"))
    assert member.hp == 520, "First battle should heal"
    assert member.ultimate_charge == 1, "First battle should grant charge"

    # Second battle - apply relics again
    loop.run_until_complete(apply_relics(party))
    loop.run_until_complete(BUS.emit_async("battle_end"))
    assert member.hp == 540, "Second battle should heal again"
    assert member.ultimate_charge == 2, "Second battle should grant charge again"

    loop.close()
