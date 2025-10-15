import asyncio
import sys
import types

from autofighter.cards import apply_cards
from autofighter.cards import award_card
from autofighter.party import Party
from autofighter.stats import BUS
from plugins.characters._base import PlayerBase


def setup_event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop


def test_oracle_prayer_charm_activates_radiant_regeneration_on_low_hp():
    """Test that Oracle Prayer Charm grants Radiant Regeneration HoT when HP drops below 45%."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    party = Party()

    # Create a party member with sufficient stats for Radiant Regeneration to work
    member = PlayerBase()
    member.id = "test_member"
    member.set_base_stat("max_hp", 1000)
    member.set_base_stat("atk", 50)
    member.set_base_stat("vitality", 1.0)
    member.hp = 1000
    party.members.append(member)

    # Award and apply Oracle Prayer Charm
    award_card(party, "oracle_prayer_charm")
    loop.run_until_complete(apply_cards(party))

    # Verify stats were applied (+3% vitality should be present)
    # The vitality multiplier is 1.03x
    assert member.vitality >= 1.03

    # Drop HP below 45% threshold (450 HP)
    member.hp = 400
    loop.run_until_complete(BUS.emit_async("damage_taken", member, None, 0))

    # Check that HoT was applied by verifying hots list
    effect_manager = getattr(member, "effect_manager", None)
    assert effect_manager is not None, "Effect manager should be created"
    assert len(effect_manager.hots) > 0, "Radiant Regeneration HoT should be active"

    # Verify the HoT is Radiant Regeneration (Light element)
    hot = effect_manager.hots[0]
    assert hot.id == "light_radiant_regeneration"
    assert hot.turns == 2

    # Verify the HoT healing amount is calculated correctly
    # RadiantRegeneration uses: base = max(15, int(source.atk * 0.2))
    # healing = int(base * max(source.vitality, 1.0))
    # With atk=50, vitality=1.03: base = max(15, 10) = 15, healing = int(15 * 1.03) = 15
    assert hot.healing >= 15, f"Expected healing >= 15, got {hot.healing}"

    # Reset for cleanup
    loop.run_until_complete(BUS.emit_async("battle_end"))
    loop.close()


def test_oracle_prayer_charm_triggers_once_per_ally_per_battle():
    """Test that Oracle Prayer Charm only triggers once per ally per battle."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    party = Party()

    member = PlayerBase()
    member.id = "test_member"
    member.set_base_stat("max_hp", 1000)
    member.set_base_stat("atk", 50)
    member.set_base_stat("vitality", 1.0)
    member.hp = 1000
    party.members.append(member)

    # Award and apply Oracle Prayer Charm
    award_card(party, "oracle_prayer_charm")
    loop.run_until_complete(apply_cards(party))

    # Drop HP below threshold first time
    member.hp = 400
    loop.run_until_complete(BUS.emit_async("damage_taken", member, None, 0))

    effect_manager = getattr(member, "effect_manager", None)
    initial_hot_count = len(effect_manager.hots)
    assert initial_hot_count > 0, "First trigger should add HoT"

    # Drop HP even lower - should NOT trigger again
    member.hp = 200
    loop.run_until_complete(BUS.emit_async("damage_taken", member, None, 0))

    # Verify no additional HoT was added
    assert len(effect_manager.hots) == initial_hot_count, "Should not trigger twice in same battle"

    # End battle and start new one
    loop.run_until_complete(BUS.emit_async("battle_end"))

    # Reset HP to full and apply cards again for new battle
    member.hp = 1000
    effect_manager.hots.clear()
    loop.run_until_complete(apply_cards(party))

    # Drop HP below threshold in new battle
    member.hp = 400
    loop.run_until_complete(BUS.emit_async("damage_taken", member, None, 0))

    # Should trigger again in new battle
    assert len(effect_manager.hots) > 0, "Should trigger again in new battle"

    loop.run_until_complete(BUS.emit_async("battle_end"))
    loop.close()


def test_oracle_prayer_charm_applies_to_multiple_allies():
    """Test that Oracle Prayer Charm can trigger for multiple allies independently."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    party = Party()

    # Create two party members
    member1 = PlayerBase()
    member1.id = "member1"
    member1.set_base_stat("max_hp", 1000)
    member1.set_base_stat("atk", 50)
    member1.set_base_stat("vitality", 1.0)
    member1.hp = 1000
    party.members.append(member1)

    member2 = PlayerBase()
    member2.id = "member2"
    member2.set_base_stat("max_hp", 1000)
    member2.set_base_stat("atk", 50)
    member2.set_base_stat("vitality", 1.0)
    member2.hp = 1000
    party.members.append(member2)

    # Award and apply Oracle Prayer Charm
    award_card(party, "oracle_prayer_charm")
    loop.run_until_complete(apply_cards(party))

    # Drop member1 HP below threshold
    member1.hp = 400
    loop.run_until_complete(BUS.emit_async("damage_taken", member1, None, 0))

    effect_manager1 = getattr(member1, "effect_manager", None)
    assert len(effect_manager1.hots) > 0, "Member1 should receive HoT"

    # Drop member2 HP below threshold
    member2.hp = 350
    loop.run_until_complete(BUS.emit_async("damage_taken", member2, None, 0))

    effect_manager2 = getattr(member2, "effect_manager", None)
    assert len(effect_manager2.hots) > 0, "Member2 should also receive HoT"

    loop.run_until_complete(BUS.emit_async("battle_end"))
    loop.close()


def test_oracle_prayer_charm_does_not_trigger_above_threshold():
    """Test that Oracle Prayer Charm does not trigger when HP is above 45%."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    party = Party()

    member = PlayerBase()
    member.id = "test_member"
    member.set_base_stat("max_hp", 1000)
    member.set_base_stat("atk", 50)
    member.set_base_stat("vitality", 1.0)
    member.hp = 1000
    party.members.append(member)

    # Award and apply Oracle Prayer Charm
    award_card(party, "oracle_prayer_charm")
    loop.run_until_complete(apply_cards(party))

    # Drop HP to exactly 46% (above threshold)
    member.hp = 460
    loop.run_until_complete(BUS.emit_async("damage_taken", member, None, 0))

    effect_manager = getattr(member, "effect_manager", None)
    # Effect manager may exist from base stats, but should have no HoTs
    if effect_manager:
        assert len(effect_manager.hots) == 0, "Should not trigger above 45% threshold"

    loop.run_until_complete(BUS.emit_async("battle_end"))
    loop.close()
