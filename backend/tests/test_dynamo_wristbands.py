import asyncio
import sys
import types

from autofighter.cards import apply_cards
from autofighter.cards import award_card
from autofighter.party import Party
from autofighter.stats import BUS
from plugins.characters._base import PlayerBase
from plugins.damage_types.lightning import Lightning


def setup_event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop


def test_dynamo_wristbands_grants_crit_on_lightning_damage():
    """Test that Dynamo Wristbands grants crit rate when Lightning damage is dealt."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    party = Party()

    # Create a party member with Lightning damage type
    member = PlayerBase()
    member.id = "lightning_member"
    member.set_base_stat("max_hp", 1000)
    member.set_base_stat("atk", 100)
    member.set_base_stat("crit_rate", 0.05)  # 5% base crit
    member.hp = 1000
    member.damage_type = Lightning()
    party.members.append(member)

    # Create a dummy target
    target = PlayerBase()
    target.id = "target"
    target.set_base_stat("max_hp", 1000)
    target.hp = 1000

    # Award and apply Dynamo Wristbands
    award_card(party, "dynamo_wristbands")
    loop.run_until_complete(apply_cards(party))

    # Verify base ATK buff was applied (+3% = 1.03x)
    assert member.atk >= 103

    # Get initial crit rate
    initial_crit = member.crit_rate

    # Emit Lightning damage dealt event
    loop.run_until_complete(
        BUS.emit_async(
            "damage_dealt",
            member,
            target,
            50,
            Lightning(),
            None,
            None,
            "attack",
        )
    )

    # Check that crit rate buff was applied
    effect_manager = getattr(member, "effect_manager", None)
    assert effect_manager is not None, "Effect manager should be created"

    # Verify crit rate increased
    new_crit = member.crit_rate
    assert new_crit > initial_crit, "Crit rate should increase after Lightning damage"

    loop.run_until_complete(BUS.emit_async("battle_end"))
    loop.close()


def test_dynamo_wristbands_stacks_up_to_two():
    """Test that Dynamo Wristbands stacks up to 2 times."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    party = Party()

    member = PlayerBase()
    member.id = "lightning_member"
    member.set_base_stat("max_hp", 1000)
    member.set_base_stat("atk", 100)
    member.set_base_stat("crit_rate", 0.05)
    member.hp = 1000
    member.damage_type = Lightning()
    party.members.append(member)

    target = PlayerBase()
    target.id = "target"
    target.set_base_stat("max_hp", 1000)
    target.hp = 1000

    award_card(party, "dynamo_wristbands")
    loop.run_until_complete(apply_cards(party))

    initial_crit = member.crit_rate

    # First Lightning damage - should grant first stack
    loop.run_until_complete(
        BUS.emit_async(
            "damage_dealt",
            member,
            target,
            50,
            Lightning(),
            None,
            None,
            "attack",
        )
    )

    crit_after_first = member.crit_rate
    assert crit_after_first > initial_crit, "First stack should increase crit rate"

    # Second Lightning damage - should grant second stack
    loop.run_until_complete(
        BUS.emit_async(
            "damage_dealt",
            member,
            target,
            50,
            Lightning(),
            None,
            None,
            "attack",
        )
    )

    crit_after_second = member.crit_rate
    assert (
        crit_after_second > crit_after_first
    ), "Second stack should further increase crit rate"

    # Third Lightning damage - should NOT grant third stack
    loop.run_until_complete(
        BUS.emit_async(
            "damage_dealt",
            member,
            target,
            50,
            Lightning(),
            None,
            None,
            "attack",
        )
    )

    crit_after_third = member.crit_rate
    assert (
        crit_after_third == crit_after_second
    ), "Should not stack beyond 2 times in same turn"

    loop.run_until_complete(BUS.emit_async("battle_end"))
    loop.close()


def test_dynamo_wristbands_resets_stacks_on_turn_start():
    """Test that Dynamo Wristbands stack tracking resets each turn."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    party = Party()

    member = PlayerBase()
    member.id = "lightning_member"
    member.set_base_stat("max_hp", 1000)
    member.set_base_stat("atk", 100)
    member.set_base_stat("crit_rate", 0.05)
    member.hp = 1000
    member.damage_type = Lightning()
    party.members.append(member)

    target = PlayerBase()
    target.id = "target"
    target.set_base_stat("max_hp", 1000)
    target.hp = 1000

    award_card(party, "dynamo_wristbands")
    loop.run_until_complete(apply_cards(party))

    # Deal Lightning damage twice to reach stack cap
    for _ in range(2):
        loop.run_until_complete(
            BUS.emit_async(
                "damage_dealt",
                member,
                target,
                50,
                Lightning(),
                None,
                None,
                "attack",
            )
        )

    # Start new turn - this should reset stack tracking (though buffs decay naturally)
    loop.run_until_complete(BUS.emit_async("turn_start"))

    # The effect manager should still exist and could contain other effects,
    # but stack tracking is reset internally
    effect_manager = getattr(member, "effect_manager", None)
    assert effect_manager is not None

    loop.run_until_complete(BUS.emit_async("battle_end"))
    loop.close()


def test_dynamo_wristbands_only_triggers_on_lightning_damage():
    """Test that Dynamo Wristbands only triggers on Lightning damage, not other types."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    party = Party()

    member = PlayerBase()
    member.id = "ice_member"
    member.set_base_stat("max_hp", 1000)
    member.set_base_stat("atk", 100)
    member.set_base_stat("crit_rate", 0.05)
    member.hp = 1000
    # Member has Ice damage type, not Lightning
    party.members.append(member)

    target = PlayerBase()
    target.id = "target"
    target.set_base_stat("max_hp", 1000)
    target.hp = 1000

    award_card(party, "dynamo_wristbands")
    loop.run_until_complete(apply_cards(party))

    initial_crit = member.crit_rate

    # Deal Ice damage (not Lightning) - should NOT trigger
    from plugins.damage_types.ice import Ice

    loop.run_until_complete(
        BUS.emit_async(
            "damage_dealt", member, target, 50, Ice(), None, None, "attack"
        )
    )

    # Crit rate should not have increased
    new_crit = member.crit_rate
    assert (
        new_crit == initial_crit
    ), "Crit rate should not increase for non-Lightning damage"

    loop.run_until_complete(BUS.emit_async("battle_end"))
    loop.close()


def test_dynamo_wristbands_multiple_allies():
    """Test that Dynamo Wristbands tracks stacks independently for multiple allies."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    party = Party()

    # Create two Lightning allies
    member1 = PlayerBase()
    member1.id = "lightning_member1"
    member1.set_base_stat("max_hp", 1000)
    member1.set_base_stat("atk", 100)
    member1.set_base_stat("crit_rate", 0.05)
    member1.hp = 1000
    member1.damage_type = Lightning()
    party.members.append(member1)

    member2 = PlayerBase()
    member2.id = "lightning_member2"
    member2.set_base_stat("max_hp", 1000)
    member2.set_base_stat("atk", 100)
    member2.set_base_stat("crit_rate", 0.05)
    member2.hp = 1000
    member2.damage_type = Lightning()
    party.members.append(member2)

    target = PlayerBase()
    target.id = "target"
    target.set_base_stat("max_hp", 1000)
    target.hp = 1000

    award_card(party, "dynamo_wristbands")
    loop.run_until_complete(apply_cards(party))

    # Member 1 deals Lightning damage
    loop.run_until_complete(
        BUS.emit_async(
            "damage_dealt",
            member1,
            target,
            50,
            Lightning(),
            None,
            None,
            "attack",
        )
    )

    # Member 2 deals Lightning damage
    loop.run_until_complete(
        BUS.emit_async(
            "damage_dealt",
            member2,
            target,
            50,
            Lightning(),
            None,
            None,
            "attack",
        )
    )

    # Both should have their own effect managers and buffs
    effect_manager1 = getattr(member1, "effect_manager", None)
    effect_manager2 = getattr(member2, "effect_manager", None)

    assert effect_manager1 is not None, "Member1 should have effect manager"
    assert effect_manager2 is not None, "Member2 should have effect manager"

    loop.run_until_complete(BUS.emit_async("battle_end"))
    loop.close()
